from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, UnidentifiedImageError
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .experience_collector import school_search_name
from .models import PartnerUniversity
from .student_view import fetch_partner_universities
from .web_search import search_text


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 "
    "TaiwanExchangeGuide/0.1"
)
STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_IMAGE_OUTPUT_DIR = STATIC_DIR / "assets" / "schools"
DEFAULT_IMAGE_MANIFEST = STATIC_DIR / "assets" / "school-images.json"
POSITIVE_TERMS = {
    "campus": 38,
    "hero": 32,
    "banner": 28,
    "building": 24,
    "university": 18,
    "school": 12,
    "college": 12,
    "student": 8,
}
NEGATIVE_TERMS = {
    "logo": -100,
    "icon": -90,
    "favicon": -100,
    "sprite": -100,
    "avatar": -80,
    "portrait": -30,
    "faculty": -20,
    "staff": -20,
    "placeholder": -100,
}
IMAGE_ATTRIBUTES = (
    "src",
    "data-src",
    "data-lazy-src",
    "data-original",
    "data-image",
    "nitro-lazy-src",
)
OFFICIAL_IMAGE_OVERRIDES: dict[str, tuple[str, str]] = {
    "先皇技術學院(King Mongkut's institue of Technology ladkrabang)": (
        "https://oia.kmitl.ac.th/wp-content/uploads/2025/06/IMG_3722-980x653.jpg",
        "https://oia.kmitl.ac.th/welcomes-kajonkiet-international-school-phuket/",
    ),
    "法政大學 (Thammasat University)": (
        "https://oia.tu.ac.th/wp-content/uploads/2024/09/Dormitory_Student.jpg",
        "https://oia.tu.ac.th/accommodation-page/",
    ),
    "蒙庫國王科技大學 (King Mongkut's University of Technology Thonburi (KMUTT))": (
        "https://www.kmutt.ac.th/wp-content/uploads/2025/07/IMG_4286_0-1200x800.jpg",
        "https://www.kmutt.ac.th/en/news/29/07/2025/90799/",
    ),
    "宋卡王子大學 (Prince of Songkla University (PSU))": (
        "https://cmdt-uic.psu.ac.th/wp-content/uploads/2026/03/inter1.jpg",
        "https://cmdt-uic.psu.ac.th/international-student/",
    ),
    "一橋大學 (Hitotsubashi University) 無": (
        "https://www.hit-u.ac.jp/home/assets/images/bg-img1.jpg",
        "https://www.hit-u.ac.jp/eng/",
    ),
    "筑波大學 (The University of Tsukuba) 無": (
        "https://www.tsukuba.ac.jp/en/images/main-visual-en.jpg",
        "https://www.tsukuba.ac.jp/en/",
    ),
    "中國政法大學": (
        "https://en.cupl.edu.cn/images/ny/nyba2.jpg",
        "https://en.cupl.edu.cn/Campus/Visitors1.htm",
    ),
    "京畿大學 (Kyonggi University)": (
        "https://enter.kyonggi.ac.kr/ajaxfile/CMN_SVC/FileView.do?GBN=X03&SITE_NO=2&MENU_NO=110",
        "https://enter.kyonggi.ac.kr/cms/FR_CON/index.do?MENU_ID=110",
    ),
    "東國大學 (Dongguk University)": (
        "https://www.dongguk.edu/resources/files/og_thumbnail.jpg?v=01",
        "https://www.dongguk.edu/eng/main",
    ),
    "釜慶大學 (Pukyong National University)": (
        "https://www.pknu.ac.kr/images/front2/main/m_mainBanner01_e.png?v=1",
        "https://www.pknu.ac.kr/eng",
    ),
    "慶北大學 (Kyungpook National University)": (
        "https://en.knu.ac.kr/img/admission/double_bg.png",
        "https://en.knu.ac.kr/admission/exchange01.htm",
    ),
    "誠信女子大學 (Sungshin Women's University)": (
        "http://www.sungshin.ac.kr/editorUpload/images/000684/20260219102946512_KOMKITEL.png",
        "https://www.sungshin.ac.kr/main_eng/20146/subview.do?enc=Zm5jdDF8QEB8JTJGYmJzJTJGbWFpbl9lbmclMkY0OTUyJTJGMTUxODU1JTJGYXJ0Y2xWaWV3LmRvJTNG",
    ),
    "韓國漢陽大學Erica校區 Hanyang University ERICA": (
        "https://www.hanyang.ac.kr/documents/10548136/260875580/campus_bg3.jpg/7785fc41-9af0-4640-7a08-7d9f6fc72a9c?t=1769750656496&download=true",
        "https://www.hanyang.ac.kr/web/eng/erica-campus1",
    ),
    "光云大學Kwangwoon University": (
        "https://www.kw.ac.kr/KWData/Banner/2023/20230407103939.jpg",
        "https://www.kw.ac.kr/en/index.jsp",
    ),
    "馬來西亞馬來亞大學 Universiti Malaya": (
        "https://um.edu.my/Image/News/news_5ccfe917a8b76641bf979195df.jpg",
        "https://www.um.edu.my/news/indexnews.php",
    ),
    "印度昌迪加爾大學 Chandigarh University": (
        "https://www.cuchd.in/international/assets/img/campus-life-img-4.jpg",
        "https://www.cuchd.in/international/campus-life.php",
    ),
    "林肯大學 Lincoln University": (
        "https://livingheritage.lincoln.ac.nz/assets/pic/26545",
        "https://livingheritage.lincoln.ac.nz/nodes/view/26",
    ),
    "德國巴登-符騰堡州立合作大學 Duale Hochschule Baden-Württemberg Karlsruhe, Germany Baden-Wuerttemberg Cooperative State University": (
        "https://www.karlsruhe.dhbw.de/fileadmin/_processed_/b/b/csm_360-Grad-Rundgang_dhbw-karlsruhe-1_745e96ac33.jpg",
        "https://www.karlsruhe.dhbw.de/studium/im-studium/erstsemester.html",
    ),
    "韓國嘉泉大學 Gachon University": (
        "https://ace.gachon.ac.kr/upload/global_graduate_photo/3c91c548203f4d3a84a2272dd63d2da0.jpg",
        "https://ace.gachon.ac.kr/gschool/gallery/photo_list",
    ),
    "越南胡志明市科技教育大學 HCMC University of Technology and Education": (
        "https://en.hcmute.edu.vn/Resources/Images/SubDomain/HomePage/Center/kynguyen2.jpg",
        "https://en.hcmute.edu.vn/ArticleId/46c382f7-9990-47da-abf4-50d02d708fda/ho-chi-minh-city-university-of-technology-and-education-advancing-together-with-the-nation-in-a-new-era-of-development",
    ),
    "德國拉芬斯堡-魏恩加騰應用科技大學 Ravensburg-Weingarten University of Applied Sciences": (
        "https://www.rwu.de/sites/default/files/2025-08/rwu_luftbild_hauptgebaeude_foto_rwu_2023.jpg",
        "https://www.rwu.de/en/studies/study-organization/rwu-campus",
    ),
    "匈牙利德布勒森大學 University of Debrecen": (
        "https://edu.unideb.hu/tartalom/fotoalbum/01university_30/foepulet_cimerrel3.jpg",
        "https://edu.unideb.hu/gallery.php?album=01university_30",
    ),
    "法國特魯瓦工程技術大學 Université de technologie de Troyes": (
        "https://www.utt.fr/medias/photo/campus-grace-chiang-1-_1547819368422-jpg?ID_FICHE=4112",
        "https://www.utt.fr/le-campus-utt",
    ),
    "波蘭波茲南理工大學 Poznan University of Technology": (
        "https://www.put.poznan.pl/sites/default/files/2023-09/DSC07099-2.jpg",
        "https://put.poznan.pl/en/artykul/nowy-rektorat-politechniki-poznanskiej-w-kampusie-warta-w-poznaniu",
    ),
    "西班牙馬拉加大學 Universidad de Málaga": (
        "http://www.uma.es/media/fotos/image_7827.jpeg",
        "https://www.uma.es/smart-campus/cms/menu/edificios-uma/",
    ),
    "香港城市大學 City University of Hong Kong": (
        "https://www.cityu.edu.hk/cdo/img/photos/home_28.jpg",
        "https://www.cityu.edu.hk/about/campus",
    ),
    "韓國淑明女子大學 Sookmyung Women's University": (
        "https://haksa.sookmyung.ac.kr/sites/sookmyungen/atchmnfl_mngr/imageSlide/22/temp_1672722521837100.jpg",
        "https://haksa.sookmyung.ac.kr/sites/sookmyungen/index.do",
    ),
    "日本東北大學 Tohoku University": (
        "https://www.tohoku.ac.jp/en/events/images/092_virtual_tour_of_aobayama_campus_t.jpg",
        "https://www.tohoku.ac.jp/en/events/special_event/virtual_tour_of_aobayama_campus.html",
    ),
    "法國索邦大學 Sorbonne Université": (
        "https://www.sorbonne-universite.fr/sites/default/files/styles/1380xauto/public/media/2019-12/0-universite.jpg?itok=GcKOjRPz",
        "https://www.sorbonne-universite.fr/en/university",
    ),
    "瑞典布萊金厄技術學院 Blekinge Institute Of Technology": (
        "https://www.bth.se/images/200.15b01267195ad78d0ed6213f/1744032194044/Flygfoto-Campus-Karlskrona-24.jpg",
        "https://www.bth.se/english/about-bth",
    ),
    "日本立教大學商學院 Rikkyo University, College of Business": (
        "https://en.admission.rikkyo.ac.jp/wp-content/uploads/2021/02/img-key-34.jpg",
        "https://en.admission.rikkyo.ac.jp/explore/campuses/",
    ),
    "法國艾克斯馬賽大學管理研究所 IAE Aix-Marseille Graduate School of Management": (
        "https://iae-aix.univ-amu.fr/sites/default/files/media-image/IAE-facade2-entete.jpg",
        "https://iae-aix.univ-amu.fr/fr/presentation",
    ),
    "法國諾歐商學院 NEOMA Business School": (
        "https://neoma-bs.com/neoma/download/29162/NEOMA-rouen-ENTREE-c-jbdelerue.jpg",
        "https://neoma-bs.com/about-neoma/pressroom",
    ),
    "法國諾曼第高等商學院 EM Normandie Business School": (
        "https://en.em-normandie.com/sites/default/files/styles/1920_740/public/medias/images/campus-caen_hp.jpg?itok=g8fJ4Q1d",
        "https://en.em-normandie.com/",
    ),
    "泰國法政大學商學院 Thammasat Business School": (
        "https://sgs.tu.ac.th/wp-content/uploads/2023/07/Template-for-FBWebsite-Cover-Landscape-1-1.jpg",
        "https://sgs.tu.ac.th/news/thammasat-university-celebrates-89th-anniversary/",
    ),
    "泰國清邁大學公衛學院 Chiang Mai University, Faculty of Public Health": (
        "https://ph.cmu.ac.th/img_2/phbn_1.jpg",
        "https://www.ph.cmu.ac.th/EN/index.php",
    ),
    "日本西南學院大學商學院 Seinan Gakuin University": (
        "https://www.seinan-gu.ac.jp/j7icgd000000007a-img/top_july_1.jpg",
        "https://www.seinan-gu.ac.jp/",
    ),
    "日本九州大學 Kyushu University": (
        "https://isc.kyushu-u.ac.jp/invitation/assets/img/about/slide01/slide-01-01.jpg",
        "https://isc.kyushu-u.ac.jp/invitation/about/",
    ),
    "日本橫濱市立大學 Yokohama City University": (
        "https://www.yokohama-cu.ac.jp/english/about/hc1e5b0000000csy-img/campus_hakkei.jpg",
        "https://www.yokohama-cu.ac.jp/english/about/index.html",
    ),
    "歐洲知識經濟與管理學院 Skema Business School": (
        "https://www.skema.edu/sites/default/files/2024-05/grand-paris-campus-1500x1200.jpg",
        "https://www.skema.edu/en/campus/paris",
    ),
    "法國凱致商學院 KEDGE Business School": (
        "https://programme.kedge.edu/bundles/kedgecore/images/lpmulti.jpg?202605261204",
        "https://programme.kedge.edu/en/kedge-international-under-and-postgraduate-programmes",
    ),
    "TBS Education": (
        "https://www.tbs-education.com/content/uploads/sites/12/2026/01/tbs-education-entree-lascrosses-rentree-2025.jpg",
        "https://www.tbs-education.com/campuses/toulouse-campus/",
    ),
    "EPITECH": (
        "https://www.epitech.eu/wp-content/uploads/Epitech-Paris-Meilleure-ecole-informatique-ingenieur-data-IA-cybersecurite-10.webp",
        "https://www.epitech.eu/ecole-informatique-paris/",
    ),
    "Sciences Po Toulouse": (
        "https://www.sciencespo-toulouse.fr/medias/photo/manufacture-des-tabacs-toulouse-_1664201703627-jpg",
        "https://www.sciencespo-toulouse.fr/",
    ),
    "University of Wrocław": (
        "https://bip.uni.wroc.pl/download//35088/gmach_magdalena_marcula.jpeg?v=1666856864",
        "https://bip.uni.wroc.pl/",
    ),
    "Jagiellonian University Faculty of Philology": (
        "https://www.uj.edu.pl/documents/10172/148218640/kampus685_1.jpg/67e73b3e-6b7a-407c-94ec-7cf96198dba3?t=1626263518717",
        "https://www.uj.edu.pl/en_GB/",
    ),
    "北京清華大學 Tsinghua University": (
        "https://www.tsinghua.edu.cn/__local/5/E6/A5/019436B67552DF5F9737C6D6BD1_E5F89531_15630B.jpg",
        "https://www.tsinghua.edu.cn/en/Campus.htm",
    ),
    "武漢大學 Wuhan University": (
        "https://en.whu.edu.cn/newnet/images/about_bg.png",
        "https://en.whu.edu.cn/",
    ),
    "波蘭華沙生命科學大學 Warsaw University of Life Sciences": (
        "https://www.sggw.edu.pl/wp-content/uploads/2020/11/SGGW_17-scaled.jpg",
        "https://www.sggw.edu.pl/en/studies/",
    ),
    "鵅鴻大學 (Lac Hong University, LHU)": (
        "https://en.lhu.edu.vn/Data/Folders/3/images/360Banner_ENG.jpg",
        "https://en.lhu.edu.vn/",
    ),
    "越南河內國家大學 (Vietnam National University,Hanoi)": (
        "https://vstatic.vietnam.vn/vietnam/resource/IMAGE/2025/1/19/457c26d5d459482ebab1e1821f8602ef",
        "https://www.vietnam.vn/en/dai-hoc-quoc-gia-ha-noi-dua-6-000-sinh-vien-len-hoa-lac",
    ),
    "越南胡志明市國際大學 Vietnam National University, Ho Chi Minh City": (
        "https://hcmiu.edu.vn/wp-content/uploads/2026/07/truong-dai-hoc-quoc-te-IU.jpg",
        "https://hcmiu.edu.vn/en/",
    ),
    "越南文朗大學 (VanLang University)": (
        "https://vluwebmedia.s3.ap-southeast-1.amazonaws.com/vlu_welcome_day_chao_don_sinh_vien_trao_doi_quoc_te_tai_truong_dai_hoc_van_lang_a_a605e9a6df.jpg",
        "https://www.vlu.edu.vn/en/news/welcome-day-greeting-international-exchange-students-at-van-lang-university",
    ),
    "國立胡志明市經濟大學ˇ國際商學院(University of Economics Ho Chi Minh City-International School of Business)": (
        "https://international.isb.edu.vn/wp-content/uploads/sites/9/2020/03/co-so-59-Nguyen-Dinh-Chieu-1-min-1.png",
        "https://international.isb.edu.vn/campuses/",
    ),
    "越南德國大學(Vietnamese-German University)": (
        "https://img.youtube.com/vi/aKexZlnITqg/maxresdefault.jpg",
        "https://vgu.edu.vn/international-office/incomings-international-students/campus-tour",
    ),
    "美國明尼蘇達大學 University of Minnesota (GO Minnesota方案)": (
        "https://twin-cities.umn.edu/sites/twin-cities.umn.edu/files/umn-lawn.jpg",
        "https://twin-cities.umn.edu/",
    ),
    "明尼蘇達大學 University of Minnesota": (
        "https://twin-cities.umn.edu/sites/twin-cities.umn.edu/files/umn-lawn.jpg",
        "https://twin-cities.umn.edu/",
    ),
    "韓國延世大學 Yonsei University": (
        "https://www.yonsei.ac.kr/sites/en_sc/images/sub/img-cam1-intro2.jpg",
        "https://www.yonsei.ac.kr/en_sc/1817/subview.do",
    ),
    "馬里蘭大學巴爾的摩分校 The University of Maryland School of Nursing": (
        "https://www.nursing.umaryland.edu/media/son/news--events/desktop-and-phone-wallpapers/USG-Campus_Building-III.JPG",
        "https://www.nursing.umaryland.edu/news-events/social-media/",
    ),
    "威斯康辛大學密爾基分校 University of Wisconsin-Milwaukee": (
        "https://uwm.edu/wp-content/uploads/2024/09/about-UWM_Banner_DJI_20240918145211_0136_D-1.jpg",
        "https://uwm.edu/about/",
    ),
    "加州大學爾灣分校 University of California, Irvine": (
        "https://news.uci.edu/files/2018/09/studentcenter_170216_06a_sz.jpg",
        "https://news.uci.edu/2018/09/24/uci-celebrates-53rd-birthday/",
    ),
}
OFFICIAL_IMAGE_OVERRIDE_NOTES: dict[str, str] = {
    "越南河內國家大學 (Vietnam National University,Hanoi)": (
        "越南國家推廣平台刊載的河內國家大學和樂校區照片，頁面標示圖片來源為 VNU 官方粉絲頁"
    ),
}
OFFICIAL_IMAGE_DOWNLOAD_FALLBACKS: dict[str, str] = {
    "中國政法大學": (
        "https://tse2.mm.bing.net/th?id=OIP.GyRxQAB1eLvyI-T0pEBJVgHaD-&w=1600&h=900&c=7&rs=1&pid=Api"
    ),
    "越南胡志明市科技教育大學 HCMC University of Technology and Education": (
        "https://ts1.mm.bing.net/th?id=OIP.-XJi32QMKptceXrBeEhWigHaEK&w=1600&h=900&rs=1&c=4"
    ),
}
OFFICIAL_IMAGE_PAGE_OVERRIDES: dict[str, tuple[str, ...]] = {
    "山梨學院大學博雅教育國際學院(International College of Liberal Arts(iCLA) at Yamanashi Gakuin University)": (
        "https://www.icla.ygu.ac.jp/en/facilities/",
        "https://www.icla.ygu.ac.jp/en/campus-life/",
    ),
    "武藏野大學 (Musashino University)": (
        "https://www.musashino-u.ac.jp/english/",
        "https://www.musashino-u.ac.jp/guide/campus/",
    ),
    "蔚山科技大學(Ulsan National Institute of Science and Technology)": (
        "https://www.unist.ac.kr/unist/index.do",
        "https://www.unist.ac.kr/unist/introduction/campus-tour.do",
    ),
    "明知大學(Myongi university)": (
        "https://english.mju.ac.kr/mjukr/index.do",
    ),
    "嶺南大學 (Yeungnam University)": (
        "https://www.yu.ac.kr/english/index.do",
        "https://www.yu.ac.kr/english/life/student-life.do",
    ),
    "世宗大學 (Sejong University)": (
        "https://www.sejong.edu/eng/index.do",
        "https://en.sejong.ac.kr/eng/about-sejong/CampusMap.do",
    ),
}


def _official_image_override(school_name: str) -> tuple[str, str] | None:
    exact = OFFICIAL_IMAGE_OVERRIDES.get(school_name)
    if exact:
        return exact
    canonical = school_search_name(school_name).casefold().strip()
    for known_name, override in OFFICIAL_IMAGE_OVERRIDES.items():
        if school_search_name(known_name).casefold().strip() == canonical:
            return override
    return None


@dataclass(slots=True)
class ImageCandidate:
    url: str
    score: int
    context: str


@dataclass(slots=True)
class SchoolImageRecord:
    school_name: str
    country: str
    official_page_url: str
    image_source_url: str | None
    local_path: str | None
    width: int | None
    height: int | None
    content_hash: str | None
    checked_at: str
    status: str
    note: str | None = None


def collect_school_images(
    *,
    output_dir: Path,
    manifest_path: Path,
    timeout_seconds: float = 15.0,
    delay_seconds: float = 0.35,
    limit: int | None = None,
    missing_only: bool = False,
    refresh_overrides: bool = False,
    partners: list[PartnerUniversity] | None = None,
) -> list[SchoolImageRecord]:
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en,zh-TW;q=0.8"})
    partners = (
        [partner.model_copy(deep=True) for partner in partners]
        if partners is not None
        else fetch_partner_universities(timeout_seconds=timeout_seconds)
    )
    if limit:
        partners = partners[:limit]

    existing = _read_existing_manifest(manifest_path)
    records: list[SchoolImageRecord] = []
    for index, partner in enumerate(partners):
        previous = existing.get(partner.school_name)
        should_refresh = refresh_overrides and _official_image_override(partner.school_name) is not None
        if (
            missing_only
            and previous
            and previous.status == "verified"
            and previous.local_path
            and not should_refresh
        ):
            asset_path = output_dir / Path(urlparse(previous.local_path).path).name
            if asset_path.exists():
                records.append(previous)
                print(f"[{index + 1:02d}/{len(partners):02d}] {partner.school_name}: kept")
                continue
        override = _official_image_override(partner.school_name)
        official_url = override[1] if override else (partner.website or "")
        if not official_url:
            records.append(_missing_record(partner.school_name, partner.country or "", official_url, "合作校資料未提供官網"))
            continue
        try:
            record = _collect_one(
                session=session,
                school_name=partner.school_name,
                country=partner.country or "",
                official_url=official_url,
                output_dir=output_dir,
                timeout_seconds=timeout_seconds,
            )
        except requests.RequestException as exc:
            record = _missing_record(partner.school_name, partner.country or "", official_url, f"官網讀取失敗：{type(exc).__name__}")
        records.append(record)
        print(f"[{index + 1:02d}/{len(partners):02d}] {partner.school_name}: {record.status}")
        if delay_seconds > 0 and index < len(partners) - 1:
            time.sleep(delay_seconds)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    merged = dict(existing)
    for record in records:
        merged[record.school_name] = record
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_policy": "Images are selected from each university's official website and require rights review before public commercial use.",
        "schools": [asdict(record) for record in merged.values()],
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return records


def _collect_one(
    *,
    session: requests.Session,
    school_name: str,
    country: str,
    official_url: str,
    output_dir: Path,
    timeout_seconds: float,
) -> SchoolImageRecord:
    override = _official_image_override(school_name)
    if override:
        image_url, source_page_url = override
        try:
            downloaded = _download_and_prepare(session, image_url, timeout_seconds, allow_wide=True)
        except (requests.RequestException, UnidentifiedImageError, OSError, ValueError):
            try:
                downloaded = _download_and_prepare_with_browser(
                    image_url=image_url,
                    source_page_url=source_page_url,
                    timeout_seconds=timeout_seconds,
                )
            except (PlaywrightError, PlaywrightTimeoutError, UnidentifiedImageError, OSError, ValueError):
                downloaded = None
        if not downloaded and (fallback_url := OFFICIAL_IMAGE_DOWNLOAD_FALLBACKS.get(school_name)):
            try:
                downloaded = _download_and_prepare(
                    session,
                    fallback_url,
                    timeout_seconds,
                    allow_wide=True,
                )
            except (requests.RequestException, UnidentifiedImageError, OSError, ValueError):
                downloaded = None
        if downloaded:
            return _save_record(
                school_name=school_name,
                country=country,
                official_page_url=source_page_url,
                image_source_url=image_url,
                downloaded=downloaded,
                output_dir=output_dir,
                note=OFFICIAL_IMAGE_OVERRIDE_NOTES.get(
                    school_name,
                    (
                        "官方子網域暫時無法連線；下載搜尋快取中的同一張官方照片"
                        if school_name in OFFICIAL_IMAGE_DOWNLOAD_FALLBACKS
                        else "擷取自學校官方 Campus／About 頁面"
                    ),
                ),
            )

    errors: list[str] = []
    official_page_url = official_url
    for page_url, page_html in _official_photo_pages(
        session=session,
        school_name=school_name,
        official_url=official_url,
        timeout_seconds=timeout_seconds,
    ):
        official_page_url = page_url
        candidates = extract_image_candidates(page_html, page_url)
        for candidate in candidates[:18]:
            try:
                downloaded = _download_and_prepare(session, candidate.url, timeout_seconds)
            except (requests.RequestException, UnidentifiedImageError, OSError, ValueError) as exc:
                errors.append(type(exc).__name__)
                try:
                    downloaded = _download_and_prepare_with_browser(
                        image_url=candidate.url,
                        source_page_url=page_url,
                        timeout_seconds=timeout_seconds,
                    )
                except (
                    PlaywrightError,
                    PlaywrightTimeoutError,
                    UnidentifiedImageError,
                    OSError,
                    ValueError,
                ):
                    downloaded = None
            if downloaded is None:
                continue
            return _save_record(
                school_name=school_name,
                country=country,
                official_page_url=page_url,
                image_source_url=candidate.url,
                downloaded=downloaded,
                output_dir=output_dir,
                note=f"擷取自學校官方校園／主視覺頁（{candidate.context}）",
            )
    note = "官方頁面未找到可用的大型橫式照片"
    if errors:
        note += f"；略過 {len(errors)} 個無效候選圖"
    return _missing_record(school_name, country, official_page_url, note)


def _official_photo_pages(
    *,
    session: requests.Session,
    school_name: str,
    official_url: str,
    timeout_seconds: float,
) -> list[tuple[str, str]]:
    pages: list[tuple[str, str]] = []
    seen: set[str] = set()

    def fetch(url: str) -> None:
        if url in seen or not _same_official_site(url, official_url):
            return
        seen.add(url)
        try:
            response = session.get(url, timeout=timeout_seconds, allow_redirects=True)
            response.raise_for_status()
        except requests.RequestException:
            browser_page = _fetch_page_html_with_browser(
                url,
                timeout_seconds=timeout_seconds,
            )
            if browser_page:
                final_url, html = browser_page
                if _same_official_site(final_url, official_url):
                    pages.append((final_url, html))
            return
        if not _same_official_site(response.url, official_url):
            return
        pages.append((response.url, response.text))

    fetch(official_url)
    for page_url in OFFICIAL_IMAGE_PAGE_OVERRIDES.get(school_name, ()):
        fetch(page_url)
    host = urlparse(official_url).netloc.casefold().removeprefix("www.")
    if host:
        try:
            results = search_text(
                f"{school_name} campus buildings {host}",
                max_results=6,
                timeout_seconds=timeout_seconds,
            )
        except Exception:
            results = []
        for row in results:
            url = str(row.get("href") or row.get("url") or "")
            if url:
                fetch(url)
            if len(pages) >= 5:
                break
    return pages


def _fetch_page_html_with_browser(
    url: str,
    *,
    timeout_seconds: float,
) -> tuple[str, str] | None:
    timeout_ms = int(timeout_seconds * 1000)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True, user_agent=USER_AGENT)
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(1200)
            result = (page.url, page.content())
            browser.close()
            return result
    except (PlaywrightError, PlaywrightTimeoutError):
        return None


def _same_official_site(candidate_url: str, official_url: str) -> bool:
    candidate = urlparse(candidate_url).netloc.casefold().removeprefix("www.")
    official = urlparse(official_url).netloc.casefold().removeprefix("www.")
    return bool(
        candidate
        and official
        and (
            candidate == official
            or candidate.endswith(f".{official}")
            or official.endswith(f".{candidate}")
        )
    )


def extract_image_candidates(html: str, page_url: str) -> list[ImageCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: dict[str, ImageCandidate] = {}

    def add(raw_url: str | None, score: int, context: str) -> None:
        if not raw_url:
            return
        raw_url = raw_url.strip().split()[0]
        url = urljoin(page_url, raw_url)
        if urlparse(url).scheme not in {"http", "https"}:
            return
        text = f"{url} {context}".lower()
        adjusted = score + _keyword_score(text)
        if adjusted < -20 or url.lower().endswith((".svg", ".gif", ".ico")):
            return
        current = candidates.get(url)
        if current is None or adjusted > current.score:
            candidates[url] = ImageCandidate(url=url, score=adjusted, context=context)

    meta_specs = (
        ("meta[property='og:image']", 100, "Open Graph"),
        ("meta[property='og:image:secure_url']", 98, "Open Graph"),
        ("meta[name='twitter:image']", 92, "Twitter Card"),
        ("meta[property='twitter:image']", 92, "Twitter Card"),
        ("link[rel='image_src']", 88, "image_src"),
    )
    for selector, score, context in meta_specs:
        for node in soup.select(selector):
            add(node.get("content") or node.get("href"), score, context)

    for image in soup.find_all("img"):
        context = " ".join(
            str(value)
            for value in (
                image.get("alt", ""),
                image.get("class", ""),
                image.get("id", ""),
                image.parent.get("class", "") if image.parent else "",
            )
        )
        width = _integer_attribute(image.get("width"))
        height = _integer_attribute(image.get("height"))
        size_score = 0
        if width and height:
            size_score = min(35, int((width * height) / 50_000))
            if width < 360 or height < 180:
                size_score -= 70
        for attribute in IMAGE_ATTRIBUTES:
            add(image.get(attribute), 24 + size_score, context or "頁面圖片")
        srcset = (
            image.get("srcset")
            or image.get("data-srcset")
            or image.get("nitro-lazy-srcset")
        )
        if srcset:
            largest = srcset.split(",")[-1].strip().split()[0]
            add(largest, 32 + size_score, context or "響應式頁面圖片")

    for node in soup.select("[style*='background']"):
        style = node.get("style", "")
        context = " ".join((str(node.get("class", "")), str(node.get("id", ""))))
        for raw_url in re.findall(r"url\(['\"]?([^)'\"]+)", style, flags=re.IGNORECASE):
            add(raw_url, 52, context or "背景主視覺")

    return sorted(candidates.values(), key=lambda candidate: candidate.score, reverse=True)


def _download_and_prepare(
    session: requests.Session,
    url: str,
    timeout_seconds: float,
    allow_wide: bool = False,
) -> tuple[bytes, int, int] | None:
    response = session.get(url, timeout=timeout_seconds, allow_redirects=True, headers={"Referer": url})
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()
    if "image" not in content_type or len(response.content) < 18_000:
        return None
    return _prepare_image_bytes(response.content, allow_wide=allow_wide)


def _download_and_prepare_with_browser(
    *,
    image_url: str,
    source_page_url: str,
    timeout_seconds: float,
) -> tuple[bytes, int, int] | None:
    timeout_ms = int(timeout_seconds * 1000)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        try:
            page.goto(source_page_url, wait_until="domcontentloaded", timeout=timeout_ms)
        except PlaywrightTimeoutError:
            pass
        page.wait_for_timeout(1200)
        content: bytes | None = None
        try:
            response = context.request.get(
                image_url,
                headers={"Referer": source_page_url, "User-Agent": USER_AGENT},
                timeout=timeout_ms,
            )
            if response.ok:
                content = response.body()
        except PlaywrightError:
            content = None
        try:
            prepared = _prepare_image_bytes(content, allow_wide=True) if content else None
        except (UnidentifiedImageError, OSError, ValueError):
            prepared = None
        if prepared:
            browser.close()
            return prepared
        try:
            response = page.goto(image_url, wait_until="commit", timeout=timeout_ms)
            if response and response.ok:
                content = response.body()
                try:
                    prepared = _prepare_image_bytes(content, allow_wide=True)
                except (UnidentifiedImageError, OSError, ValueError):
                    prepared = None
            if not prepared:
                page.wait_for_timeout(500)
                image = page.locator("img").first
                if image.count():
                    content = image.screenshot(type="png", timeout=timeout_ms)
                    prepared = _prepare_image_bytes(content, allow_wide=True)
        except (PlaywrightError, UnidentifiedImageError, OSError, ValueError):
            prepared = None
        browser.close()
    return prepared


def _prepare_image_bytes(content: bytes, *, allow_wide: bool = False) -> tuple[bytes, int, int] | None:
    if len(content) < 18_000:
        return None
    with Image.open(io.BytesIO(content)) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        width, height = image.size
        minimum_ratio = 0.65 if allow_wide else 1.15
        maximum_ratio = 5.0 if allow_wide else 3.5
        if width < 600 or height < 280 or not minimum_ratio <= width / height <= maximum_ratio:
            return None
        fitted = ImageOps.fit(image, (1600, 900), method=Image.Resampling.LANCZOS)
        output = io.BytesIO()
        fitted.save(output, format="JPEG", quality=84, optimize=True, progressive=True)
    return output.getvalue(), 1600, 900


def _save_record(
    *,
    school_name: str,
    country: str,
    official_page_url: str,
    image_source_url: str,
    downloaded: tuple[bytes, int, int],
    output_dir: Path,
    note: str,
) -> SchoolImageRecord:
    image_bytes, width, height = downloaded
    digest = hashlib.sha256(image_bytes).hexdigest()
    filename = f"{hashlib.sha256(school_name.encode('utf-8')).hexdigest()[:14]}.jpg"
    destination = output_dir / filename
    destination.write_bytes(image_bytes)
    return SchoolImageRecord(
        school_name=school_name,
        country=country,
        official_page_url=official_page_url,
        image_source_url=image_source_url,
        local_path=f"/static/assets/schools/{filename}?v={digest[:12]}",
        width=width,
        height=height,
        content_hash=digest,
        checked_at=datetime.now(UTC).isoformat(),
        status="verified",
        note=note,
    )


def _read_existing_manifest(manifest_path: Path) -> dict[str, SchoolImageRecord]:
    if not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {
            row["school_name"]: SchoolImageRecord(**row)
            for row in payload.get("schools", [])
            if row.get("school_name")
        }
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return {}


def _keyword_score(text: str) -> int:
    score = 0
    for term, value in POSITIVE_TERMS.items():
        if term in text:
            score += value
    for term, value in NEGATIVE_TERMS.items():
        if term in text:
            score += value
    return score


def _integer_attribute(value: object) -> int | None:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group()) if match else None


def _missing_record(school_name: str, country: str, official_url: str, note: str) -> SchoolImageRecord:
    return SchoolImageRecord(
        school_name=school_name,
        country=country,
        official_page_url=official_url,
        image_source_url=None,
        local_path=None,
        width=None,
        height=None,
        content_hash=None,
        checked_at=datetime.now(UTC).isoformat(),
        status="missing",
        note=note,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect partner-university images from official websites.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_IMAGE_OUTPUT_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_IMAGE_MANIFEST)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--missing-only", action="store_true")
    parser.add_argument("--refresh-overrides", action="store_true")
    args = parser.parse_args()
    records = collect_school_images(
        output_dir=args.output_dir,
        manifest_path=args.manifest,
        timeout_seconds=args.timeout,
        delay_seconds=args.delay,
        limit=args.limit,
        missing_only=args.missing_only,
        refresh_overrides=args.refresh_overrides,
    )
    verified = sum(record.status == "verified" for record in records)
    print(f"Completed: {verified}/{len(records)} official school images verified.")


if __name__ == "__main__":
    main()

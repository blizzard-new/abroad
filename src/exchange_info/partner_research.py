from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from functools import lru_cache
from urllib.parse import urlparse

import requests

from .content_summary import summarize_official_life_link
from .experience_collector import COUNTRY_SEARCH_NAMES, school_search_name
from .models import (
    DestinationProfile,
    PageCategory,
    PartnerResearchRecord,
    PartnerUniversity,
    SourceReference,
    StudentGuideChecklistItem,
    StudentGuidePhoto,
    StudentGuideSection,
)
from .school_identity import school_identity_key
from .student_survival import apply_shared_student_survival_guide
from .web_search import search_text


BLOCKED_DISCOVERY_HOSTS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "researchgate.net",
    "studyabroad101.com",
    "timeshighereducation.com",
    "usnews.com",
    "wikipedia.org",
    "youtube.com",
}

ACADEMIC_DOMAIN_MARKERS = (
    ".ac.",
    ".edu",
    ".univ-",
    ".uni-",
    "university",
    "universite",
    "universita",
)

GENERIC_NAME_WORDS = {
    "and",
    "at",
    "college",
    "for",
    "international",
    "of",
    "school",
    "the",
    "university",
}

# Sites confirmed against the first live NTPU research batch. Keeping these
# canonical landing pages prevents a faculty sub-site from outranking the
# university-wide exchange entry on a later refresh.
VERIFIED_OFFICIAL_SITES = {
    "king mongkut's institute of technology ladkrabang kmitl": (
        "https://oia.kmitl.ac.th/incoming-programs/",
        "KMITL incoming exchange students",
    ),
    "king mongkut's institue of technology ladkrabang": (
        "https://oia.kmitl.ac.th/incoming-programs/",
        "KMITL incoming exchange students",
    ),
    "king mongkut's institute of technology ladkrabang": (
        "https://oia.kmitl.ac.th/incoming-programs/",
        "KMITL incoming exchange students",
    ),
    "thammasat university": (
        "https://oia.tu.ac.th/aim-articles/",
        "Thammasat University incoming exchange application",
    ),
    "thammasat university thailand": (
        "https://oia.tu.ac.th/aim-articles/",
        "Thammasat University incoming exchange application",
    ),
    "king mongkut's university of technology thonburi (kmutt": (
        "https://www.kmutt.ac.th/internationalization/mobility-program/exchange-programs/",
        "KMUTT incoming exchange students",
    ),
    "king mongkut's university of technology thonburi": (
        "https://www.kmutt.ac.th/internationalization/mobility-program/exchange-programs/",
        "KMUTT incoming exchange students",
    ),
    "king mongkut's university of technology thonburi kmutt": (
        "https://www.kmutt.ac.th/internationalization/mobility-program/exchange-programs/",
        "KMUTT incoming exchange students",
    ),
    "prince of songkla university (psu": (
        "https://gao.psu.ac.th/students/1-stop-service",
        "Prince of Songkla University international student one-stop service",
    ),
    "prince of songkla university": (
        "https://gao.psu.ac.th/students/1-stop-service",
        "Prince of Songkla University international student one-stop service",
    ),
    "prince of songkla university psu": (
        "https://gao.psu.ac.th/students/1-stop-service",
        "Prince of Songkla University international student one-stop service",
    ),
    "national economics university vietnam": (
        "https://neu.edu.vn/en/",
        "National Economics University official English website",
    ),
    "lac hong university": (
        "https://en.lhu.edu.vn/",
        "Lac Hong University official English website",
    ),
    "vietnam national university hanoi": (
        "https://vnu.edu.vn/eng/?C2549/N20206/Information-for-exchange-students-at-Vietnam-National-University%2C-Hanoi.htm=",
        "Vietnam National University Hanoi exchange students",
    ),
    "international university vnu hcmc": (
        "https://hcmiu.edu.vn/en/",
        "International University VNU HCMC official website",
    ),
    "van lang university": (
        "https://www.vlu.edu.vn/en/admissions/student-exchange-opportunities",
        "Van Lang University exchange opportunities",
    ),
    "university of economics and law vnu hcmc": (
        "https://www.uel.edu.vn/en",
        "University of Economics and Law official English website",
    ),
    "ueh international school of business": (
        "https://international.isb.edu.vn/transfer-programs/international-students/",
        "UEH International School of Business incoming exchange students",
    ),
    "national economics university, vietnam": (
        "https://neu.edu.vn/en/",
        "National Economics University official English website",
    ),
    "lac hong university, lhu": (
        "https://en.lhu.edu.vn/",
        "Lac Hong University official English website",
    ),
    "vietnam national university,hanoi": (
        "https://vnu.edu.vn/eng/?C2549/N20206/Information-for-exchange-students-at-Vietnam-National-University%2C-Hanoi.htm=",
        "Vietnam National University Hanoi exchange students",
    ),
    "vietnam national university, ho chi minh city": (
        "https://hcmiu.edu.vn/en/",
        "International University VNU HCMC official website",
    ),
    "vanlang university": (
        "https://www.vlu.edu.vn/en/admissions/student-exchange-opportunities",
        "Van Lang University exchange opportunities",
    ),
    "university of economics and law": (
        "https://www.uel.edu.vn/en",
        "University of Economics and Law official English website",
    ),
    "university of economics ho chi minh city-international school of business": (
        "https://international.isb.edu.vn/transfer-programs/international-students/",
        "UEH International School of Business incoming exchange students",
    ),
    "vietnamese-german university": (
        "https://vgu.edu.vn/international-office",
        "Vietnamese-German University International Office",
    ),
    "adam mickiewicz university": (
        "https://erasmus.amu.edu.pl/en/incoming-students2/how-to-apply",
        "Adam Mickiewicz University incoming exchange application",
    ),
    "kozminski university": (
        "https://www.kozminski.edu.pl/en/community/incoming-students",
        "Kozminski University incoming students",
    ),
    "poznań university of economics and business": (
        "https://ue.poznan.pl/en/students/incoming-exchange-students/",
        "Poznań University of Economics and Business incoming exchange students",
    ),
    "poznań university of technology": (
        "https://put.poznan.pl/en/erasmus-incoming",
        "Poznań University of Technology incoming Erasmus students",
    ),
    "warsaw university of life sciences": (
        "https://rekrutacja.sggw.edu.pl/en/offer/REK_2026_27Z_WYMIENNE/programme/MOBILE/",
        "Warsaw University of Life Sciences non-EU incoming exchange",
    ),
    "university of wrocław": (
        "https://international.uni.wroc.pl/en/incoming-exchange-students",
        "University of Wrocław incoming exchange students",
    ),
    "krakow university of economics": (
        "https://bpz.uek.krakow.pl/en/incoming-students/",
        "Krakow University of Economics incoming students",
    ),
    "jagiellonian university faculty of philology": (
        "https://mymobility.uj.edu.pl/en-gb/offer/BILATERALNA_UTRECHT_2025/programme/UJ_BILATERAL_EXCHANGE/",
        "Jagiellonian University bilateral exchange application",
    ),
    "neoma business school": (
        "https://neoma-bs.com/",
        "NEOMA Business School official website",
    ),
    "université de technologie de troyes": (
        "https://www.utt.fr/academic-programs",
        "Université de Technologie de Troyes exchange programs",
    ),
    "efrei": (
        "https://eng.efrei.fr/international-office/",
        "Efrei International Office",
    ),
    "excelia business school": (
        "https://www.excelia-group.com/student-services/international-students/exchange-students/programmes-details",
        "Excelia exchange student programs",
    ),
    "rennes school of business": (
        "https://www.rennes-sb.com/exchange-programmes/incoming-exchange-students/",
        "Rennes School of Business incoming exchange students",
    ),
    "esce international business school": (
        "https://www.esce.fr/en/",
        "ESCE International Business School official English website",
    ),
    "essca school of management": (
        "https://www.essca.eu/en/",
        "ESSCA School of Management official website",
    ),
    "skema business school": (
        "https://www.skema.edu/en/exchange-students",
        "SKEMA Business School exchange students",
    ),
    "pôle léonard de vinci": (
        "https://www.devinci.fr/international/",
        "Pôle Léonard de Vinci international office",
    ),
    "em normandie business school": (
        "https://www.em-normandie.com/experience-em-normandie/international/programmes-echange",
        "EM Normandie exchange programs",
    ),
    "edhec business school": (
        "https://www.edhec.edu/en/international-students",
        "EDHEC Business School international students",
    ),
    "tbs education": (
        "https://www.tbs-education.com/international/incoming-students/",
        "TBS Education incoming students",
    ),
    "edc paris business school": (
        "https://www.edcparis.edu/en/",
        "EDC Paris Business School official English website",
    ),
    "toulouse capitole university": (
        "https://www.ut-capitole.fr/home/international",
        "Toulouse Capitole University international office",
    ),
    "epitech": (
        "https://www.epitech.eu/international/",
        "EPITECH international programs",
    ),
    "sciences po aix": (
        "https://www.sciencespo-aix.fr/international/",
        "Sciences Po Aix international office",
    ),
    "sciences po toulouse": (
        "https://www.sciencespo-toulouse.fr/en/international/",
        "Sciences Po Toulouse international office",
    ),
    "kedge business school": (
        "https://student.kedge.edu/study-abroad-in-france/incoming-students",
        "KEDGE Business School incoming students",
    ),
    "université de lille": (
        "https://international.univ-lille.fr/en/coming-to-the-university-of-lille/as-an-international-student/exchange-student/",
        "University of Lille exchange students",
    ),
    "kyonggi university": (
        "https://www.kyonggi.ac.kr/international_kgu/contents.do?key=7582",
        "Kyonggi University incoming exchange program",
    ),
    "dongguk university": (
        "https://www.dongguk.edu/eng/main",
        "Dongguk University official English website",
    ),
    "pukyong national university": (
        "https://www.pknu.ac.kr/eng",
        "Pukyong National University official English website",
    ),
    "kyungpook national university": (
        "https://en.knu.ac.kr/admission/exchange01.htm",
        "Kyungpook National University exchange student program",
    ),
    "sungshin women's university": (
        "https://www.sungshin.ac.kr/main_eng/index.do",
        "Sungshin Women's University official English website",
    ),
    "erica hanyang university erica": (
        "https://www.hanyang.ac.kr/web/eng/erica-campus1",
        "Hanyang University ERICA Campus official website",
    ),
    "kwangwoon university": (
        "https://www.kw.ac.kr/en/index.jsp",
        "Kwangwoon University official English website",
    ),
    "kwansei gakuin university": (
        "https://www.kwansei.ac.jp/en/",
        "Kwansei Gakuin University official English website",
    ),
    "saga university": (
        "https://www.saga-u.ac.jp/en/",
        "Saga University official English website",
    ),
    "international college of liberal arts(icla) at yamanashi gakuin university": (
        "https://www.icla.ygu.ac.jp/en/",
        "iCLA at Yamanashi Gakuin University official website",
    ),
    "the university of electro-communications;uec": (
        "https://www.uec.ac.jp/eng/",
        "The University of Electro-Communications official English website",
    ),
    "musashino university": (
        "https://www.musashino-u.ac.jp/english/",
        "Musashino University official English website",
    ),
    "hitotsubashi university": (
        "https://international.hit-u.ac.jp/en/pros/exchange/",
        "Hitotsubashi University exchange student program",
    ),
    "meiji university": (
        "https://www.meiji.ac.jp/cip/english/admissions/exchange.html",
        "Meiji University exchange student program",
    ),
    "chuo university": (
        "https://www.chuo-u.ac.jp/english/admissions/exchange/",
        "Chuo University exchange student program",
    ),
    "utsunomiya university": (
        "https://www.utsunomiya-u.ac.jp/en/",
        "Utsunomiya University official English website",
    ),
    "kobe university": (
        "https://www.kobe-u.ac.jp/en/academics/admissions/exchange-programs/",
        "Kobe University exchange programs",
    ),
    "konan university": (
        "https://www.konan-u.ac.jp/english/",
        "Konan University official English website",
    ),
    "osaka university of economics": (
        "https://www.osaka-ue.ac.jp/entrance/english/",
        "Osaka University of Economics official English website",
    ),
    "the university of tsukuba": (
        "https://www.tsukuba.ac.jp/en/academics/international-exchange-students/programs/",
        "University of Tsukuba exchange program",
    ),
    "fukushima university": (
        "https://english.adb.fukushima-u.ac.jp/",
        "Fukushima University official English website",
    ),
    "kindai university": (
        "https://www.kindai.ac.jp/english/",
        "Kindai University official English website",
    ),
    "chiba university": (
        "https://www.chiba-u.jp/e/",
        "Chiba University official English website",
    ),
    "daito bunka university": (
        "https://www.daito.ac.jp/english/",
        "Daito Bunka University official English website",
    ),
    "nishikyusyu university": (
        "https://www.nisikyu-u.ac.jp/",
        "Nishikyushu University official website",
    ),
    "靜岡縣立大學": (
        "https://eng.u-shizuoka-ken.ac.jp/",
        "University of Shizuoka official English website",
    ),
    "上海立信會計 金融學院": (
        "https://en.lixin.edu.cn/Programs/list.htm",
        "Shanghai Lixin University international exchange student guide",
    ),
    "上海財經大學": (
        "https://iecoenglish.sufe.edu.cn/3446/list.htm",
        "Shanghai University of Finance and Economics incoming exchange program",
    ),
    "天津大學": (
        "https://en.tju.edu.cn/info/1245/8733.htm",
        "Tianjin University exchange programs",
    ),
    "華東師範大學": (
        "https://lxs.ecnu.edu.cn/en/",
        "East China Normal University international students office",
    ),
    "南開大學": (
        "https://ensie.nankai.edu.cn/",
        "Nankai University international students office",
    ),
    "中國人民大學": (
        "https://sis.ruc.edu.cn/en/internationalExchange/studentexchange/exchange_application/index.htm",
        "Renmin University of China student exchange application",
    ),
    "中國政法大學": (
        "https://sis.cupl.edu.cn/",
        "China University of Political Science and Law international education office",
    ),
    "北京體育大學": (
        "https://en.bsu.edu.cn/Campus/StudentLife/StudyandLifeServicesforInternationalStudents/index.htm",
        "Beijing Sport University international student services",
    ),
    "西南大學": (
        "https://admissions.swu.edu.cn/",
        "Southwest University international admissions",
    ),
    "山東師範大學": (
        "https://en.cie.sdnu.edu.cn/",
        "Shandong Normal University international students office",
    ),
    "東北林業大學": (
        "https://siee.nefu.edu.cn/English/Programs/_Exchange_Program.htm",
        "Northeast Forestry University exchange program",
    ),
    "武漢大學": (
        "https://en.whu.edu.cn/",
        "Wuhan University official English website",
    ),
    "華中農業大學": (
        "https://en.hzau.edu.cn/index.htm",
        "Huazhong Agricultural University official English website",
    ),
    "吉林大學": (
        "https://cie.jlu.edu.cn/",
        "Jilin University College of International Education",
    ),
    "四川大學": (
        "https://global.scu.edu.cn/oso/article/index/1131",
        "Sichuan University exchange application and admission",
    ),
    "南京大學": (
        "https://stuex.nju.edu.cn/en_/NonwdegreeProgram/list.htm",
        "Nanjing University international student exchange program",
    ),
    "西北政法大學": (
        "https://en.nwupl.edu.cn/admission/83096.htm",
        "Northwest University of Political Science and Law exchange guide",
    ),
    "西安交通大學": (
        "https://sie.xjtu.edu.cn/en/exchange.pdf",
        "Xi'an Jiaotong University exchange student application guide",
    ),
    "廈門大學": (
        "https://admissions.xmu.edu.cn/",
        "Xiamen University international admissions",
    ),
    "ulsan national institute of science and technology": (
        "https://www.unist.ac.kr/unist/index.do",
        "UNIST official website",
    ),
    "myongi university": (
        "https://english.mju.ac.kr/mjukr/index.do",
        "Myongji University official English website",
    ),
    "yeungnam university": (
        "https://www.yu.ac.kr/english/index.do",
        "Yeungnam University official English website",
    ),
    "sejong university": (
        "https://www.sejong.edu/eng/index.do",
        "Sejong University official English website",
    ),
}

# These entries use the exact display name from NTPU's current partner-school
# catalog. They are intentionally kept separate from the broad search aliases:
# several schools have near-identical English or Chinese names, and a generic
# web search can otherwise select a different university (for example Shandong
# University of Science and Technology instead of Shandong University).
VERIFIED_OFFICIAL_SITES.update(
    {
        "下諾夫哥羅德羅巴切夫斯基國立大學": (
            "https://eng.unn.ru/",
            "Lobachevsky State University official English website",
        ),
        "東北大學": (
            "https://www.tohoku.ac.jp/en/",
            "Tohoku University official English website",
        ),
        "勞倫森大學": (
            "https://laurentian.ca/",
            "Laurentian University official website",
        ),
        "o.p.金達爾全球大學": (
            "https://jgu.edu.in/",
            "O.P. Jindal Global University official website",
        ),
        "republic 布拉格生命科學大學": (
            "https://www.czu.cz/en/",
            "Czech University of Life Sciences Prague official English website",
        ),
        "republic 茲林托馬斯巴塔大學": (
            "https://www.utb.cz/en/",
            "Tomas Bata University in Zlin official English website",
        ),
        "republic 西波西米亞大學": (
            "https://www.zcu.cz/en/",
            "University of West Bohemia official English website",
        ),
        "republic 俄斯特拉發工業大學": (
            "https://www.vsb.cz/en/",
            "VSB Technical University of Ostrava official English website",
        ),
        "中央財經大學": (
            "https://en.cufe.edu.cn/",
            "Central University of Finance and Economics official English website",
        ),
        "仰光大學": (
            "https://www.uy.edu.mm/",
            "University of Yangon official website",
        ),
        "佛羅倫斯藝術大學": (
            "https://fua.it/",
            "Florence University of the Arts official website",
        ),
        "俄斯特拉發大學": (
            "https://www.osu.eu/",
            "University of Ostrava official English website",
        ),
        "北安普頓大學": (
            "https://www.northampton.ac.uk/",
            "University of Northampton official website",
        ),
        "北愛荷華大學": (
            "https://uni.edu/",
            "University of Northern Iowa official website",
        ),
        "南猶他大學": (
            "https://www.suu.edu/",
            "Southern Utah University official website",
        ),
        "卡爾斯塔德大學": (
            "https://www.kau.se/en",
            "Karlstad University official English website",
        ),
        "印尼大學": (
            "https://www.ui.ac.id/en/",
            "Universitas Indonesia official English website",
        ),
        "印尼伊斯蘭大學": (
            "https://www.uii.ac.id/en/",
            "Universitas Islam Indonesia official English website",
        ),
        "比娜大學": (
            "https://binus.ac.id/",
            "BINUS University official website",
        ),
        "印尼迪安努斯萬托羅大學": (
            "https://dinus.ac.id/en/",
            "Universitas Dian Nuswantoro official English website",
        ),
        "吉羅卡斯特大學": (
            "https://uogj.edu.al/",
            "Eqrem Cabej University of Gjirokaster official website",
        ),
        "奧斯陸大學（犯罪學與社會學法系）": (
            "https://www.jus.uio.no/ikrs/english/",
            "University of Oslo Department of Criminology and Sociology of Law",
        ),
        "奧維第烏斯大學": (
            "https://www.univ-ovidius.ro/",
            "Ovidius University of Constanta official website",
        ),
        "挪威克里斯蒂安尼亞應用科學大學": (
            "https://www.kristiania.no/en/",
            "Kristiania University of Applied Sciences official English website",
        ),
        "山東大學": (
            "https://www.en.sdu.edu.cn/",
            "Shandong University official English website",
        ),
        "布拉提斯拉瓦斯洛伐克工業大學": (
            "https://www.stuba.sk/english.html?page_id=132",
            "Slovak University of Technology in Bratislava official English website",
        ),
        "愛丁堡大學": (
            "https://www.ed.ac.uk/",
            "University of Edinburgh official website",
        ),
        "拉斯帕爾瑪斯大學": (
            "https://www.ulpgc.es/en/",
            "University of Las Palmas de Gran Canaria official English website",
        ),
        "拉脫維亞大學": (
            "https://www.lu.lv/en/",
            "University of Latvia official English website",
        ),
        "新加坡社科大學": (
            "https://www.suss.edu.sg/",
            "Singapore University of Social Sciences official website",
        ),
        "新墨西哥州立大學": (
            "https://www.nmsu.edu/",
            "New Mexico State University official website",
        ),
        "義大利卡利亞里大學": (
            "https://www.unica.it/unica/en/homepage.page",
            "University of Cagliari official English website",
        ),
        "昌迪加爾大學": (
            "https://www.cuchd.in/",
            "Chandigarh University official website",
        ),
        "明斯特大學": (
            "https://www.uni-muenster.de/en/",
            "University of Muenster official English website",
        ),
        "明斯特應用技術大學": (
            "https://www.fh-muenster.de/msb/en/index.php",
            "FH Muenster School of Business official English website",
        ),
        "普列漢諾夫經濟大學": (
            "https://www.rea.ru/en/",
            "Plekhanov Russian University of Economics official English website",
        ),
        "俄羅斯經濟與公共管理學院": (
            "https://www.ranepa.ru/eng/",
            "RANEPA official English website",
        ),
        "普雷紹夫大學": (
            "https://www.unipo.sk/en/",
            "University of Presov official English website",
        ),
        "暨南大學": (
            "https://english.jnu.edu.cn/",
            "Jinan University official English website",
        ),
        "東華理工大學": (
            "https://eng.ecut.edu.cn/",
            "East China University of Technology official English website",
        ),
        "格但斯克科技大學": (
            "https://pg.edu.pl/en",
            "Gdansk University of Technology official English website",
        ),
        "梅拉達倫大學": (
            "https://www.mdu.se/en/malardalen-university",
            "Malardalen University official English website",
        ),
        "比利時魯汶林堡學院大學": (
            "https://www.ucll.be/en",
            "UCLL University of Applied Sciences official English website",
        ),
        "泰國東方大學": (
            "https://www.buu.ac.th/en/",
            "Burapha University official English website",
        ),
        "泰國清邁大學": (
            "https://www.cmu.ac.th/en/",
            "Chiang Mai University official English website",
        ),
        "斯洛伐克布拉斯第拉瓦經濟大學": (
            "https://euba.sk/en/",
            "University of Economics in Bratislava official English website",
        ),
        "圖里巴大學": (
            "https://www.turiba.lv/en/",
            "Turiba University official English website",
        ),
        "瑞典厄勒布魯大學": (
            "https://www.oru.se/english/",
            "Orebro University official English website",
        ),
        "瑞士西部應用科技大學日內瓦商學院": (
            "https://www.hesge.ch/heg/en",
            "Geneva School of Business Administration official English website",
        ),
        "百麗宮國際大學": (
            "https://paragoniu.edu.kh/",
            "Paragon International University official website",
        ),
        "穆爾西亞聖安東尼奧天主教大學": (
            "https://international.ucam.edu/",
            "UCAM Catholic University of Murcia official international website",
        ),
        "立陶宛維塔斯．馬格努斯大學": (
            "https://www.vdu.lt/en/",
            "Vytautas Magnus University official English website",
        ),
        "英屬哥倫比亞大學": (
            "https://www.ubc.ca/",
            "University of British Columbia official website",
        ),
        "荷蘭烏特勒支應用科技大學": (
            "https://www.internationalhu.com/",
            "HU University of Applied Sciences Utrecht official international website",
        ),
        "羅馬尼亞布拉索夫特蘭西瓦尼亞大學": (
            "https://www.unitbv.ro/en/",
            "Transilvania University of Brasov official English website",
        ),
        "茵斯堡大學": (
            "https://www.uibk.ac.at/en/",
            "University of Innsbruck official English website",
        ),
        "蒂米什拉西部大學": (
            "https://www.uvt.ro/en/",
            "West University of Timisoara official English website",
        ),
        "蘭州大學": (
            "https://en.lzu.edu.cn/",
            "Lanzhou University official English website",
        ),
        "費內巴赫大學": (
            "https://www.fbu.edu.tr/en",
            "Fenerbahce University official English website",
        ),
        "阿拉木圖管理大學": (
            "https://almau.edu.kz/en/",
            "Almaty Management University official English website",
        ),
        "阿提巴斯大學": (
            "https://altinbas.edu.tr/en/",
            "Altinbas University official English website",
        ),
        "蒙古財經大學": (
            "https://ufe.edu.mn/",
            "University of Finance and Economics Mongolia official website",
        ),
        "高麗大學世宗校區": (
            "https://sejong.korea.ac.kr/eng/",
            "Korea University Sejong Campus official English website",
        ),
        "越南融促大學": (
            "https://daihoc.fpt.edu.vn/en/",
            "FPT University official English website",
        ),
        "加拿大多倫多都會大學": (
            "https://www.torontomu.ca/",
            "Toronto Metropolitan University official website",
        ),
        "香港恆生大學": (
            "https://www.hsu.edu.hk/en/",
            "Hang Seng University of Hong Kong official English website",
        ),
        "香港教育大學": (
            "https://www.eduhk.hk/en/",
            "Education University of Hong Kong official English website",
        ),
        "香港樹仁大學": (
            "https://www.hksyu.edu/en/",
            "Hong Kong Shue Yan University official English website",
        ),
        "香港理工大學": (
            "https://www.polyu.edu.hk/en/",
            "Hong Kong Polytechnic University official English website",
        ),
        "黎剎系統大學": (
            "https://www.urs.edu.ph/",
            "University of Rizal System official website",
        ),
    }
)

CURATED_DESTINATION_DETAILS = {
    "kyonggi university": {
        "housing_summary": (
            "京畿大學申請資料要求交換生繳交宿舍申請表；若不住宿舍，則須繳交校外住宿確認文件。"
            "住宿是否核配與實際費用仍以錄取後通知為準。"
        ),
        "cost_summary": (
            "交換生依校際協議向原就讀學校繳交學費，不另繳京畿大學學費；住宿、旅費與醫療保險"
            "等支出由學生自行負擔。"
        ),
        "campus_life_summary": (
            "交換生須由姊妹校正式提名，錄取通知會一併說明簽證、選課、入境準備與免費接機資訊。"
        ),
        "coverage_status": "official_verified",
        "sources": [
            (
                "Student Exchange Program | Kyonggi University",
                "https://www.kyonggi.ac.kr/international_kgu/contents.do?key=7582",
            ),
        ],
    },
    "dongguk university": {
        "housing_summary": (
            "東國大學官方住宿頁列有 Chungmu Residence Hall：距忠武路站步行約 1 分鐘，"
            "為附家具三人房、房外共用衛浴並提供 Wi-Fi；入住期、房費、退款與延長規則應以當期公告為準。"
        ),
        "transport_summary": (
            "首爾校區位於首爾中區，官方交通頁建議由地鐵 3 號線東大入口站 6 號出口步行約 5 分鐘到校；"
            "也可由忠武路站轉乘或步行，機場出發路線應按抵達時間與宿舍位置重新確認。"
        ),
        "campus_life_summary": (
            "東國大學國際學生辦公室提供學籍、移民與生活適應的一站式支援，並列有交換計畫、"
            "國際學生服務與多語諮詢的專責聯絡方式。"
        ),
        "coverage_status": "official_verified",
        "sources": [
            (
                "Office of International Students | Dongguk University",
                "https://www.dongguk.edu/eng/page/1525",
            ),
            (
                "International Student Guide Book | Dongguk University",
                "https://www.dongguk.edu/resources/pdf/24_Stduent_Guide_Book_Eng.pdf",
            ),
            (
                "How to Get to Dongguk University",
                "https://www.dongguk.edu/eng/page/1514",
            ),
            (
                "Residence | Dongguk University",
                "https://www.dongguk.edu/eng/page/1530",
            ),
        ],
        "source_summaries": {
            "https://www.dongguk.edu/eng/page/1514": (
                "東國大學官方交通頁列出首爾校區地址，以及東大入口站 6 號出口步行約 5 分鐘、"
                "忠武路站與公車等到校方式。"
            ),
            "https://www.dongguk.edu/eng/page/1530": (
                "東國大學官方住宿頁列出 Chungmu Residence Hall 的房型、共用設施、Wi-Fi、"
                "住宿期間與付款規則，費用須以當期公告為準。"
            ),
        },
        "guide_photos": [
            {
                "image_url": "/static/assets/guides/dongguk-chungmu-1.jpg",
                "source_url": "https://www.dongguk.edu/eng/page/1530",
                "alt": "東國大學 Chungmu Residence Hall 三人房與書桌",
                "caption": "Chungmu Residence Hall 附家具三人房；實際房型與床位配置以校方當期安排為準。",
                "category": "housing",
            },
            {
                "image_url": "/static/assets/guides/dongguk-chungmu-2.jpg",
                "source_url": "https://www.dongguk.edu/eng/page/1530",
                "alt": "東國大學 Chungmu Residence Hall 共用廚房與用餐區",
                "caption": "Chungmu Residence Hall 共用廚房與用餐空間。",
                "category": "housing",
            },
            {
                "image_url": "/static/assets/guides/dongguk-chungmu-3.jpg",
                "source_url": "https://www.dongguk.edu/eng/page/1530",
                "alt": "東國大學 Chungmu Residence Hall 洗衣空間",
                "caption": "Chungmu Residence Hall 洗衣與整燙空間。",
                "category": "housing",
            },
            {
                "image_url": "/static/assets/guides/dongguk-chungmu-4.jpg",
                "source_url": "https://www.dongguk.edu/eng/page/1530",
                "alt": "東國大學 Chungmu Residence Hall 建築入口",
                "caption": "Chungmu Residence Hall 建築入口與周邊街景。",
                "category": "housing",
            },
        ],
    },
    "pukyong national university": {
        "transport_summary": (
            "釜慶大學大淵校區位於釜山地鐵 2 號線慶星大學・釜慶大學站周邊；官方交通頁另列"
            "釜山站、西部客運站與兩校區的地鐵及公車路線。"
        ),
        "campus_life_summary": (
            "官方校園資訊區分大淵與龍塘兩校區，並提供校址、校園地圖與交通方式；學生需依"
            "實際開課及住宿安排確認主要活動校區。"
        ),
        "coverage_status": "official_verified",
        "sources": [
            (
                "Campus Information | Pukyong National University",
                "https://www.pknu.ac.kr/eng/45",
            ),
            (
                "Pukyong National University Official Website",
                "https://www.pknu.ac.kr/eng",
            ),
        ],
    },
    "kyungpook national university": {
        "housing_summary": (
            "交換生會自動安排入住校內宿舍雙人房；每學期費用依餐食方案約為 500 至 1,000 美元，"
            "宿舍餐廳不提供特殊飲食選項。"
        ),
        "cost_summary": (
            "申請財力證明的官方標準為一學期 800 萬韓元、兩學期以上 1,600 萬韓元；持 D-2 簽證"
            "者原則上會納入韓國國民健康保險，實際月費以帳單為準。"
        ),
        "campus_life_summary": (
            "校方為新交換生安排韓國學生 buddy；英語授課清單通常在春季課前一月、秋季課前七月"
            "公布，大學部每學期上限 18 學分。"
        ),
        "coverage_status": "official_verified",
        "sources": [
            (
                "Exchange Student Program | Kyungpook National University",
                "https://en.knu.ac.kr/admission/exchange01.htm",
            ),
        ],
    },
    "sungshin women's university": {
        "housing_summary": (
            "誠信女子大學修井校區鄰近兩棟學生宿舍：Sungmi Building 距正門步行約 3 分鐘，"
            "Sungmiryo Building 距正門約 1 分鐘；交換生實際申請資格與房型以當期通知為準。"
        ),
        "transport_summary": (
            "修井主校區位於首爾，從地鐵 4 號線誠信女大入口站步行約 10 分鐘；另有彌阿的雲庭"
            "綠色校區，選課前應確認課程所在校區。"
        ),
        "campus_life_summary": (
            "修井校區設有中央圖書館、學生中心、國際會議中心、體育館與國際教育中心等設施。"
        ),
        "coverage_status": "official_verified",
        "sources": [
            (
                "Soojung Campus Guide | Sungshin Women's University",
                "https://www.sungshin.ac.kr/main_eng/20058/subview.do",
            ),
            (
                "International Admissions | Sungshin Women's University",
                "https://www.sungshin.ac.kr/main_eng/15057/subview.do",
            ),
        ],
    },
    "erica hanyang university erica": {
        "transport_summary": (
            "ERICA 校區位於京畿道安山市，與漢陽大學首爾校區不同；學生應依錄取通知確認抵達、"
            "住宿與校區交通安排。"
        ),
        "campus_life_summary": (
            "ERICA 校區以產學合作與實作教育為特色；校方另有 Hanmille 交流活動，由本地學生"
            "協助外籍交換生適應韓國與校園生活。"
        ),
        "coverage_status": "official_verified",
        "sources": [
            (
                "ERICA Campus | Hanyang University",
                "https://www.hanyang.ac.kr/web/eng/erica-campus1",
            ),
            (
                "International Programs (ERICA) | Hanyang University",
                "https://www.hanyang.ac.kr/en/web/eng/global_e",
            ),
        ],
    },
    "kwangwoon university": {
        "housing_summary": (
            "交換生可依校方資訊選擇學生宿舍或自行安排校外住宿；宿舍名額、房型與費用須以當期"
            "交換生通知為準。"
        ),
        "transport_summary": (
            "光云大學距首都圈電鐵 1 號線光云大學站步行約 6 分鐘，距 6 號線石溪站約 10 分鐘；"
            "學期間平日上午另有石溪站接駁車。"
        ),
        "campus_life_summary": (
            "官方校園導覽列出國際學舍、中央圖書館、學生福利設施、文化藝術中心與主要教學大樓。"
        ),
        "coverage_status": "official_verified",
        "sources": [
            (
                "Campus Tour | Kwangwoon University",
                "https://www.kw.ac.kr/en/about/tour01.jsp",
            ),
            (
                "Location and Transportation | Kwangwoon University",
                "https://www.kw.ac.kr/en/about/tour02.jsp",
            ),
            (
                "Exchange Student Fact Sheet | Kwangwoon University",
                "https://www.kw.ac.kr/en/admission/KWU_Factsheet%202021.pdf",
            ),
        ],
    },
    "kwansei gakuin university": {
        "cost_summary": (
            "目前找到的費用頁是一般學位生入學費用，不應直接當成交換生生活預算；"
            "交換生仍須依當期住宿、餐食與交通通知另行估算。"
        ),
        "housing_summary": (
            "校方交換生住宿頁提供宿舍、寄宿家庭與自行租屋三種選擇；宿舍會依供應量與個別需求分配，"
            "不保證入住第一志願，分配結果公布後原則上不能更改。"
        ),
        "campus_life_summary": (
            "官方 Campus Life 入口整合社團活動、校園設施、學生服務、學年行事曆與成績證明等資訊；"
            "實際可參加項目以交換學期公告為準。"
        ),
        "coverage_status": "official_verified",
        "sources": [
            (
                "Accommodations for Exchange Students | Kwansei Gakuin University",
                "https://www.kwansei.ac.jp/en/campuslife/accommodations/application-exchange.html",
            ),
            (
                "Campus Life and Student Support | Kwansei Gakuin University",
                "https://www.kwansei.ac.jp/en/campuslife/",
            ),
        ],
    },
    "saga university": {
        "housing_summary": (
            "佐賀大學留學生會館距校園步行約 3 分鐘；單人房附廚房、浴廁、冷暖氣與基本家具，"
            "官方列示月租 11,000 日圓，原則上最長入住 1 年，申請資訊通常於 1 月及 7 月公告。"
        ),
        "cost_summary": (
            "留學生會館單人房官方月租為 11,000 日圓；水電、房內網路合約與退房清潔費另計。"
            "若住校外，學生須自行找房並確認保證人與留學生住宅保險條件。"
        ),
        "campus_life_summary": (
            "國際學生 tutor 可協助校園與市公所手續、初期採買、找房及機場接送等生活適應事項；"
            "是否提供與安排方式以當期國際處通知為準。"
        ),
        "coverage_status": "official_verified",
        "sources": [
            (
                "Saga University International House and Private Apartments",
                "https://www.irdc.saga-u.ac.jp/en/foreignstudent/dormitory/",
            ),
            (
                "Tutor System for International Students | Saga University",
                "https://www.irdc.saga-u.ac.jp/en/tutor-top/",
            ),
        ],
    },
    "international college of liberal arts(icla) at yamanashi gakuin university": {
        "housing_summary": (
            "iCLA 的國際宿舍由日本學生與各國學生共同居住，設有樓層學生 leader 協助生活溝通；"
            "交換生實際房型與是否安排校內住宿，仍以該學期錄取及住宿通知為準。"
        ),
        "transport_summary": (
            "iCLA 位於山梨縣甲府市，校方介紹約距東京都心 90 分鐘；實際通勤、機場轉乘與末班車"
            "應依出發學期的官方交通資訊另行規劃。"
        ),
        "campus_life_summary": (
            "iCLA 為英語授課的博雅學院，學生可參與運動、音樂、藝術及山梨學院大學社團；"
            "校內另有交流空間與 24 小時自習空間。"
        ),
        "coverage_status": "official_verified",
        "sources": [
            (
                "Campus Life | International College of Liberal Arts",
                "https://www.icla.ygu.ac.jp/en/campus-life/",
            ),
            (
                "Dormitory Life | International College of Liberal Arts",
                "https://www.icla.ygu.ac.jp/jp/dormitory/",
            ),
            (
                "iCLA Official Website",
                "https://www.icla.ygu.ac.jp/en/",
            ),
        ],
    },
    "the university of electro-communications;uec": {
        "housing_summary": (
            "UEC Port 提供附家具的 KIZUNA 套房型宿舍與 TOMODACHI 分租型宿舍，官方列示合計 400 間；"
            "校內 International House 供國際生與外籍研究人員居住，原則上最長 1 年。"
        ),
        "campus_life_summary": (
            "宿舍位於東京都調布市；房型、交換生可申請資格、空房與入住期間須以當期 UEC 國際處"
            "及宿舍公告確認。"
        ),
        "coverage_status": "official_partial",
        "sources": [
            (
                "Student Dormitories | The University of Electro-Communications",
                "https://www.uec.ac.jp/eng/campus/dormitory.html",
            ),
        ],
    },
}

CURATED_DESTINATION_DETAILS.update(
    {
        "hitotsubashi university": {
            "housing_summary": (
                "交換生可優先申請小平國際校區的一橋寮單人房；錄取後校方會另寄住宿申請資料，"
                "房間仍須依當期名額與期限完成申請。"
            ),
            "campus_life_summary": (
                "交換生須先由原校提名，可交換一學期或一學年；校內另有英語授課的 HGP、語言交流活動，"
                "以及宿舍 RA／CA 協助生活與跨文化交流。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Exchange Students | Hitotsubashi University",
                    "https://international.hit-u.ac.jp/en/pros/exchange/",
                ),
                (
                    "Accommodation | Hitotsubashi University",
                    "https://international.hit-u.ac.jp/en/curr/accom/",
                ),
            ],
        },
        "meiji university": {
            "housing_summary": (
                "交換生可申請明治大學安排的宿舍，但房型由校方依名額分配；超額時可能需要自行在東京找房，"
                "因此錄取後要同步確認住宿結果與付款期限。"
            ),
            "cost_summary": (
                "申請在留資格證明時須準備財力證明；官方 2027 資訊以一年 144 萬日圓、半年 72 萬日圓"
                "作為財力文件的最低參考額。"
            ),
            "campus_life_summary": (
                "交換生須由姊妹校提名後完成線上申請；多數課程為日語授課，但部分學院提供英語課程，"
                "所有交換生也能依程度修讀日語課。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Exchange Student Program | Meiji University",
                    "https://www.meiji.ac.jp/cip/english/admissions/exchange.html",
                ),
                (
                    "Exchange Program Fact Sheet | Meiji University",
                    "https://www.meiji.ac.jp/cip/english/admissions/FACTSHEET4exchange_EN.html",
                ),
            ],
        },
        "chuo university": {
            "housing_summary": (
                "中央大學交換資料列有校方宿舍與校外住宿選項；不同校區的通勤距離不同，"
                "收到錄取通知後要依所屬校區確認宿舍、費用與入住期間。"
            ),
            "campus_life_summary": (
                "姊妹校學生可申請一學期或一學年之非學位交換；國際中心負責交換與國際學生支援，"
                "實際課程、校區及住宿以當年度交換生說明為準。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "On Exchange | Chuo University",
                    "https://www.chuo-u.ac.jp/english/admissions/exchange/",
                ),
            ],
        },
        "utsunomiya university": {
            "campus_life_summary": (
                "宇都宮大學同時有校級與院級交換協議；臺北大學名額所屬的國際學部學生，"
                "送件前應由國際處確認協議層級、可修課範圍與接待窗口。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                (
                    "Exchange Agreements | Utsunomiya University",
                    "https://www.utsunomiya-u.ac.jp/en/agreement/index.php",
                ),
                (
                    "Utsunomiya University Official Website",
                    "https://www.utsunomiya-u.ac.jp/en/",
                ),
            ],
        },
        "kobe university": {
            "housing_summary": (
                "交換生可優先分配神戶大學宿舍的單人房，但仍受空房限制；選擇校外租屋者須自行找房與簽約。"
            ),
            "transport_summary": (
                "部分宿舍前往六甲台校區約需 40 至 50 分鐘並會產生交通費，選宿舍時要把所屬法學部校區"
                "與通勤時間一起比較。"
            ),
            "campus_life_summary": (
                "神戶大學校級交換的春季與秋季提名、申請、COE、宿舍及抵達時程均分開公告；"
                "院級協議學生須另向原校與法學部確認適用時程。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Application Schedule | Kobe University",
                    "https://www.kobe-u.ac.jp/en/academics/admissions/exchange-programs/application-schedule/",
                ),
                (
                    "Accommodation for Exchange Students | Kobe University",
                    "https://www.kobe-u.ac.jp/en/academics/admissions/exchange-programs/accommodation/",
                ),
            ],
        },
        "konan university": {
            "campus_life_summary": (
                "甲南大學官方英文網站提供學院、校園與國際交流入口；交換生的指定課程、住宿與費用資訊"
                "需在臺北大學完成提名後，以甲南大學寄發的當期申請文件為準。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                ("Konan University Official Website", "https://www.konan-u.ac.jp/english/"),
            ],
        },
        "osaka university of economics": {
            "housing_summary": (
                "校方公開住宿資訊包含女子學生寮、供餐合作宿舍與校外套房；交換生可否入住及申請方式"
                "仍應以國際交流窗口的錄取通知為準。"
            ),
            "campus_life_summary": (
                "大阪經濟大學官方頁說明交換期間可為半年或一年，並可依原校規定申請學分抵免；"
                "實際課程與交換條件須由兩校國際處確認。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                (
                    "International Exchange | Osaka University of Economics",
                    "https://www.osaka-ue.ac.jp/entrance/english/international/index.html",
                ),
                (
                    "Housing Guide | Osaka University of Economics",
                    "https://www.osaka-ue.ac.jp/campus/living/",
                ),
            ],
        },
        "the university of tsukuba": {
            "housing_summary": (
                "短期交換生可申請一之矢地區的 Short Stay House；官方特別提醒其他校內住宿不對交換生開放，"
                "校外租屋也不提供代找服務。"
            ),
            "cost_summary": (
                "校方估計除學費與宿舍外，餐食、衣物及教材等生活支出平均約每月 80,000 日圓；"
                "實際費用仍依住宿與個人生活方式調整。"
            ),
            "campus_life_summary": (
                "所有申請人須由姊妹校正式提名，再完成線上申請與 UTOS 文件上傳；入學月份不同，"
                "提名、申請與文件截止日也不同。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Exchange Program | University of Tsukuba",
                    "https://www.tsukuba.ac.jp/en/academics/international-exchange-students/programs/",
                ),
                (
                    "Living Expenses | University of Tsukuba",
                    "https://www.tsukuba.ac.jp/en/admissions/fees-living-expenses/",
                ),
            ],
        },
    }
)

CURATED_DESTINATION_DETAILS.update(
    {
        "上海立信會計 金融學院": {
            "campus_life_summary": (
                "官方交換生指南列出國際交流處、國際交流學院與入境、簽證承辦窗口，校址位於上海浦東上川路；"
                "目前公開頁面未列出本梯次交換生的固定住宿費，應以錄取與抵校通知為準。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                ("International Exchange Student Guide | SLU", "https://en.lixin.edu.cn/Programs/list.htm"),
                ("International Students Office | SLU", "https://lxlx.lixin.edu.cn/"),
            ],
        },
        "上海財經大學": {
            "housing_summary": (
                "合作校正式提名並確認錄取後，交換生可依錄取資料中的指示線上申請校內住宿；"
                "宿舍名額仍須校方確認，不能視為自動保證。"
            ),
            "cost_summary": (
                "交換協議期間通常免繳上財學費，住宿與個人支出自理；官方舊版交換手冊提供每月約 1,000 至 1,500 元人民幣生活費參考，"
                "實際金額須看當期 factsheet。"
            ),
            "campus_life_summary": (
                "申請先由臺北大學提名，學生再依上財寄出的郵件完成線上申請；校園卡可用於用餐、宿舍門禁與圖書館。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("Incoming Exchange | SUFE", "https://iecoenglish.sufe.edu.cn/3446/list.htm"),
                ("Exchange Student Housing | SUFE", "https://iecoenglish.sufe.edu.cn/19907/list.htm"),
            ],
        },
        "天津大學": {
            "housing_summary": (
                "天津大學表示會為交換生提供校內住宿，衛津路與北洋園校區都有國際學生宿舍，費用參考約每晚 60 元人民幣。"
            ),
            "cost_summary": (
                "國際學生須購買校方指定保險，官方目前列出半年 400 元、一年 800 元人民幣；其他費用依交換協議與錄取通知。"
            ),
            "campus_life_summary": (
                "交換生必須由合作校提名並由特定學院接收；原則上先選該學院課程，跨院選課要另取得授課單位同意。"
            ),
            "coverage_status": "official_verified",
            "sources": [("Exchange Programs | Tianjin University", "https://en.tju.edu.cn/info/1245/8733.htm")],
        },
        "華東師範大學": {
            "housing_summary": (
                "校內宿舍採線上預約、先到先得；只有已正式錄取且完成相關費用程序的學生能預約。未搶到床位者須自行安排校外住宿。"
            ),
            "cost_summary": (
                "官方國際生指南列出的校內雙人房約每床每天 40 至 70 元人民幣，校外租屋約每月 2,500 至 4,500 元；"
                "房價可能更新，交換生應以當期通知為準。"
            ),
            "campus_life_summary": (
                "宿舍分布於普陀與閔行校區，選課與住宿前要先確認實際接收校區，避免通勤安排錯誤。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("Accommodation | ECNU", "https://lxs.ecnu.edu.cn/en/accommodation/"),
                ("International Student Guide | ECNU", "https://lxs.ecnu.edu.cn/en/"),
            ],
        },
        "南開大學": {
            "housing_summary": (
                "八里臺與津南校區均有國際學生宿舍，提供單人或雙人房；也可校外租屋，但搬入後要依規定辦理住宿登記。"
            ),
            "cost_summary": (
                "校方 2026 國際生資訊列出住宿約每月 1,000 至 3,000 元人民幣、醫療保險每年 800 元；"
                "這是國際生參考，交換生實際收費仍以兩校協議與錄取通知為準。"
            ),
            "campus_life_summary": (
                "兩校區都有餐廳與清真餐點；申請前須確認課程所屬校區，再決定宿舍或校外住所。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("Accommodation | Nankai University", "https://ensie.nankai.edu.cn/STUDENT_SERVICE/ACCOMMODATION.htm"),
                ("2026 International Student Fees | Nankai University", "https://ensie.nankai.edu.cn/info/1089/1167.htm"),
            ],
        },
        "中國人民大學": {
            "housing_summary": (
                "錄取後會隨入學資料收到宿舍申請表，校內床位採先到先得；官方列出單人房每天 80 至 100 元、"
                "雙人房每人每天 31 至 40 元人民幣。"
            ),
            "campus_life_summary": (
                "人大國際關係學院交換流程為母校提名、線上申請、審核錄取；官方目前列出秋季提名 5 月 1 日、申請 5 月 15 日，"
                "春季提名 11 月 1 日、申請 11 月 15 日，但學生仍應以臺北大學當年度公告為準。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("Exchange Application | Renmin University", "https://sis.ruc.edu.cn/en/internationalExchange/studentexchange/exchange_application/index.htm"),
                ("Exchange Campus Life | Renmin University", "https://sis.ruc.edu.cn/en/internationalExchange/studentexchange/exchange_life/index.htm"),
            ],
        },
        "中國政法大學": {
            "campus_life_summary": (
                "國際教育學院負責交換生與國際生事務；目前公開頁面可確認學校與承辦單位，但未找到足以核對本梯次住宿、費用及截止日的完整交換生 factsheet。"
                "學生應等待臺北大學提名後收到的 CUPL 申請信。"
            ),
            "coverage_status": "official_partial",
            "sources": [("School of International Studies | CUPL", "https://sis.cupl.edu.cn/")],
            "source_summaries": {
                "https://sis.cupl.edu.cn/": (
                    "中國政法大學國際教育學院官方入口，提供國際學生教育、交換活動與承辦單位資訊；"
                    "目前首頁未公開臺北大學合作案的當期住宿費與申請截止日。"
                ),
            },
        },
        "北京體育大學": {
            "housing_summary": (
                "校方國際生資料列出雙人房每人每天 70 元、單人房每天 120 元人民幣；宿舍有空調與基本家具，實際安排以錄取通知為準。"
            ),
            "cost_summary": (
                "2026 國際生簡章列出保險每年 800 元、簽證約 500 元、體檢約 400 元人民幣；交換生是否適用全部項目須依校際協議確認。"
            ),
            "campus_life_summary": (
                "校園擁有大量室內外運動訓練場館；國際學生服務頁同時提供訪學生、短期項目與生活服務入口。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("International Student Services | BSU", "https://en.bsu.edu.cn/Campus/StudentLife/StudyandLifeServicesforInternationalStudents/index.htm"),
                ("2026 International Admission Prospectus | BSU", "https://en.bsu.edu.cn/NewsEvents/Events/86442500a53d414287abf5764edba4b2.htm"),
            ],
        },
        "西南大學": {
            "housing_summary": (
                "國際學院公布的住宿參考包含單人、雙人及四人房；目前資料為一般國際生標準，交換生能否分配及費率應以錄取通知為準。"
            ),
            "cost_summary": (
                "官方目前列出住宿每學期約 3,500 至 7,000 元人民幣、醫療保險每年 800 元；不要直接把一般國際生學費套用到校際交換生。"
            ),
            "campus_life_summary": (
                "線上申請、體檢、語言證明與簽證文件由國際學院辦理；公開頁面未提供臺北大學合作案的專屬交換生截止日。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                ("International Admissions | Southwest University", "https://admissions.swu.edu.cn/"),
                ("Tuition and Fees | Southwest University", "https://admissions.swu.edu.cn/Admissions/Tuition_and_Fees.htm"),
            ],
        },
        "山東師範大學": {
            "campus_life_summary": (
                "國際教育學院官網提供招生、費用、獎學金、學生服務與下載專區；目前公開英文頁面未列出臺北大學交換生的專屬住宿與截止日，"
                "需依提名後的通知補齊。"
            ),
            "coverage_status": "official_partial",
            "sources": [("International Students Office | Shandong Normal University", "https://en.cie.sdnu.edu.cn/")],
            "source_summaries": {
                "https://en.cie.sdnu.edu.cn/": (
                    "山東師範大學國際教育學院官方入口，集中提供課程、招生、獎學金、費用、學生服務與下載專區；"
                    "頁面未列出臺北大學交換生的專屬住宿與截止日期。"
                ),
            },
        },
        "東北林業大學": {
            "housing_summary": (
                "交換生可申請校內國際學生宿舍；官方列出雙人房每人每月 500 元、單人房每月 1,000 元人民幣。"
            ),
            "cost_summary": (
                "交換生學費依校際協議，住宿、保險與簽證費自理；保險為每學期 400 元或每年 800 元人民幣。"
            ),
            "campus_life_summary": (
                "交換期可為一學期或一學年，申請人須為合作校正式在學學生並繳交母校推薦信、成績單與語言證明；"
                "中文授課一般要求 HSK 4，英文授課的非英語母語者須提供英文能力證明。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("Exchange Program | Northeast Forestry University", "https://siee.nefu.edu.cn/English/Programs/_Exchange_Program.htm"),
                ("Accommodation | Northeast Forestry University", "https://siee.nefu.edu.cn/lxsh/zs.htm"),
            ],
        },
        "武漢大學": {
            "housing_summary": (
                "國際學生宿舍依校區與房型約每人每月 600 至 1,400 元人民幣；校內外住宿都必須完成臨時住宿登記。"
            ),
            "campus_life_summary": (
                "武大接受合作校交換生，交換期與費用依各校協議；選校時應先確認接收學院及課程所在校區，再安排住宿。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("Student Exchange Programs | Wuhan University", "https://en.whu.edu.cn/jzbf/International1/Students_Exchange_Programs.htm"),
                ("Campus Accommodation | Wuhan University", "https://en.whu.edu.cn/jzbf/Campus_Life1/Campus_Accommodation.htm"),
            ],
        },
        "華中農業大學": {
            "campus_life_summary": (
                "官方英文網站可核對學校、學院與國際交流入口；目前未找到足以確認臺北大學交換生住宿、費用與申請截止日的公開專頁，"
                "學生應以兩校提名後的申請包為準。"
            ),
            "coverage_status": "official_partial",
            "sources": [("Official English Website | Huazhong Agricultural University", "https://en.hzau.edu.cn/index.htm")],
        },
        "吉林大學": {
            "housing_summary": (
                "吉林大學有多處國際學生宿舍，2026 官方資料列出的床位約每天 25 至 60 元，另有每套每月 1,200 至 1,300 元的房型；"
                "分配會考量校區、課程與房源。"
            ),
            "campus_life_summary": (
                "國際教育學院負責錄取、報到與住宿資訊；目前公開費用主要來自一般國際生簡章，交換生仍須依校際協議確認學費與房型。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                ("College of International Education | Jilin University", "https://cie.jlu.edu.cn/"),
                ("2026 International Student Accommodation | Jilin University", "https://cie.jlu.edu.cn/info/1079/3656.htm"),
            ],
        },
        "四川大學": {
            "housing_summary": (
                "校方可提供宿舍，交換生不必另外自行預約，通常由交換項目承辦人協助保留；也可選擇住校外。"
            ),
            "campus_life_summary": (
                "申請人須為與四川大學有有效交換協議之合作校在學生，先由母校提名，且通常須已在母校完成至少一年學業；"
                "交換生也需要體檢並購買來華留學生保險。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("Exchange Application and Admission | Sichuan University", "https://global.scu.edu.cn/oso/article/index/1131"),
                ("Study and Campus Life FAQ | Sichuan University", "https://global.scu.edu.cn/oso/article/index/1134?lang=zh"),
            ],
        },
        "南京大學": {
            "city": "南京（仙林校區／鼓樓校區）",
            "housing_summary": (
                "交換生可申請仙林校區宿舍，但床位不保證；春季交換的住宿申請一般在 10 月 30 日前、秋季在 4 月 30 日前送件。"
                "雙人房每學期約 3,000 元、單人房約 6,000 元人民幣，另有押金與水電。"
            ),
            "transport_summary": (
                "鼓樓與仙林校區相距約 20 公里；校方抵達指南估計計程車約 40 分鐘、60 至 70 元人民幣，"
                "也可搭地鐵。校方不提供機場接送，報到地點在鼓樓校區，住宿與課程校區要先核對。"
            ),
            "campus_life_summary": (
                "必須先由臺北大學國際處提名；符合語言要求後，可選英文授課、中文授課或華語課程。校方建議交換生優先申請仙林校區雙人房。"
            ),
            "guide_photos": [
                {
                    "image_url": "/static/assets/guides/nju-xianlin-dorms.jpg",
                    "source_url": "https://stuex.nju.edu.cn/en_/wousing/list.htm",
                    "alt": "南京大學仙林校區學生宿舍建築",
                    "caption": "仙林校區學生宿舍建築；房型與實際分配仍以當期住宿通知為準。",
                    "category": "housing",
                },
                {
                    "image_url": "/static/assets/guides/nju-international-dorm-21.jpg",
                    "source_url": "https://stuex.nju.edu.cn/en_/wousing/list.htm",
                    "alt": "南京大學仙林校區留學生公寓二十一幢入口",
                    "caption": "仙林校區留學生公寓 21 幢入口。",
                    "category": "housing",
                },
                {
                    "image_url": "/static/assets/guides/nju-dorm-bathroom.jpg",
                    "source_url": "https://stuex.nju.edu.cn/en_/wousing/list.htm",
                    "alt": "南京大學留學生宿舍衛浴設施",
                    "caption": "官方住宿頁展示的宿舍衛浴設施。",
                    "category": "housing",
                },
                {
                    "image_url": "/static/assets/guides/nju-dorm-laundry.jpg",
                    "source_url": "https://stuex.nju.edu.cn/en_/wousing/list.htm",
                    "alt": "南京大學留學生宿舍洗衣設備",
                    "caption": "官方住宿頁展示的自助洗衣設備。",
                    "category": "housing",
                },
            ],
            "student_guide_sections": [
                {
                    "key": "courses_and_workload",
                    "title": "課程與課業強度",
                    "summary": (
                        "交換生可選華語、英語授課與中文授課課程；實際課表要等完成註冊後依 email 開放。"
                        "大學部只能在開學前兩週加退選，華語密集班每週 16 至 22 小時。"
                    ),
                    "points": [
                        "大學部透過選課系統登記；研究所課程通常要下載紙本表單並取得授課教師同意。",
                        "一則校方刊登的交換心得提到修四門課的負擔尚可，另一則提到與本地生共同簡報有壓力但很有收穫。",
                        "『嚴不嚴』不能用全校一個答案概括；選課前要逐門確認授課語言、評量、出席與小組報告。",
                    ],
                    "source_urls": [
                        "https://stuex.nju.edu.cn/en_/woursewwelection/list.htm",
                        "https://stuex.nju.edu.cn/en_/64/93/c23304a353427/page.htm",
                        "https://stuex.nju.edu.cn/en_/64/92/c23304a353426/page.htm",
                    ],
                    "evidence_type": "mixed",
                    "caution": "課業感受來自個別交換心得；不同學院、教師與學期可能差很多。",
                },
                {
                    "key": "faculty_and_teaching",
                    "title": "師資與授課方式",
                    "summary": (
                        "公開交換指南沒有替所有交換課列出固定師資。已找到的學生心得提到教授願意提供協助，"
                        "但課程可能含簡報、跨文化小組合作與中文課堂互動。"
                    ),
                    "points": [
                        "先用選課系統查看當學期教師與課綱，不把舊心得中的教授評價套到所有課程。",
                        "若想選跨系專業課，要特別確認先修條件、授課語言與是否需教師簽核。",
                        "中文能力會影響參與社團、本地生合作與中文授課課程的選擇範圍。",
                    ],
                    "source_urls": [
                        "https://stuex.nju.edu.cn/en_/woursewwelection/list.htm",
                        "https://stuex.nju.edu.cn/en_/64/93/c23304a353427/page.htm",
                        "https://stuex.nju.edu.cn/en_/64/92/c23304a353426/page.htm",
                    ],
                    "evidence_type": "mixed",
                    "caution": "教師與課綱會隨學期調整，最後以當期選課系統為準。",
                },
                {
                    "key": "housing_reality",
                    "title": "住宿真實情況",
                    "summary": (
                        "仙林校區宿舍可申請但不保證床位；宿舍有基本家具、衛浴與自助洗衣等設施。"
                        "有心得提醒國際宿舍到教學區與食堂要走一段路，冬季體感也可能偏冷。"
                    ),
                    "points": [
                        "官方頁列出仙林雙人房每學期約 3,000 元、單人房約 6,000 元，另收押金、水電；費率要在申請時再確認。",
                        "宿舍不提供床上用品，官方頁有列可到校購買的寢具套裝，但價格欄位有 360／380 元差異。",
                        "住宿申請、房型與校區會直接影響通勤；不要在收到核配前把校內床位當成已確定。",
                    ],
                    "source_urls": [
                        "https://stuex.nju.edu.cn/en_/wousing/list.htm",
                        "https://stuex.nju.edu.cn/en_/wormitorywwacilities/list.htm",
                        "https://stuex.nju.edu.cn/en_/64/92/c23304a353426/page.htm",
                    ],
                    "evidence_type": "mixed",
                    "caution": "住宿費與設備頁未清楚標示更新日期，申請前要向校方確認當期版本。",
                },
                {
                    "key": "neighborhood_and_daily_life",
                    "title": "學校附近機能",
                    "summary": (
                        "仙林校區內外可找到食堂、超市、醫療與運動設施；鼓樓校區較靠近市中心。"
                        "仙林較安靜、適合讀書，但往市區時間較長。"
                    ),
                    "points": [
                        "仙林校區有 11 間食堂、鼓樓有 4 間，主要以校園卡付款。",
                        "仙林宿舍 2、3 號樓附近有校內超市；兩校區皆有校醫院，校園卡可支付校內醫療。",
                        "學生心得對食堂口味有不同看法；可把校內餐廳當基本方案，再依個人口味探索校外。",
                    ],
                    "source_urls": [
                        "https://stuex.nju.edu.cn/en_/weals/list.htm",
                        "https://stuex.nju.edu.cn/en_/whoppingwinwwanjing/list.htm",
                        "https://stuex.nju.edu.cn/en_/23293/list.htm",
                        "https://stuex.nju.edu.cn/en_/64/93/c23304a353427/page.htm",
                    ],
                    "evidence_type": "mixed",
                },
                {
                    "key": "mobile_money_and_cards",
                    "title": "門號、現金、辦卡與網路",
                    "summary": (
                        "先辦中國門號，再用學號／護照號啟用 SSO 並綁定 NJU App；App 可進校、看課表、"
                        "儲值校園卡與繳網路費。開學初仍要準備少量人民幣現金。"
                    ),
                    "points": [
                        "中國移動、聯通或電信門市可辦 SIM；NJU App 綁定時需要中國手機號。",
                        "校園卡兼具身分與消費功能，官方指引要求帶護照並準備 20 元現金購卡，首次建議儲值超過 100 元。",
                        "外籍學生可持護照到南京市內銀行申請人民幣或外幣帳戶；實際開戶文件與可用支付服務仍以銀行現場審核為準。",
                        "校園 Wi-Fi 官方頁列每月約 20 至 30 元，可由 NJU App 或微信公眾號繳費。",
                    ],
                    "source_urls": [
                        "https://stuex.nju.edu.cn/en_/NJUAPPwSingleSignwonAccount/list.htm",
                        "https://stuex.nju.edu.cn/en_/23290/list.htm",
                        "https://stuex.nju.edu.cn/en_/whangingwwwwavingwwoney/list.htm",
                    ],
                    "evidence_type": "official",
                    "caution": "電信方案、銀行開戶與行動支付規則可能變動；抵達時要重新確認。",
                },
                {
                    "key": "transport_and_arrival",
                    "title": "交通與第一次到校",
                    "summary": (
                        "校方不提供機場接送，交換生要自行前往鼓樓校區報到，再依住宿安排前往仙林。"
                        "兩校區相距約 20 公里，可搭地鐵、計程車或校車。"
                    ),
                    "points": [
                        "抵達前先確認自己住鼓樓西苑賓館或仙林 21 幢，不要只把『南京大學』丟給司機。",
                        "官方指南估計鼓樓到仙林計程車約 40 分鐘、60 至 70 元；校際班車以校園卡支付。",
                        "若要買腳踏車，官方頁舊參考為新車 400 元以上、二手 200 至 300 元；先住一週確認通勤需求再買。",
                    ],
                    "source_urls": [
                        "https://stuex.nju.edu.cn/en_/23286/list.htm",
                        "https://stuex.nju.edu.cn/en_/64/88/c23304a353416/page.htm",
                    ],
                    "evidence_type": "mixed",
                    "caution": "車資與班車時刻可能變動，出發前以校方最新通知與地圖 App 為準。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "到鼓樓校區完成報到",
                    "detail": "校方目前不提供機場接送；帶齊護照、錄取文件與照片，到鼓樓校區報到後再確認宿舍與校區交通。",
                    "timing": "抵達當天",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/23286/list.htm", "https://stuex.nju.edu.cn/en_/23287/list.htm"],
                },
                {
                    "title": "辦中國門號並啟用 NJU App",
                    "detail": "持護照到中國移動、聯通或電信門市詢問學生方案；App 綁定需要中國手機號，SSO 初始密碼為護照號。",
                    "timing": "第 1 天",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/NJUAPPwSingleSignwonAccount/list.htm"],
                },
                {
                    "title": "取得住宿登記與處理簽證",
                    "detail": "住宿舍者向櫃台取得臨時住宿登記；X1 且停留超過半年者須在入境 30 天內申請居留許可。",
                    "timing": "第 1～2 天",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/23292/list.htm"],
                },
                {
                    "title": "辦校園卡、儲值並開通網路",
                    "detail": "帶護照與至少 20 元現金購買校園卡；啟用 App 後可儲值校園卡、繳 Wi-Fi 費並查課表。",
                    "timing": "第 1～2 天",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/23290/list.htm", "https://stuex.nju.edu.cn/en_/NJUAPPwSingleSignwonAccount/list.htm"],
                },
                {
                    "title": "確認選課信與加退選截止",
                    "detail": "完成註冊後等待國際處 email 與選課號；大學部加退選只開放學期前兩週。",
                    "timing": "第 2～3 天",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/woursewwelection/list.htm"],
                },
            ],
            "packing_from_taiwan": [
                {
                    "title": "證件正本與備份",
                    "detail": "護照、錄取通知、JW202、需要時的體檢正本，以及數張兩吋照片；另留雲端與紙本備份。",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/23287/list.htm", "https://stuex.nju.edu.cn/en_/wtudentwward/list.htm"],
                },
                {
                    "title": "保暖層、羽絨外套與雨具",
                    "detail": "南京夏季濕熱、梅雨明顯，冬季冷且乾；北大交換心得也特別提醒發熱衣與羽絨外套。",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/wravellingwinwwhina/list.htm", "https://cms-carrier.ntpu.edu.tw/uploads/110_efa2f2f2ab.pdf"],
                    "evidence_type": "mixed",
                },
                {
                    "title": "轉接頭、延長線與常備藥",
                    "detail": "北大學生心得建議從臺灣帶轉接頭、延長線與習慣的感冒藥；處方藥要保留處方或英文藥袋。",
                    "source_urls": ["https://cms-carrier.ntpu.edu.tw/uploads/110_efa2f2f2ab.pdf"],
                    "evidence_type": "student_experience",
                },
                {
                    "title": "首日可用的人民幣現金",
                    "detail": "準備小額現金支付校園卡、交通與尚未綁定行動支付前的支出，不必攜帶大量現金。",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/23287/list.htm", "https://stuex.nju.edu.cn/en_/23290/list.htm"],
                },
            ],
            "buy_after_arrival": [
                {
                    "title": "寢具與大型生活用品",
                    "detail": "宿舍不附床上用品；確認房型與床尺寸後，再買校方套裝或在當地補齊，避免從臺灣搬錯尺寸。",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/wousing/list.htm"],
                },
                {
                    "title": "中國 SIM 與校園卡",
                    "detail": "門號與校園卡都需要抵達後依護照、學號及現場方案辦理；不要先在臺灣買長約方案。",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/NJUAPPwSingleSignwonAccount/list.htm", "https://stuex.nju.edu.cn/en_/23290/list.htm"],
                },
                {
                    "title": "盥洗、清潔與日常消耗品",
                    "detail": "仙林宿舍區附近有校內超市，先帶 2～3 天旅行份量，其餘到校確認房間後購買。",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/whoppingwinwwanjing/list.htm"],
                },
                {
                    "title": "腳踏車或額外交通工具",
                    "detail": "先確認住宿、上課校區與實際步行距離，再決定是否買二手車；不要在報到前先下單。",
                    "source_urls": ["https://stuex.nju.edu.cn/en_/23286/list.htm"],
                    "evidence_type": "practical_inference",
                },
            ],
            "coverage_status": "official_verified",
            "coverage_note": (
                "已整理南京大學交換指南、校方刊登的交換心得與臺北大學舊生報告；"
                "費用、門號、銀行與交通等會變動的項目均標示需在出發前再確認。"
            ),
            "sources": [
                ("International Student Exchange Program | Nanjing University", "https://stuex.nju.edu.cn/en_/NonwdegreeProgram/list.htm"),
                ("Exchange Student Housing | Nanjing University", "https://stuex.nju.edu.cn/en_/wousing/list.htm"),
                ("Dormitory Facilities | Nanjing University", "https://stuex.nju.edu.cn/en_/wormitorywwacilities/list.htm"),
                ("Course Selection | Nanjing University", "https://stuex.nju.edu.cn/en_/woursewwelection/list.htm"),
                ("NJU APP & Single Sign-on Account", "https://stuex.nju.edu.cn/en_/NJUAPPwSingleSignwonAccount/list.htm"),
                ("Campus Card | Nanjing University", "https://stuex.nju.edu.cn/en_/23290/list.htm"),
                ("Getting to Campus | Nanjing University", "https://stuex.nju.edu.cn/en_/23286/list.htm"),
                ("New Student Enrollment | Nanjing University", "https://stuex.nju.edu.cn/en_/23287/list.htm"),
                ("Student Card | Nanjing University", "https://stuex.nju.edu.cn/en_/wtudentwward/list.htm"),
                ("Visa and Residence Permit | Nanjing University", "https://stuex.nju.edu.cn/en_/23292/list.htm"),
                ("Meals | Nanjing University", "https://stuex.nju.edu.cn/en_/weals/list.htm"),
                ("Shopping in Nanjing | Nanjing University", "https://stuex.nju.edu.cn/en_/whoppingwinwwanjing/list.htm"),
                ("Changing & Saving Money | Nanjing University", "https://stuex.nju.edu.cn/en_/whangingwwwwavingwwoney/list.htm"),
                ("Medical Services | Nanjing University", "https://stuex.nju.edu.cn/en_/23293/list.htm"),
                ("Travelling and Climate | Nanjing University", "https://stuex.nju.edu.cn/en_/wravellingwinwwhina/list.htm"),
                ("Reflections of an Exchange Student | Nanjing University", "https://stuex.nju.edu.cn/en_/64/92/c23304a353426/page.htm"),
                ("Exchange Review | Nanjing University", "https://stuex.nju.edu.cn/en_/64/93/c23304a353427/page.htm"),
                ("Exchange Experience | Nanjing University", "https://stuex.nju.edu.cn/en_/64/88/c23304a353416/page.htm"),
                ("NTPU Outbound Exchange Report: Nanjing University (110 academic year)", "https://cms-carrier.ntpu.edu.tw/uploads/110_efa2f2f2ab.pdf"),
            ],
        },
        "西北政法大學": {
            "housing_summary": (
                "官方交換指南列出長安校區雙人房，附空調、獨立衛浴與淋浴；2021 指南費用為每學期 1,500 元人民幣，"
                "因資料年份較早，現行費率必須再向校方確認。"
            ),
            "cost_summary": (
                "舊版交換指南列出免學費、保險每學期 400 元、體檢約 350 元人民幣；這些數字只作準備預算參考，不視為現行保證。"
            ),
            "campus_life_summary": (
                "可申請一學期的專業課或中文課，須有母校推薦、在學與成績證明、語言證明等；最新期限以臺北大學與接收校通知為準。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                ("Exchange Student Guide | Northwest University of Political Science and Law", "https://en.nwupl.edu.cn/admission/83096.htm"),
                ("International Student Admission | NWUPL", "https://en.nwupl.edu.cn/admission/106765.htm"),
            ],
        },
        "西安交通大學": {
            "housing_summary": (
                "若交換協議有住宿條款就依協議辦理；沒有特別條款時，交換生須自行付費預訂校內住宿，不能假設免費或自動保留。"
            ),
            "campus_life_summary": (
                "申請人須是有效合作協議下的全職學位生，先取得母校提名，再透過線上系統申請；申請費免收、學費依交換協議免除。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("Exchange Student Application Guide | Xi'an Jiaotong University", "https://sie.xjtu.edu.cn/en/exchange.pdf"),
                ("International Exchanges | Xi'an Jiaotong University", "https://en.xjtu.edu.cn/internationalexchanges.html"),
            ],
        },
        "廈門大學": {
            "housing_summary": (
                "思明校區國際生宿舍床位有限，未取得校內住宿者要在抵達前自行找房；官方參考為思明校區雙人房每床每天 35 至 65 元，"
                "校外鄰近租屋約每房每月 2,500 元人民幣。"
            ),
            "cost_summary": (
                "官方生活預算列出伙食每月約 1,000 至 1,500 元、醫療保險每年 800 元人民幣；交換生學費仍須依校際協議確認。"
            ),
            "campus_life_summary": (
                "學校有思明、翔安與漳州等校區，住宿條件與費率差異很大；錄取後應先確認課程校區，不能只依學校名稱訂房。"
            ),
            "coverage_status": "official_partial",
            "sources": [("Study Costs | Xiamen University", "https://admissions.xmu.edu.cn/Admissions/Costs.htm")],
        },
    }
)

CURATED_DESTINATION_DETAILS.update(
    {
        "fukushima university": {
            "housing_summary": (
                "福島大學國際會館提供附家具單人房，官方標示月費 8,900 日圓；校內男女宿舍單人房"
                "月費約 7,800 日圓，實際名額與其他費用須依當期公告。"
            ),
            "campus_life_summary": (
                "無日本保證人的國際學生若符合條件並加入指定租屋保險，校方可提供機構保證；"
                "入住前仍要確認適用房型與資格。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Housing for International Students | Fukushima University",
                    "https://english.adb.fukushima-u.ac.jp/international/housing.html",
                ),
            ],
        },
        "kindai university": {
            "housing_summary": (
                "近畿大學交換方案要求交換生入住校方安排的住宿；房型、費用、入住日與退宿規則"
                "應依錄取後寄發的交換生指南辦理。"
            ),
            "campus_life_summary": (
                "官方交換方案手冊集中說明課程、日語學習、住宿與校園支援；申請前要先確認"
                "臺北大學合作名額所對應的校區與學院。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Exchange Program Guide | Kindai University",
                    "https://www.kindai.ac.jp/english/files/study-at-kindai/program.pdf",
                ),
                ("Kindai University Official Website", "https://www.kindai.ac.jp/english/"),
            ],
        },
        "chiba university": {
            "housing_summary": (
                "千葉大學國際交流會館因建物老化已停止新申請；交換生應及早確認其他校方公告住宿、"
                "UR 住宅或自行租屋方案，不可把國際會館視為保證住宿。"
            ),
            "campus_life_summary": (
                "校內有 CISG 國際學生社群、LEX 語言交換與個別 tutor，協助新生適應課業與生活。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Housing | Chiba University",
                    "https://www.chiba-u.jp/global-edu/sai/housing.html",
                ),
                (
                    "Student Activities | Chiba University",
                    "https://www.chiba-u.jp/e/campus-life/friends/index.html",
                ),
            ],
        },
        "daito bunka university": {
            "housing_summary": (
                "交換生可依當期規定申請 Dormy Tsurugashima 學生宿舍；錄取後應核對房租、餐食、"
                "通勤與入住期間，不能只依一般新生宿舍資訊判斷。"
            ),
            "campus_life_summary": (
                "大東文化大學交換生須依國際交流中心公告完成申請；校方另提供跨文化交流與日語學習支援。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Exchange Student Application | Daito Bunka University",
                    "https://www.daito.ac.jp/international_exchange/admission/application.html",
                ),
                (
                    "Dormy Tsurugashima Student Dormitory",
                    "https://www.daito.ac.jp/international_exchange/admission/file/file_dormy_tsurugashima.pdf",
                ),
            ],
        },
        "nishikyusyu university": {
            "campus_life_summary": (
                "西九州大學官方網站可核對校名、校區與學術單位；目前公開頁面未完整列出交換生住宿、"
                "費用及抵達流程，學生應以兩校提名後寄發的申請資料為準。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                ("Nishikyushu University Official Website", "https://www.nisikyu-u.ac.jp/"),
            ],
        },
        "靜岡縣立大學": {
            "housing_summary": (
                "校方提供國際學生寮與校外租屋資訊；校外租屋月租參考約 25,000 至 60,000 日圓，"
                "簽約初期通常還要準備押金、禮金與仲介費。"
            ),
            "campus_life_summary": (
                "學校提供分級日語會話、JLPT 準備、conversation partner、IFC 國際學友會及留學生交流活動。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "International Student Support | University of Shizuoka",
                    "https://www.u-shizuoka-ken.ac.jp/exchange/international-student/",
                ),
                (
                    "International Dormitory FAQ | University of Shizuoka",
                    "https://eng.u-shizuoka-ken.ac.jp/media/FAQ_about_Dormitory.pdf",
                ),
            ],
        },
    }
)

CURATED_DESTINATION_DETAILS.update(
    {
        "adam mickiewicz university": {
            "housing_summary": (
                "AMU 官方宿舍頁明確提醒：提出宿舍申請不代表一定取得床位。"
                "宿舍分布於波茲南不同區域，房型與設施不一；收到核配前應保留校外住宿備案。"
            ),
            "transport_summary": (
                "AMU 表示各宿舍可連接波茲南大眾運輸；實際通勤時間取決於最後核配宿舍與上課院系，"
                "入住前要用兩個精確地址重新計算。"
            ),
            "campus_life_summary": (
                "交換生須先由合作校提名；官方目前列冬季／全學年提名截止 5 月 31 日、"
                "夏季提名截止 11 月 30 日，學生再進入 USOSirk 完成線上申請。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "How to Apply | Adam Mickiewicz University",
                    "https://erasmus.amu.edu.pl/en/incoming-students2/how-to-apply",
                ),
                (
                    "Exchange Student Fact Sheet | Adam Mickiewicz University",
                    "https://erasmus.amu.edu.pl/en/incoming-students2/fact-sheet-2425",
                ),
            ],
            "source_summaries": {
                "https://erasmus.amu.edu.pl/en/incoming-students2/how-to-apply": (
                    "AMU 官方交換頁說明合作校資格、母校提名、USOSirk 線上申請與分學期截止日；"
                    "學生應等校方提名後再建立申請。"
                ),
                "https://erasmus.amu.edu.pl/en/incoming-students2/fact-sheet-2425": (
                    "AMU 交換生 factsheet 彙整國際處聯絡、學期、提名與申請窗口，實際日期以當學年版本為準。"
                ),
            },
        },
        "kozminski university": {
            "housing_summary": (
                "Kozminski University 明確表示沒有校內宿舍；國際處可提供華沙住宿資訊與行政協助，"
                "但學生仍須自行比較房源、簽約與通勤。"
            ),
            "campus_life_summary": (
                "校方 incoming 頁集中提供當學年 factsheet、課程清單、課綱與行事曆；"
                "選課前要以交換生專用課表核對授課語言與開課學期。"
            ),
            "cost_summary": (
                "校方合作的私人宿舍多採含水電與 Wi-Fi 的方案，但房租、押金與取消條款依業者和房型不同；"
                "付款前應要求完整費用表，不把促銷碼視為固定折扣。"
            ),
            "transport_summary": (
                "校方列出的私人宿舍距校約數公里至十多公里，通勤差異大；"
                "選房時應用實際地址比較到校時間、夜間班次與轉乘次數。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Incoming Students | Kozminski University",
                    "https://www.kozminski.edu.pl/en/community/incoming-students",
                ),
            ],
            "source_summaries": {
                "https://www.kozminski.edu.pl/en/community/incoming-students": (
                    "Kozminski 官方 incoming 頁說明申請協調窗口、交換生課程與 factsheet；"
                    "並明確標示學校沒有校內住宿，只提供找房與合法居留等資訊協助。"
                ),
            },
        },
        "poznań university of economics and business": {
            "housing_summary": (
                "PUEB 可讓交換生申請學生宿舍，但房數有限且不保證每位申請人都有床位；"
                "收到提名後應同步準備校外備案。"
            ),
            "campus_life_summary": (
                "交換生先由母校提名，再依 PUEB 指示申請；每位學生可配對在地 mentor。"
                "學期通常含 15 週課程與其後兩週考試，校方另提供初級波蘭語課。"
            ),
            "cost_summary": (
                "校方住宿頁目前列雙人房每月約 800 PLN、單人房約 1,100–1,200 PLN，"
                "入住時另收約一個月房租的可退押金；金額仍須以當期住宿通知核對。"
            ),
            "transport_summary": (
                "Feniks 等宿舍位於 Dożynkowa 一帶，可搭電車或公車往返校區與市中心；"
                "路線編號可能調整，應在出發前依宿舍核配地址查最新班次。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Incoming Exchange Students | PUEB",
                    "https://ue.poznan.pl/en/students/incoming-exchange-students/",
                ),
            ],
            "source_summaries": {
                "https://ue.poznan.pl/en/students/incoming-exchange-students/": (
                    "PUEB 官方頁說明母校提名後的申請、有限宿舍床位、mentor、學生證交通優惠、"
                    "學期結構與交換生語言課程。"
                ),
            },
        },
        "poznań university of technology": {
            "housing_summary": (
                "PUT 表示國際學生可申請位於校園內、完成整修的學生宿舍；"
                "交換生床位、房型、費用與申請期限仍以當期 incoming 通知為準。"
            ),
            "campus_life_summary": (
                "PUT incoming 專頁集中提供申請步驟、英語課程、行事曆、居留登記、醫療與 buddy 資訊；"
                "報到前應逐項核對當學期版本。"
            ),
            "cost_summary": (
                "校方部分住宿費頁面仍標示舊學年價格，因此不把舊金額當成現在房價；"
                "錄取後應直接向 incoming 團隊確認當學期房租、押金、網路與退宿費用。"
            ),
            "transport_summary": (
                "Piotrowo 宿舍區鄰近校區，前往舊城與火車站也有電車；"
                "實際時間仍取決於核配宿舍、上課建築與施工調整。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Erasmus Incoming | Poznań University of Technology",
                    "https://put.poznan.pl/en/erasmus-incoming",
                ),
            ],
            "source_summaries": {
                "https://put.poznan.pl/en/erasmus-incoming": (
                    "PUT 官方 incoming 頁彙整線上申請、課程、學年日曆、居留登記、醫療、到校證明與 buddy 支援。"
                ),
            },
        },
        "warsaw university of life sciences": {
            "campus_life_summary": (
                "非歐盟雙邊交換生須先由合作校提名；SGGW 目前公開頁列秋／冬季申請截止 7 月 15 日、"
                "英文至少 B2，並提供英語授課的大學部與碩士課程入口。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Non-EU Incoming Student Mobility | SGGW",
                    "https://rekrutacja.sggw.edu.pl/en/offer/REK_2026_27Z_WYMIENNE/programme/MOBILE/",
                ),
                (
                    "Welcome to SGGW",
                    "https://www.sggw.edu.pl/en/",
                ),
            ],
            "source_summaries": {
                "https://rekrutacja.sggw.edu.pl/en/offer/REK_2026_27Z_WYMIENNE/programme/MOBILE/": (
                    "SGGW 官方招募頁說明非歐盟合作校交換生須由母校提名，列出申請截止、B2 英語要求、"
                    "課程入口與 Learning Agreement。"
                ),
                "https://www.sggw.edu.pl/en/": (
                    "SGGW 官方英文首頁提供 WePoint 國際生支援入口與校園、學術及國際合作資訊。"
                ),
            },
        },
        "university of wrocław": {
            "cost_summary": (
                "UWr 官方生活頁將飲食預算分為每月約 600–750 PLN（低）、750–1,000 PLN（中）"
                "與 1,100–1,300 PLN（較高）；住宿與其他支出另計，實際預算依房型與生活方式調整。"
            ),
            "housing_summary": (
                "UWr 官方生活頁列出 Ołówek、Kredka、Dwudziestolatka、Słowianka 與 Parawanowiec 等學生宿舍；"
                "實際房型、名額與價格應以當期住宿公告確認。"
            ),
            "transport_summary": (
                "弗羅茨瓦夫市內以公車與電車為主；官方生活頁說明學生可用有效學生證購買折扣學期票，"
                "票價與 URBANCARD 規則須在出發前查最新版本。"
            ),
            "campus_life_summary": (
                "交換生可透過 Erasmus+、雙邊協議、CEEPUS 或 ISEP 入校；校方安排 Orientation Days，"
                "並有 International Office 與 buddy system 協助落地。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Incoming Exchange Students | University of Wrocław",
                    "https://international.uni.wroc.pl/en/incoming-exchange-students",
                ),
                (
                    "Living in Wrocław | University of Wrocław",
                    "https://international.uni.wroc.pl/en/welcome-point/living-wroclaw",
                ),
            ],
            "source_summaries": {
                "https://international.uni.wroc.pl/en/incoming-exchange-students": (
                    "UWr 官方 incoming 頁列交換管道、提名與申請期限、學年日曆和迎新日期。"
                ),
                "https://international.uni.wroc.pl/en/welcome-point/living-wroclaw": (
                    "UWr 官方生活頁整理宿舍、生活費、學生交通票、保險、銀行與緊急聯絡資訊。"
                ),
            },
        },
        "krakow university of economics": {
            "housing_summary": (
                "KUE incoming 頁目前連結私人學生宿舍選項，未承諾校內床位；"
                "學生應自行確認租約、押金、通勤與取消條款。"
            ),
            "campus_life_summary": (
                "學生須先由母校提名，再登入 IRKA 申請；官方目前列冬季／全學年提名截止 5 月 31 日，"
                "學生申請截止 6 月 15 日，夏季申請截止 11 月 30 日，並要求至少 B2 英語證明。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Incoming Students | Krakow University of Economics",
                    "https://bpz.uek.krakow.pl/en/incoming-students/",
                ),
            ],
            "source_summaries": {
                "https://bpz.uek.krakow.pl/en/incoming-students/": (
                    "KUE 官方 incoming 頁列母校提名、IRKA 申請、B2 英語、護照與照片等文件、"
                    "分學期截止日、課程與私人住宿入口。"
                ),
            },
        },
        "jagiellonian university faculty of philology": {
            "campus_life_summary": (
                "雙邊交換生先由母校提名，再完成線上申請；文件包含申請表、B2 英語證明、成績單、"
                "證件照與預選課程，最終錄取由接收院系決定。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Bilateral Exchange | Jagiellonian University",
                    "https://mymobility.uj.edu.pl/en-gb/offer/BILATERALNA_UTRECHT_2025/programme/UJ_BILATERAL_EXCHANGE/",
                ),
                (
                    "Faculty of Philology | Jagiellonian University",
                    "https://filg.uj.edu.pl/en_GB/",
                ),
            ],
            "source_summaries": {
                "https://mymobility.uj.edu.pl/en-gb/offer/BILATERALNA_UTRECHT_2025/programme/UJ_BILATERAL_EXCHANGE/": (
                    "UJ 官方雙邊交換頁說明母校提名、線上申請、B2 語言證明、成績單、照片、預選課程，"
                    "以及 5 月 31 日與 11 月 30 日的分學期申請期限。"
                ),
                "https://filg.uj.edu.pl/en_GB/": (
                    "UJ 文學院官方頁可核對接收院系、系所與學術資源；當期可修課程仍需等院系確認。"
                ),
            },
        },
    }
)

CURATED_DESTINATION_DETAILS.update(
    {
        "king mongkut's institue of technology ladkrabang": {
            "housing_summary": (
                "KMITL 官方來校交換頁提供 International Students Guidebook 與 Living@KMITL 入口，"
                "但目前公開頁未列交換生保證床位、房型及本梯次價格；錄取後要向 OIA 索取可入住清單。"
            ),
            "transport_summary": (
                "KMITL 位於曼谷 Lat Krabang、校址為 1 Chalong Krung 1 Alley；不要只輸入 KMITL 縮寫，"
                "抵達前應保存 OIA 所在的 President Building、宿舍泰文地址及接待人電話。"
            ),
            "campus_life_summary": (
                "2026 來校交換規定要求一學期修 3–6 門課（15–30 ECTS），多數課程採 17 週、"
                "3 學分約含每週 3 小時課堂與 6 小時研究／自修；另有圖書館、醫療、運動與校內銀行服務。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("Incoming Programs | KMITL OIA", "https://oia.kmitl.ac.th/incoming-programs/"),
                ("Living at KMITL | OIA", "https://oia.kmitl.ac.th/living-kmitl/"),
            ],
            "source_summaries": {
                "https://oia.kmitl.ac.th/incoming-programs/": (
                    "KMITL OIA 官方頁列出母校提名、線上申請、合併 PDF 文件、GPA 2.5、CEFR B1、"
                    "2026 學期與截止日、每學期 3–6 門課及 17 週工作量。"
                ),
                "https://oia.kmitl.ac.th/living-kmitl/": (
                    "KMITL 官方生活頁整理圖書館、醫療、運動設施、校內銀行與前往曼谷市區入口；"
                    "公開頁未承諾交換生住宿。"
                ),
            },
        },
        "thammasat university": {
            "housing_summary": (
                "Thammasat OIA 住宿頁分開列 Tha Prachan 與 Rangsit 周邊選項、房型、月租、押金、"
                "水電、設備與接駁；價格會調整，且交換生仍需依實際上課校區確認可申請房源。"
            ),
            "transport_summary": (
                "法政大學至少涉及 Tha Prachan 與 Rangsit 等校區，兩地不能當成同一個通勤圈；"
                "先以錄取院系、課表與住宿地址選房，Tha Prachan 宿舍頁另列平日接駁與公共運輸。"
            ),
            "campus_life_summary": (
                "AIMS 來校流程由母校國際處送件，通過後由院系審查並寄發錄取；官方校園生活頁列出"
                "圖書館、教室、醫院、餐廳、便利商店、洗衣、運動設施與 150 多個社團。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("Incoming AIMS Students | Thammasat OIA", "https://oia.tu.ac.th/aim-articles/"),
                ("Accommodation | Thammasat OIA", "https://oia.tu.ac.th/accommodation-page/"),
                ("Life at Thammasat", "https://tu.ac.th/en/education/campuslife/"),
            ],
            "source_summaries": {
                "https://oia.tu.ac.th/aim-articles/": (
                    "Thammasat OIA 官方來校頁說明由母校國際處申請、院系資格審查、約三週結果、"
                    "錄取信寄送與 Non-Immigrant ED 簽證步驟。"
                ),
                "https://oia.tu.ac.th/accommodation-page/": (
                    "官方住宿頁逐項列出 Tha Prachan、Rangsit 校內外住宿的房型、月租、押金、設備、"
                    "水電、保全與接駁；學生要依實際校區重新核對當期價格及空房。"
                ),
                "https://tu.ac.th/en/education/campuslife/": (
                    "法政大學官方校園生活頁介紹 Rangsit 的宿舍、餐飲、便利商店、洗衣、教室、醫院、"
                    "運動設施與學生社團，不能直接套用到 Tha Prachan 的通勤。"
                ),
            },
        },
        "king mongkut's university of technology thonburi (kmutt": {
            "housing_summary": (
                "KMUTT 官方住宿頁說明一般校內宿舍優先服務全日制大學生；國際學生常用的 Heliconia House"
                "為校內家具房、含 Wi-Fi、最多兩人共住，公開價為每房每月 15,000–18,000 泰銖，"
                "不含水電，預訂前仍要確認空房與取消條款。"
            ),
            "cost_summary": (
                "KMUTT 官方 exchange factsheet 提供住宿及生活費估算，但費用會依房型、押金、水電與生活方式改變；"
                "系統只把它當作規劃起點，不視為保證價格。"
            ),
            "transport_summary": (
                "主要交換校區為 Bangkok Bangmod，校方也有 Bangkhuntien 等校區；"
                "選課前必須逐門核對上課地點，再用實際住宿地址估算曼谷尖峰通勤。"
            ),
            "campus_life_summary": (
                "官方交換頁明列至少修 3 門或 9 學分、出席率 80%，評量可含分組、簡報、作業、課堂參與、"
                "小考、專題、期中與期末；偏好課程不保證開成，因此選課與備選課要同時準備。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Exchange Programs | KMUTT",
                    "https://www.kmutt.ac.th/internationalization/mobility-program/exchange-programs/",
                ),
                ("Housing | KMUTT", "https://www.kmutt.ac.th/en/kmutt-education/housing/"),
                ("Bangmod Campus | KMUTT", "https://www.kmutt.ac.th/en/about-kmutt/campus/"),
            ],
            "source_summaries": {
                "https://www.kmutt.ac.th/internationalization/mobility-program/exchange-programs/": (
                    "KMUTT 官方交換頁整理資格、英文文件、學期、截止日、最低修課量、選課限制、"
                    "80% 出席要求、評量方式、住宿、生活費與學生 Buddy。"
                ),
                "https://www.kmutt.ac.th/en/kmutt-education/housing/": (
                    "官方住宿頁列出 Bangmod／Bangkhuntien 校內宿舍容量、聯絡方式，以及 Heliconia House"
                    "家具、Wi-Fi、共住人數與每房月租；空房與費用仍要在預訂時重查。"
                ),
                "https://www.kmutt.ac.th/en/about-kmutt/campus/": (
                    "KMUTT 官方 Bangmod 校區頁列出院系、宿舍、教學大樓、校址與交通入口，"
                    "可用來避免把其他校區誤當成主要上課地點。"
                ),
            },
        },
        "prince of songkla university (psu": {
            "housing_summary": (
                "PSU 官方 One-Stop Service 提供國際宿舍預約入口；校方設施頁表示國際學生可住校內，"
                "但 PSU 有五個校區，房型、價格與床位必須先依錄取校區確認，不能拿 Phuket 或 Pattani 的房價套用 Hat Yai。"
            ),
            "transport_summary": (
                "PSU 官方 Soft Landing 指南說明 Hat Yai 主校區位於泰國南部，從曼谷飛行約 1 小時 15 分、"
                "距馬來西亞邊境約 60 公里；若錄取的是其他校區，轉機與到校方式要另向院系確認。"
            ),
            "campus_life_summary": (
                "PSU One-Stop Service 協助簽證延長、90 日通報、保險與校內行政；2026 國際生頁另提供"
                "文化禮儀、宋卡生活、緊急聯絡、設施與 Non-ED 簽證導引，入學後仍以錄取院系課表為準。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("PSU International One-Stop Service", "https://gao.psu.ac.th/students/1-stop-service"),
                ("PSU Facilities", "https://reg.psu.ac.th/en/weblink-en/"),
                ("Getting Ready to Study at PSU", "https://gao.psu.ac.th/images/softlanding/Chapter_2.pdf"),
                ("PSU International Student Guide", "https://cmdt-uic.psu.ac.th/international-student/"),
            ],
            "source_summaries": {
                "https://gao.psu.ac.th/students/1-stop-service": (
                    "PSU Global Affairs 官方服務頁整理 Non-ED 簽證、延長、90 日通報、再入境許可、"
                    "保險、國際宿舍預約、校園設施與緊急聯絡窗口。"
                ),
                "https://reg.psu.ac.th/en/weblink-en/": (
                    "PSU 官方設施頁介紹 Hat Yai 校園餐飲、圖書館、醫療、保險與國際宿舍預約；"
                    "其他校區條件不同，須依錄取校區確認。"
                ),
                "https://gao.psu.ac.th/images/softlanding/Chapter_2.pdf": (
                    "PSU 官方抵達指南說明 Hat Yai 與曼谷的距離、機場與到校規劃、辦公時間及抵達前應準備的聯絡資料。"
                ),
                "https://cmdt-uic.psu.ac.th/international-student/": (
                    "PSU International College 2026 國際生頁整理文化適應、宋卡生活、簽證、設施與緊急聯絡資訊。"
                ),
            },
        },
        "national economics university, vietnam": {
            "housing_summary": (
                "NEU 官方校園設施頁確認校內有學生宿舍、餐廳、圖書館與多棟教學大樓；"
                "但未承諾交換生床位，也未公布本梯次房型與費用，提名後須向國際合作窗口確認。"
            ),
            "transport_summary": (
                "主要校址為河內 207 Giai Phong；抵達前要用錄取信上的實際上課大樓與住宿地址規劃路線，"
                "不能只把 NEU 校名當成叫車目的地。"
            ),
            "campus_life_summary": (
                "官方設施頁列出 A2 教學大樓、Phạm Văn Đồng 圖書館、教室 Wi-Fi、餐廳與學生空間；"
                "交換課程、授課語言與點名考核仍須等當期課表。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                ("National Economics University", "https://neu.edu.vn/en/"),
                ("Infrastructure | NEU ISME", "https://isme.neu.edu.vn/en/infrastructure/"),
            ],
            "source_summaries": {
                "https://neu.edu.vn/en/": (
                    "NEU 官方英文網站可核對學校、學術單位與最新校務公告；交換生實際申請仍須依母校提名後通知。"
                ),
                "https://isme.neu.edu.vn/en/infrastructure/": (
                    "NEU 官方學院設施頁介紹 A2 教學大樓、圖書館、校園 Wi-Fi、餐廳、宿舍與學生空間，"
                    "但沒有提供交換生保證床位或當期住宿價格。"
                ),
            },
        },
        "lac hong university, lhu": {
            "housing_summary": (
                "LHU 官方英文網站提供 Student life、Visiting Dong Nai 與 360 校園導覽入口；"
                "交換生宿舍、房型、費用與接送目前未在可讀頁面完整公開，須向國際關係單位索取當期資料。"
            ),
            "transport_summary": (
                "校址在 Đồng Nai 省 Biên Hòa 市 10 Huỳnh Văn Nghệ；抵達胡志明市機場後仍有跨城市移動，"
                "應先向校方確認接送或正式到校路線。"
            ),
            "campus_life_summary": (
                "官方網站列出工程、資訊、藥學、商管、語言等學院及圖書館、學生生活與 360 導覽；"
                "交換可修課表和授課語言需以提名後文件為準。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                ("Lac Hong University Official Website", "https://en.lhu.edu.vn/"),
            ],
            "source_summaries": {
                "https://en.lhu.edu.vn/": (
                    "LHU 官方英文首頁列出校址、學術單位、圖書館、Student life、Visiting Dong Nai 與 360 校園導覽；"
                    "公開頁未完整列交換生住宿與到校流程。"
                ),
            },
        },
        "vietnam national university,hanoi": {
            "housing_summary": (
                "VNU 官方交換頁曾列 4–6 人共用、附衛浴與冷氣的宿舍安排，但頁面中的免費住宿與費用為舊學年資料；"
                "不可當成現在價格或保證床位，須重新索取當期 fact sheet。"
            ),
            "cost_summary": (
                "官方交換頁的生活費與保險金額屬較早期參考，幣值與物價已可能改變；"
                "本頁只保留項目類型，不把舊金額當成目前預算。"
            ),
            "campus_life_summary": (
                "官方交換頁列出母校提名、至少完成兩學期、GPA 2.5/4.0、英文門檻、英文文件、"
                "一學期或一學年交換與分學期申請節點；學生送件前仍要向 VNU 核對當期版本。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Information for Exchange Students | VNU Hanoi",
                    "https://vnu.edu.vn/eng/?C2549/N20206/Information-for-exchange-students-at-Vietnam-National-University%2C-Hanoi.htm=",
                ),
            ],
            "source_summaries": {
                "https://vnu.edu.vn/eng/?C2549/N20206/Information-for-exchange-students-at-Vietnam-National-University%2C-Hanoi.htm=": (
                    "VNU 官方交換頁整理資格、英文門檻、提名信、成績單、護照、健康證明、交換期間與申請節點；"
                    "住宿與費用段落帶有舊學年標示，系統因此不把舊金額當成現況。"
                ),
            },
        },
        "vietnam national university, ho chi minh city": {
            "housing_summary": (
                "IU-VNUHCM 官方來校表單列出 VNU-HCM 校內住宿選項與住宿登記欄位；"
                "文件版本較舊，現行房型、費用與國際生床位須向 International Student Services Center 重新確認。"
            ),
            "transport_summary": (
                "主要校區位於 VNU-HCM 都市區；官方課務公告顯示部分教室、中央圖書館、運動中心與宿舍區分散，"
                "選課後要逐門核對上課地點。"
            ),
            "campus_life_summary": (
                "學校以英文授課為主；官方來校文件包含護照、航班、簽證接收地與住宿資料，"
                "但交換申請時程仍應以臺北大學提名後由 IU 寄出的最新表單為準。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                ("International University VNU-HCMC", "https://hcmiu.edu.vn/en/"),
                (
                    "Incoming Student Registration Form | IU-VNUHCM",
                    "https://hcmiu.edu.vn/wp-content/uploads/2018/03/F-IEX4.pdf",
                ),
            ],
            "source_summaries": {
                "https://hcmiu.edu.vn/en/": (
                    "IU-VNUHCM 官方英文網站可核對學校、學術單位與國際交流窗口。"
                ),
                "https://hcmiu.edu.vn/wp-content/uploads/2018/03/F-IEX4.pdf": (
                    "官方來校交換表單列出護照、航班、簽證接收地與住宿選項；因版本較早，"
                    "僅作流程欄位參考，不把其中住宿條件視為目前承諾。"
                ),
            },
        },
        "vanlang university": {
            "housing_summary": (
                "VLU 官方國際生頁表示會協助尋找校內或校外住宿；未公布保證床位、房型與費用，"
                "錄取後應向 International Student Support Center 取得可入住清單。"
            ),
            "transport_summary": (
                "官方國際生頁提供 Traveling to VLU 與校園資訊入口；VLU 有不同校區，"
                "應先以課表與住宿地址確認實際通勤，不只搜尋學校總名。"
            ),
            "campus_life_summary": (
                "交換可為一至兩學期，VLU 提供 Orientation Week、Buddy、選課、簽證與行政協助；"
                "官方迎新內容也列出多個可修領域，最終課程以當期清單為準。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "Student Exchange Opportunities | Van Lang University",
                    "https://www.vlu.edu.vn/en/admissions/student-exchange-opportunities",
                ),
                (
                    "International Students | Van Lang University",
                    "https://www.vlu.edu.vn/en/life-at-vlu/international-student",
                ),
            ],
            "source_summaries": {
                "https://www.vlu.edu.vn/en/admissions/student-exchange-opportunities": (
                    "VLU 官方交換頁說明一學期／一學年交換、短期課程、學分、語言、住宿與學生支援入口。"
                ),
                "https://www.vlu.edu.vn/en/life-at-vlu/international-student": (
                    "官方國際生頁整理 Orientation、到校交通、住宿協助、課程與國際學生服務窗口。"
                ),
            },
        },
        "university of economics and law": {
            "housing_summary": (
                "UEL 官方英文網站可核對校址、校園生活與學術單位，但未公開交換生保證住宿、房型或費用；"
                "申請前須向 UEL Global／國際合作窗口確認。"
            ),
            "transport_summary": (
                "校址位於胡志明市 Linh Xuân；官方網站提供校園地圖與 360 導覽入口，"
                "到校前應依實際住宿地址比較公車、捷運接駁或合規叫車。"
            ),
            "campus_life_summary": (
                "UEL 結合經濟、商管、法律與科技領域，官方頁列出各學院、圖書館與學生服務；"
                "交換可修課程、英文授課比例與考核方式需等當期課表。"
            ),
            "coverage_status": "official_partial",
            "sources": [
                ("University of Economics and Law", "https://www.uel.edu.vn/en"),
            ],
            "source_summaries": {
                "https://www.uel.edu.vn/en": (
                    "UEL 官方英文首頁列出經濟、商管、法律與科技相關學院、圖書館、校園生活、地圖、"
                    "360 導覽及國際單位入口；公開頁未列本梯次交換生住宿和課表。"
                ),
            },
        },
        "university of economics ho chi minh city-international school of business": {
            "housing_summary": (
                "UEH-ISB 交換生部門會提供經查核、鄰近校區且重視安全與隱私的住宿清單；"
                "學生自行找房時也可請學校協助檢查，但頁面未公布固定房租或保證床位。"
            ),
            "transport_summary": (
                "官方頁提醒胡志明市交通壅塞，列出公車、合規叫車、單車與步行等選項；"
                "應以 17 Pham Ngoc Thach 校址和實際住宿重新估算尖峰通勤。"
            ),
            "campus_life_summary": (
                "交換生每年可來校一至兩學期，英文非母語者門檻為 IELTS 5.5、單科不低於 5.0 或同等證明；"
                "英語授課科目可依學期選修，官方頁另列最低選課數、學分換算與生活清單。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                (
                    "International Students | UEH-ISB",
                    "https://international.isb.edu.vn/transfer-programs/international-students/",
                ),
            ],
            "source_summaries": {
                "https://international.isb.edu.vn/transfer-programs/international-students/": (
                    "UEH-ISB 官方交換頁說明母校提名、完成一年學業、IELTS 5.5、英語課程、最低選課數、"
                    "住宿協助、胡志明市交通、行李清單與交換生聯絡窗口。"
                ),
            },
        },
        "vietnamese-german university": {
            "housing_summary": (
                "VGU 國際處提供來校學生的抵達前後指引，但公開頁未列本梯次交換生宿舍房型與價格；"
                "應直接向 incomings@vgu.edu.vn 確認住宿、校車與入住日期。"
            ),
            "transport_summary": (
                "VGU 校園位於 Bình Dương；不要把胡志明市中心當成步行可達校區，"
                "訂房或買票前先向國際處確認校車、接送與正確校門地址。"
            ),
            "campus_life_summary": (
                "國際處負責 incoming／outgoing、抵達前後指引、交換與實習、簽證支援及跨文化活動；"
                "來校交換與簽證問題可直接聯絡 incomings 專責窗口。"
            ),
            "coverage_status": "official_verified",
            "sources": [
                ("International Office | Vietnamese-German University", "https://vgu.edu.vn/international-office"),
            ],
            "source_summaries": {
                "https://vgu.edu.vn/international-office": (
                    "VGU 官方國際處頁列出 incoming／outgoing、抵達前後指引、交換、實習、"
                    "簽證支援、跨文化活動與 incoming 專責聯絡方式。"
                ),
            },
        },
    }
)

for alias, canonical in {
    "king mongkut's institute of technology ladkrabang kmitl": "king mongkut's institue of technology ladkrabang",
    "thammasat university thailand": "thammasat university",
    "king mongkut's university of technology thonburi kmutt": "king mongkut's university of technology thonburi (kmutt",
    "prince of songkla university psu": "prince of songkla university (psu",
}.items():
    CURATED_DESTINATION_DETAILS[alias] = CURATED_DESTINATION_DETAILS[canonical]


def research_school_name(value: str) -> str:
    name = value.strip(" ()（）,，")
    name = re.sub(r"\)?\s*無\s*$", "", name).strip(" ()")
    name = re.sub(r"\s*黑龍江省哈爾\s*濱市\s*$", "", name).strip()
    name = re.sub(r"\s+", " ", name)
    name = school_search_name(name).strip(" ()（）,，")
    name = re.sub(
        r"\s+(?:For|FOR)\s+(?:SPACE|SE-|Program|Programme).*$",
        "",
        name,
    )
    return name[:180]


def _curated_destination_details(partner: PartnerUniversity) -> dict | None:
    keys = (
        research_school_name(partner.school_name).casefold(),
        partner.school_name.strip().casefold(),
        school_identity_key(partner.school_name).casefold(),
    )
    for key in keys:
        if details := CURATED_DESTINATION_DETAILS.get(key):
            return details
    return None


def _ascii_words(value: str) -> list[str]:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return [
        word
        for word in re.findall(r"[a-z0-9]{3,}", ascii_value.casefold())
        if word not in GENERIC_NAME_WORDS
    ]


def _blocked_host(host: str) -> bool:
    normalized = host.casefold().removeprefix("www.")
    return any(
        normalized == blocked or normalized.endswith(f".{blocked}")
        for blocked in BLOCKED_DISCOVERY_HOSTS
    )


def _candidate_score(
    partner: PartnerUniversity,
    *,
    title: str,
    url: str,
    body: str,
) -> int:
    parsed = urlparse(url)
    host = parsed.netloc.casefold().removeprefix("www.")
    if not host or _blocked_host(host):
        return -100
    identity = f"{title} {body}".casefold()
    words = _ascii_words(school_search_name(research_school_name(partner.school_name)))
    if not words:
        return -100
    matched = [word for word in words if word in identity]
    if len(matched) < min(2, len(words)):
        return -100
    score = len(matched) * 2
    if any(word in host for word in words):
        score += 8
    if any(marker in host for marker in ACADEMIC_DOMAIN_MARKERS):
        score += 4
    if re.search(r"official|incoming|exchange|international", identity):
        score += 2
    if re.search(r"partner|fact sheet|study abroad office", identity):
        score -= 2
    if parsed.path.casefold().endswith((".pdf", ".doc", ".docx")):
        score -= 1
    return score


def _search_candidates(
    partner: PartnerUniversity,
    *,
    max_results: int,
    timeout_seconds: float,
) -> list[tuple[int, str, str, str]]:
    name = school_search_name(research_school_name(partner.school_name))
    country = COUNTRY_SEARCH_NAMES.get(partner.country or "", partner.country or "")
    queries = (
        f"{name} {country} official university website",
        f"{name} incoming exchange international official",
    )
    rows: list[tuple[int, str, str, str]] = []
    for query in queries:
        results = search_text(
            query,
            max_results=max(4, min(10, max_results)),
            timeout_seconds=timeout_seconds,
        )
        for item in results:
            url = str(item.get("href") or item.get("url") or "").strip()
            title = str(item.get("title") or "").strip()
            body = str(item.get("body") or item.get("description") or "").strip()
            if not url.startswith(("http://", "https://")):
                continue
            score = _candidate_score(partner, title=title, url=url, body=body)
            if score > 0:
                rows.append((score, title[:240], url, body[:1000]))
    deduped: dict[str, tuple[int, str, str, str]] = {}
    for row in rows:
        host = urlparse(row[2]).netloc.casefold().removeprefix("www.")
        if host not in deduped or row[0] > deduped[host][0]:
            deduped[host] = row
    return sorted(deduped.values(), key=lambda row: (-row[0], len(row[2])))


def _wikidata_name(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.casefold()).strip()


def _wikidata_search_names(value: str) -> list[str]:
    names = [value]
    root = re.split(
        r"\b(?:college|department|faculty|graduate school|school of)\b",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip(" ,-/")
    if len(root) >= 4 and _wikidata_name(root) != _wikidata_name(value):
        names.append(root)
    return names


def _wikidata_candidate_score(query: str, label: str, description: str) -> float:
    normalized_query = _wikidata_name(query)
    normalized_label = _wikidata_name(label)
    if not normalized_query or not normalized_label:
        return 0.0
    description_key = _wikidata_name(description)
    if not re.search(r"\b(university|college|school|institute|academy)\b", description_key):
        return 0.0
    query_tokens = set(normalized_query.split())
    label_tokens = set(normalized_label.split())
    overlap = len(query_tokens & label_tokens) / max(1, len(query_tokens | label_tokens))
    ratio = SequenceMatcher(None, normalized_query, normalized_label).ratio()
    exact_bonus = 0.22 if normalized_query == normalized_label else 0.0
    return ratio * 0.62 + overlap * 0.38 + exact_bonus


def _wikidata_official_site(
    partner: PartnerUniversity,
    *,
    timeout_seconds: float,
) -> tuple[str, str, str, float] | None:
    """Resolve an institution's official website from an exact Wikidata entity match.

    Search-engine results can confuse similarly named institutions (for example,
    Shandong University and Shandong University of Science and Technology).
    Wikidata's institution label plus P856 official-website property gives us a
    safer canonical-domain fallback before general web search.
    """

    endpoint = "https://www.wikidata.org/w/api.php"
    headers = {
        "User-Agent": "taiwan-exchange-info/0.1 (public university metadata reader)",
        "Accept-Language": "en,zh-TW;q=0.8",
    }
    research_name = research_school_name(partner.school_name)
    candidates: dict[str, tuple[float, str]] = {}
    try:
        for query in _wikidata_search_names(research_name):
            response = requests.get(
                endpoint,
                params={
                    "action": "wbsearchentities",
                    "search": query,
                    "language": "en",
                    "format": "json",
                    "limit": 6,
                    "origin": "*",
                },
                headers=headers,
                timeout=timeout_seconds,
            )
            response.raise_for_status()
            for item in response.json().get("search", []):
                entity_id = str(item.get("id") or "")
                label = str(item.get("label") or "")
                score = _wikidata_candidate_score(
                    query,
                    label,
                    str(item.get("description") or ""),
                )
                if entity_id and score >= 0.56 and score > candidates.get(entity_id, (0.0, ""))[0]:
                    candidates[entity_id] = (score, label)
        if not candidates:
            return None
        entity_ids = sorted(candidates, key=lambda item: candidates[item][0], reverse=True)[:6]
        response = requests.get(
            endpoint,
            params={
                "action": "wbgetentities",
                "ids": "|".join(entity_ids),
                "props": "claims",
                "format": "json",
                "origin": "*",
            },
            headers=headers,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        entities = response.json().get("entities", {})
    except (requests.RequestException, ValueError, TypeError):
        return None

    for entity_id in entity_ids:
        claims = entities.get(entity_id, {}).get("claims", {})
        websites = claims.get("P856", [])
        for statement in websites:
            if statement.get("rank") == "deprecated":
                continue
            value = (
                statement.get("mainsnak", {})
                .get("datavalue", {})
                .get("value")
            )
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                score, label = candidates[entity_id]
                return value, label, entity_id, score
    return None


THE_WORLD_RANKING_URL = (
    "https://www.timeshighereducation.com/world-university-rankings/"
    "latest/world-ranking"
)

THE_RANKING_NAME_ALIASES = {
    "university of california davis": "University of California, Davis",
    "uc davis": "University of California, Davis",
    "uc davis the regents of the university of california on the behalf of the davis campus": "University of California, Davis",
    "university of california irvine": "University of California, Irvine",
    "uc i": "University of California, Irvine",
    "uc i university of california irvine uci": "University of California, Irvine",
    "king mongkut s institute of technology ladkrabang kmitl": "KMITL - King Mongkut's Institute of Technology Ladkrabang",
    "king mongkut s university of technology thonburi kmutt": "King Mongkut's University of Technology Thonburi",
    "thammasat university thailand": "Thammasat University",
    "prince of songkla university psu": "Prince of Songkla University",
    "kyungpook national university": "Kyungpook National University (KNU)",
    "xi an jiaotong university": "Xi'an Jiaotong University",
    "leopold franzens university of innsbruck": "University of Innsbruck",
    "universite de lille": "University of Lille",
    "college of liberal arts and social sciences city university of hong kong": "City University of Hong Kong",
    "osaka university school of law graduate school of law and politics osaka school of international public policy": "The University of Osaka",
    "the university of electro communications uec": "The University of Electro-Communications",
    "university of munster": "University of Munster",
    "fh munster munster school of business": "Munster University of Applied Sciences",
    "sciences po aix": "Sciences Po Aix",
    "sciences po toulouse": "Sciences Po Toulouse",
    "universiti tunku abdul rahman": "Universiti Tunku Abdul Rahman (UTAR)",
}

THE_RANKING_STOP_WORDS = {
    "and",
    "at",
    "campus",
    "college",
    "faculty",
    "for",
    "in",
    "institute",
    "institue",
    "international",
    "national",
    "of",
    "school",
    "the",
    "university",
}


def _normalise_ranking_name(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value or "")
    ascii_value = folded.encode("ascii", "ignore").decode("ascii").casefold()
    return " ".join(re.findall(r"[a-z0-9]+", ascii_value))


def _ranking_name_score(query: str, candidate: str) -> tuple[float, float]:
    query_name = _normalise_ranking_name(query)
    candidate_name = _normalise_ranking_name(candidate)
    if not query_name or not candidate_name:
        return 0.0, 0.0
    if query_name == candidate_name:
        return 1.0, 1.0

    query_tokens = set(query_name.split()) - THE_RANKING_STOP_WORDS
    candidate_tokens = set(candidate_name.split()) - THE_RANKING_STOP_WORDS
    overlap = query_tokens & candidate_tokens
    coverage = len(overlap) / max(1, len(query_tokens))
    jaccard = len(overlap) / max(1, len(query_tokens | candidate_tokens))
    containment = float(query_name in candidate_name or candidate_name in query_name)
    similarity = SequenceMatcher(None, query_name, candidate_name).ratio()
    score = 0.48 * similarity + 0.38 * jaccard + 0.14 * containment
    return score, coverage


@lru_cache(maxsize=2)
def _the_world_ranking_rows(timeout_seconds: float = 20.0) -> tuple[dict, ...]:
    """Load the current THE table once; it contains rank, name and profile URL."""

    from bs4 import BeautifulSoup

    response = requests.get(
        f"{THE_WORLD_RANKING_URL}?embed=true",
        headers={"User-Agent": "Mozilla/5.0 ExchangeInfoMVP/0.1"},
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    next_data = BeautifulSoup(response.text, "html.parser").find(
        "script", id="__NEXT_DATA__"
    )
    if not next_data or not next_data.string:
        raise ValueError("THE ranking table did not expose its structured data")
    payload = json.loads(next_data.string)
    rows = (
        payload.get("props", {})
        .get("pageProps", {})
        .get("page", {})
        .get("rankingsTableConfig", {})
        .get("rankingsData", {})
        .get("data", [])
    )
    return tuple(row for row in rows if isinstance(row, dict) and row.get("name"))


def _match_the_world_ranking(
    partner: PartnerUniversity,
    record: PartnerResearchRecord,
    rows: tuple[dict, ...],
) -> dict | None:
    search_name = record.research_name or research_school_name(partner.school_name)
    normalised = _normalise_ranking_name(search_name)
    alias = THE_RANKING_NAME_ALIASES.get(normalised)
    queries = [value for value in (alias, search_name) if value]

    ranked: list[tuple[float, float, dict]] = []
    for row in rows:
        best_score = 0.0
        best_coverage = 0.0
        candidates = [str(row.get("name") or "")]
        aliases = row.get("aliases")
        if isinstance(aliases, str):
            candidates.extend(part.strip() for part in aliases.split("|") if part.strip())
        for query in queries:
            for candidate in candidates:
                score, coverage = _ranking_name_score(query, candidate)
                if score > best_score:
                    best_score, best_coverage = score, coverage
        ranked.append((best_score, best_coverage, row))

    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked:
        return None
    score, coverage, row = ranked[0]
    runner_up = ranked[1][0] if len(ranked) > 1 else 0.0
    if score == 1.0:
        return row
    if score >= 0.78 and coverage >= 0.75 and score - runner_up >= 0.04:
        return row
    return None


def enrich_partner_ranking(
    partner: PartnerUniversity,
    record: PartnerResearchRecord,
    *,
    timeout_seconds: float = 15.0,
) -> PartnerResearchRecord:
    """Attach one comparable, source-linked ranking status to a partner record.

    THE is used consistently across schools. If a school has no THE profile or
    is not ranked in the current table, the record says so explicitly instead
    of inventing a number or mixing incompatible ranking systems.
    """

    checked_at = datetime.now(timezone.utc)
    general_ranking_url = THE_WORLD_RANKING_URL
    table_loaded = False
    try:
        table_rows = _the_world_ranking_rows(min(30.0, timeout_seconds + 10.0))
        table_loaded = True
        table_match = _match_the_world_ranking(partner, record, table_rows)
    except (requests.RequestException, ValueError, TypeError, json.JSONDecodeError):
        table_match = None

    if table_match is not None:
        rank = str(table_match.get("rank") or "").strip()
        profile_path = str(table_match.get("url") or "").strip()
        ranking_url = (
            f"https://www.timeshighereducation.com{profile_path}"
            if profile_path.startswith("/")
            else general_ranking_url
        )
        ranking_text = (
            "Reporter（參與評比但未獲排名區間）"
            if rank.casefold() == "reporter"
            else rank
        )
        return record.model_copy(
            update={
                "research_name": record.research_name
                or research_school_name(partner.school_name),
                "ranking_info": f"THE 世界大學排名 2026：{ranking_text}",
                "ranking_source_url": ranking_url,
                "ranking_checked_at": checked_at,
            }
        )

    if table_loaded:
        return record.model_copy(
            update={
                "research_name": record.research_name
                or research_school_name(partner.school_name),
                "ranking_info": (
                    "THE 世界大學排名 2026：未在完整排名表中找到可可靠對應的校名；"
                    "不代表未被其他榜單收錄。"
                ),
                "ranking_source_url": general_ranking_url,
                "ranking_checked_at": checked_at,
            }
        )

    wikidata_url = record.wikidata_url
    if not wikidata_url:
        metadata = _wikidata_official_site(
            partner,
            timeout_seconds=min(12.0, timeout_seconds),
        )
        if metadata and metadata[3] >= 0.82:
            _, _, entity_id, _ = metadata
            wikidata_url = f"https://www.wikidata.org/wiki/{entity_id}"

    if not wikidata_url or not re.search(r"/Q\d+$", wikidata_url):
        return record.model_copy(
            update={
                "research_name": record.research_name or research_school_name(partner.school_name),
                "ranking_info": (
                    "THE 世界大學排名 2026：未查得可可靠對應的學校排名頁；"
                    "不代表未被其他榜單收錄。"
                ),
                "ranking_source_url": general_ranking_url,
                "ranking_checked_at": checked_at,
            }
        )

    entity_id = wikidata_url.rsplit("/", 1)[-1]
    endpoint = "https://www.wikidata.org/w/api.php"
    headers = {
        "User-Agent": "taiwan-exchange-info/0.1 (public university ranking metadata reader)",
        "Accept-Language": "en,zh-TW;q=0.8",
    }
    try:
        response = requests.get(
            endpoint,
            params={
                "action": "wbgetentities",
                "ids": entity_id,
                "props": "claims",
                "format": "json",
                "origin": "*",
            },
            headers=headers,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        claims = response.json().get("entities", {}).get(entity_id, {}).get("claims", {})
        the_ids = claims.get("P5586", [])
        the_slug = next(
            (
                statement.get("mainsnak", {}).get("datavalue", {}).get("value")
                for statement in the_ids
                if statement.get("rank") != "deprecated"
            ),
            None,
        )
    except (requests.RequestException, ValueError, TypeError):
        the_slug = None

    if not isinstance(the_slug, str) or not the_slug.strip():
        return record.model_copy(
            update={
                "research_name": record.research_name or research_school_name(partner.school_name),
                "wikidata_url": wikidata_url,
                "ranking_info": (
                    "THE 世界大學排名 2026：未查得該校綜合排名頁；"
                    "不代表未被其他榜單收錄。"
                ),
                "ranking_source_url": general_ranking_url,
                "ranking_checked_at": checked_at,
            }
        )

    ranking_url = (
        "https://www.timeshighereducation.com/world-university-rankings/"
        f"{the_slug.strip()}"
    )
    rank = None
    year = 2026
    try:
        from bs4 import BeautifulSoup

        response = requests.get(
            ranking_url,
            headers={"User-Agent": "Mozilla/5.0 ExchangeInfoMVP/0.1"},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        next_data = BeautifulSoup(response.text, "html.parser").find(
            "script", id="__NEXT_DATA__"
        )
        if next_data and next_data.string:
            payload = json.loads(next_data.string)
            rank_payload = (
                payload.get("props", {})
                .get("pageProps", {})
                .get("headerProps", {})
                .get("wurRankGRA", {})
            )
            rank = str(rank_payload.get("rank") or "").strip() or None
            year = int(rank_payload.get("year") or year)
    except (requests.RequestException, ValueError, TypeError, json.JSONDecodeError):
        rank = None

    ranking_info = (
        f"THE 世界大學排名 {year}：{rank}"
        if rank
        else (
            "THE 世界大學排名 2026：學校頁未顯示當年度綜合排名；"
            "不代表未被其他榜單收錄。"
        )
    )
    return record.model_copy(
        update={
            "research_name": record.research_name or research_school_name(partner.school_name),
            "wikidata_url": wikidata_url,
            "ranking_info": ranking_info,
            "ranking_source_url": ranking_url,
            "ranking_checked_at": checked_at,
        }
    )


def discover_partner_official_site(
    partner: PartnerUniversity,
    *,
    home_university: str,
    max_results: int = 8,
    timeout_seconds: float = 15.0,
) -> PartnerResearchRecord:
    checked_at = datetime.now(timezone.utc)
    canonical_name = research_school_name(partner.school_name)
    verified = VERIFIED_OFFICIAL_SITES.get(canonical_name.casefold()) or next(
        (
            value
            for local_name, value in VERIFIED_OFFICIAL_SITES.items()
            if partner.school_name.casefold().startswith(local_name.casefold())
        ),
        None,
    )
    if verified:
        url, title = verified
        parsed = urlparse(url)
        return PartnerResearchRecord(
            home_university=home_university,
            school_name=partner.school_name,
            country=partner.country,
            research_name=canonical_name,
            official_website=url,
            official_domain=parsed.netloc.casefold().removeprefix("www."),
            verification_status="official_verified",
            candidate_title=title,
            discovery_source_url=url,
            checked_at=checked_at,
            note="首批開發查核已核對合作校官方主網域；後續重新整理沿用已確認入口。",
        )
    if partner.website:
        parsed = urlparse(partner.website if "://" in partner.website else f"https://{partner.website}")
        return PartnerResearchRecord(
            home_university=home_university,
            school_name=partner.school_name,
            country=partner.country,
            research_name=canonical_name,
            official_website=parsed.geturl(),
            official_domain=parsed.netloc.casefold().removeprefix("www."),
            verification_status="official_verified",
            candidate_title=f"{partner.school_name} official website",
            discovery_source_url=partner.website,
            checked_at=checked_at,
            note="合作校名額資料已提供官方網站。",
        )
    wikidata = _wikidata_official_site(
        partner,
        timeout_seconds=min(12.0, timeout_seconds),
    )
    if wikidata:
        url, label, entity_id, score = wikidata
        parsed = urlparse(url)
        return PartnerResearchRecord(
            home_university=home_university,
            school_name=partner.school_name,
            country=partner.country,
            research_name=canonical_name,
            official_website=url,
            official_domain=parsed.netloc.casefold().removeprefix("www."),
            wikidata_url=f"https://www.wikidata.org/wiki/{entity_id}",
            verification_status="official_verified" if score >= 0.82 else "needs_review",
            candidate_title=f"{label} official website",
            discovery_source_url=f"https://www.wikidata.org/wiki/{entity_id}",
            checked_at=checked_at,
            note=(
                f"Wikidata 機構名稱比對分數 {score:.2f}，官方網站取自 P856；"
                "低於高信心門檻的結果保留人工複核狀態。"
            ),
        )
    try:
        candidates = _search_candidates(
            partner,
            max_results=max_results,
            timeout_seconds=timeout_seconds,
        )
    except Exception as exc:
        return PartnerResearchRecord(
            home_university=home_university,
            school_name=partner.school_name,
            country=partner.country,
            research_name=canonical_name,
            verification_status="error",
            checked_at=checked_at,
            note=str(exc)[:500],
        )
    if not candidates:
        return PartnerResearchRecord(
            home_university=home_university,
            school_name=partner.school_name,
            country=partner.country,
            research_name=canonical_name,
            verification_status="not_found",
            checked_at=checked_at,
            note="公開搜尋未找到可可靠對應的合作校官方網域。",
        )
    score, title, url, _ = candidates[0]
    parsed = urlparse(url)
    status = "official_verified" if score >= 12 else "needs_review"
    return PartnerResearchRecord(
        home_university=home_university,
        school_name=partner.school_name,
        country=partner.country,
        research_name=canonical_name,
        official_website=url,
        official_domain=parsed.netloc.casefold().removeprefix("www."),
        verification_status=status,
        candidate_title=title,
        discovery_source_url=url,
        checked_at=checked_at,
        note=f"官方網域自動比對分數 {score}；低信心結果會保留人工複核狀態。",
    )


def apply_partner_research(
    partners: list[PartnerUniversity],
    records: list[PartnerResearchRecord],
    *,
    home_university: str,
) -> list[PartnerUniversity]:
    record_map = {
        school_identity_key(record.school_name): record
        for record in records
        if school_identity_key(record.home_university) == school_identity_key(home_university)
        and record.official_website
        and record.verification_status in {"official_verified", "needs_review"}
    }
    return [
        partner.model_copy(
            deep=True,
            update={
                "website": record_map[school_identity_key(partner.school_name)].official_website,
                "ranking_info": record_map[school_identity_key(partner.school_name)].ranking_info,
                "ranking_source_url": record_map[school_identity_key(partner.school_name)].ranking_source_url,
            },
        )
        if school_identity_key(partner.school_name) in record_map
        else partner.model_copy(deep=True)
        for partner in partners
    ]


def _official_information_pages(
    partner: PartnerUniversity,
    *,
    max_pages: int,
    timeout_seconds: float,
) -> list[tuple[str, str]]:
    if not partner.website:
        return []
    from .application_workflow_collector import official_host

    host = official_host(partner.website)
    if not host:
        return []
    name = school_search_name(research_school_name(partner.school_name))
    queries = (
        f"{name} {host} international student accommodation housing",
        f"{name} {host} living costs transport campus life international students",
    )
    curated = _curated_destination_details(partner)
    rows: list[tuple[str, str]] = list(curated.get("sources", [])) if curated else []
    if rows:
        return rows[:max_pages]
    for query in queries:
        results = search_text(
            query,
            max_results=max(3, max_pages),
            timeout_seconds=timeout_seconds,
        )
        for item in results:
            url = str(item.get("href") or item.get("url") or "")
            title = str(item.get("title") or partner.school_name)
            if url and urlparse(url).netloc:
                rows.append((title[:220], url))
    unique: list[tuple[str, str]] = []
    seen: set[str] = set()
    for title, url in rows:
        if url in seen:
            continue
        seen.add(url)
        unique.append((title, url))
        if len(unique) >= max_pages:
            break
    return unique


def _signal_excerpt(text: str, pattern: str, fallback: str) -> str | None:
    compact = re.sub(r"\s+", " ", text)
    match = re.search(pattern, compact, re.IGNORECASE)
    if not match:
        return None
    start = max(0, match.start() - 90)
    end = min(len(compact), match.end() + 180)
    excerpt = compact[start:end].strip(" .;|-")
    return excerpt[:360] or fallback


def _join_student_points(rows: list[str], *, limit: int = 4) -> str | None:
    values: list[str] = []
    seen: set[str] = set()
    for value in rows:
        compact = re.sub(r"\s+", " ", str(value or "")).strip(" ；。")
        key = re.sub(r"\W+", "", compact).casefold()
        if len(compact) < 10 or not key or key in seen:
            continue
        seen.add(key)
        values.append(compact)
        if len(values) >= limit:
            break
    return "；".join(values) + "。" if values else None


def _official_page_fallback_summary(text: str) -> str | None:
    sentences = [
        re.sub(r"\s+", " ", row).strip(" -|•")
        for row in re.split(r"(?<=[。！？.!?])\s+|\n+", text)
    ]
    useful = [row for row in sentences if 30 <= len(row) <= 260]
    return " ".join(useful[:2])[:360] or None


def _apply_curated_destination_details(
    partner: PartnerUniversity,
    profile: DestinationProfile,
) -> DestinationProfile:
    details = _curated_destination_details(partner)
    if not details:
        return apply_shared_student_survival_guide(profile)

    def fallback_source_summary(title: str, url: str) -> str | None:
        guide_rows = [
            *details.get("student_guide_sections", []),
            *details.get("first_72_hours", []),
            *details.get("packing_from_taiwan", []),
            *details.get("buy_after_arrival", []),
        ]
        for row in guide_rows:
            if url in row.get("source_urls", []):
                value = row.get("summary") or row.get("detail")
                if value:
                    return f"這個來源支持的學生重點：{value}"[:700]
        normalized_title = title.casefold()
        if any(word in normalized_title for word in ("housing", "accommodation", "dorm")):
            preferred = ("housing_summary", "cost_summary", "campus_life_summary")
        elif any(word in normalized_title for word in ("cost", "fee", "tuition")):
            preferred = ("cost_summary", "housing_summary", "campus_life_summary")
        else:
            preferred = (
                "campus_life_summary",
                "housing_summary",
                "cost_summary",
                "transport_summary",
            )
        for field in preferred:
            if value := details.get(field):
                return f"此官方來源的學生重點：{value}"[:700]
        return None

    sources = {source.source_url: source for source in profile.sources}
    for title, url in details["sources"]:
        existing = sources.get(url)
        curated_summary = (
            details.get("source_summaries", {}).get(url)
            or fallback_source_summary(title, url)
        )
        sources[url] = (
            existing.model_copy(
                update={
                    "title": title,
                    "summary": curated_summary or existing.summary,
                }
            )
            if existing
            else SourceReference(
                title=title,
                source_url=url,
                category=PageCategory.PARTNER_SCHOOL,
                summary=curated_summary,
            )
        )
    update = {
        field: details[field]
        for field in (
            "city",
            "cost_summary",
            "housing_summary",
            "transport_summary",
            "campus_life_summary",
        )
        if field in details
    }
    if "guide_photos" in details:
        update["guide_photos"] = [
            StudentGuidePhoto.model_validate(row) for row in details["guide_photos"]
        ]
    if "student_guide_sections" in details:
        update["student_guide_sections"] = [
            StudentGuideSection.model_validate(row)
            for row in details["student_guide_sections"]
        ]
    for field in ("first_72_hours", "packing_from_taiwan", "buy_after_arrival"):
        if field in details:
            update[field] = [
                StudentGuideChecklistItem.model_validate(row)
                for row in details[field]
            ]
    update.update(
        sources=list(sources.values()),
        coverage_status=details["coverage_status"],
        coverage_note=details.get("coverage_note")
        or (
            f"已實際讀取並摘要 {sum(bool(source.summary) for source in sources.values())} 個官方生活資訊頁；"
            "未公開的費用或交通細節維持待查，不以一般網路介紹補造。"
        ),
    )
    return apply_shared_student_survival_guide(profile.model_copy(update=update))


def collect_destination_profile(
    partner: PartnerUniversity,
    *,
    max_pages: int = 6,
    timeout_seconds: float = 20.0,
) -> DestinationProfile:
    checked_at = datetime.now(timezone.utc)
    if not partner.website:
        return DestinationProfile(
            school_name=partner.school_name,
            country=partner.country,
            last_checked=checked_at,
            coverage_status="not_found",
            coverage_note="尚未確認合作校官方網站，無法進行官方生活資訊查核。",
        )
    from .application_workflow_collector import (
        fetch_official_page_text,
        is_official_partner_url,
    )

    pages = _official_information_pages(
        partner,
        max_pages=max_pages,
        timeout_seconds=timeout_seconds,
    )
    source_rows: list[SourceReference] = []
    texts: list[str] = []
    life_points: dict[str, list[str]] = {
        "housing_points": [],
        "cost_points": [],
        "transport_points": [],
        "campus_life_points": [],
    }
    for title, url in pages:
        if not is_official_partner_url(url, partner.website):
            continue
        text = fetch_official_page_text(
            url,
            partner.website,
            timeout_seconds=timeout_seconds,
        )
        if not text:
            continue
        texts.append(text)
        payload = summarize_official_life_link(
            title=title,
            source_url=url,
            page_text=text,
            timeout_seconds=max(25.0, min(timeout_seconds + 25.0, 55.0)),
        )
        source_summary = None
        if payload:
            source_summary = re.sub(
                r"\s+", " ", str(payload.get("summary_zh") or "")
            ).strip()[:360] or None
            for field in life_points:
                values = payload.get(field, [])
                if isinstance(values, list):
                    life_points[field].extend(str(value) for value in values)
        if not source_summary:
            source_summary = _official_page_fallback_summary(text)
        if not source_summary:
            source_summary = (
                f"此合作校官方頁為「{title}」資訊入口；可讀內容主要是頁面導覽，"
                "未列出足以獨立摘要的住宿、交通或課業細節，請開啟原頁查閱最新子頁。"
            )
        source_rows.append(
            SourceReference(
                title=title,
                source_url=url,
                category=PageCategory.PARTNER_SCHOOL,
                summary=source_summary,
            )
        )
    combined = "\n".join(texts)
    housing = _join_student_points(life_points["housing_points"]) or _signal_excerpt(
        combined,
        r"accommodation|housing|residence hall|dormitory|student residence|宿舍|住宿",
        "官方住宿資訊已找到。",
    )
    cost = _join_student_points(life_points["cost_points"]) or _signal_excerpt(
        combined,
        r"living costs?|cost of living|monthly budget|tuition and fees|生活費|費用|預算",
        "官方生活費資訊已找到。",
    )
    transport = _join_student_points(life_points["transport_points"]) or _signal_excerpt(
        combined,
        r"public transport|transportation|metro|subway|train station|bus route|交通|地鐵|公車",
        "官方交通資訊已找到。",
    )
    campus = _join_student_points(life_points["campus_life_points"]) or _signal_excerpt(
        combined,
        r"orientation|student clubs?|campus life|international student support|student services|校園生活|國際學生",
        "官方校園生活資訊已找到。",
    )
    signals = [housing, cost, transport, campus]
    signal_count = sum(value is not None for value in signals)
    if signal_count >= 2 and len(source_rows) >= 2:
        status = "official_verified"
    elif source_rows:
        status = "official_partial"
    else:
        status = "not_found"
    profile = DestinationProfile(
        school_name=partner.school_name,
        country=partner.country,
        cost_summary=cost,
        housing_summary=housing,
        transport_summary=transport,
        campus_life_summary=campus,
        sources=source_rows,
        last_checked=checked_at,
        coverage_status=status,
        coverage_note=(
            f"已實際讀取並摘要 {len(source_rows)} 個合作校官方生活資訊頁，整理 {signal_count} 個生活面向。"
            if source_rows
            else "已搜尋合作校官方網域，但未找到可可靠讀取的生活資訊頁。"
        ),
    )
    return _apply_curated_destination_details(partner, profile)

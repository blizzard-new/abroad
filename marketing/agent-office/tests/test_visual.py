"""One visual designer makes every picture: she reads the boss's brief and the request, and her design is what gets drawn."""

import json
import os
import threading
from datetime import date, time

import pytest

from fake_cli import install
from office import brains, visual
from office.brand import MASCOT, VISUAL_BRIEF, BrandFacts, Briefing
from office.config import Settings
from office.models import CarouselDraft, PlanItem, Slide, ThreadsDraft, VisualPlan, VisualSlide, VisualSpec
from office.office import Office, desk_of
from office.render.renderer import Renderer
from test_render import chromium_available

needs_chromium = pytest.mark.skipif(not chromium_available(), reason="needs Chromium")
FACTS = BrandFacts(university_count=33, partner_count=5730, universities=(), site_url="https://app.uniway-tw.com", source="test")

SLIDES = [
    Slide(kind="cover", title="交換一學期要準備多少錢？先抓這三筆", body="4 個重點，申請前先收藏"),
    Slide(kind="point", title="出發前先抓機票與保險", body="機票看淡旺季，越早訂越便宜；保險要含海外醫療；簽證費依國家另計"),
    Slide(kind="point", title="托福與雅思怎麼選", body="托福較多學校接受；雅思考場多、日期彈性大"),
    Slide(kind="point", title="生活費大約多少", body="歐洲城市每月 3 萬元起跳，先用這個數字抓預算"),
    Slide(kind="cta", title="收藏起來慢慢看", body="UniWay 交換預算用同一幣別估算總成本｜連結在主頁"),
]


def designed() -> VisualPlan:
    return VisualPlan(
        outline=["總預算", "機票與保險", "語言檢定", "生活費", "收藏"],
        spec=VisualSpec(margin=64, title_size=80, body_size=40, line_height=1.55, accent="teal", emphasis="chip", page_number="foot"),
        slides=[
            VisualSlide(layout="cover", title_lines=["交換一學期要準備多少錢？", "先抓這三筆"], emphasis=["三筆"]),
            VisualSlide(layout="steps", title_lines=["出發前先抓", "機票與保險"], emphasis=["機票", "保險"], items=["機票看淡旺季，越早訂越便宜", "保險要含海外醫療", "簽證費依國家另計"]),
            VisualSlide(layout="compare", title_lines=["托福與雅思怎麼選"], emphasis=["托福"], items=["托福較多學校接受", "雅思考場多、日期彈性大"], labels=["托福", "雅思"]),
            VisualSlide(layout="stat", title_lines=["生活費大約多少"], items=["3 萬"]),
            VisualSlide(layout="cta", title_lines=["收藏起來慢慢看"]),
        ],
        art_prompt="", issues=["第 2 頁資訊偏多，建議作者刪減"],
    )


# ---- the plan is kept inside what the page can say ----
def test_the_plan_can_move_the_layout_but_never_change_a_word():
    plan, notes = visual.normalize(designed(), SLIDES)
    assert notes == [] and [s.layout for s in plan.slides] == ["cover", "steps", "compare", "stat", "cta"]
    assert plan.slides[1].items[1] == "保險要含海外醫療" and plan.slides[2].labels == ["托福", "雅思"]

    wrong = VisualPlan(
        outline=[], spec=VisualSpec(margin=300, title_size=20, body_size=99, line_height=3.0), art_prompt="",
        slides=[VisualSlide(layout="focus", title_lines=["我改了標題"]),  # not allowed on a cover; changed words are refused
                VisualSlide(layout="steps", title_lines=["出發前先抓機票", "與保險"], emphasis=["機票", "並不存在", "保險", "淡旺季"], items=["編出來的步驟一", "編出來的步驟二"]),
                VisualSlide(layout="compare", items=["編 A", "編 B"]),
                VisualSlide(layout="stat", items=["一千二百萬億"]),  # not on the page, and too long for a headline number
                VisualSlide(layout="steps", items=["x", "y"])],  # a closing page stays a closing page
    )
    fixed, notes = visual.normalize(wrong, SLIDES)
    assert (fixed.spec.margin, fixed.spec.title_size, fixed.spec.body_size, fixed.spec.line_height) == (100, 72, 44, 1.6)
    assert fixed.slides[0].layout == "cover" and fixed.slides[0].title_lines == [SLIDES[0].title]
    steps = fixed.slides[1]
    assert steps.layout == "steps" and steps.items == ["機票看淡旺季，越早訂越便宜", "保險要含海外醫療", "簽證費依國家另計"]  # replaced by the body's own sentences
    assert steps.emphasis == ["機票", "保險"] and steps.title_lines == ["出發前先抓機票", "與保險"]
    assert fixed.slides[2].layout == "compare" and fixed.slides[2].items == ["托福較多學校接受", "雅思考場多、日期彈性大"]
    assert fixed.slides[3].layout == "focus" and fixed.slides[3].items == []
    assert fixed.slides[4].layout == "cta" and fixed.slides[4].items == []
    assert any("標題斷行改動了文字" in n for n in notes) and any("超出允許範圍" in n for n in notes) and any("不是原文" in n for n in notes)

    short, notes = visual.normalize(designed(), SLIDES[:3])
    assert len(short.slides) == 3 and any("多的捨去" in n for n in notes)
    assert visual.normalize(None, SLIDES)[0] == visual.default_plan(SLIDES)


def test_with_no_design_the_pages_get_the_plain_layouts_and_the_starting_spec():
    plan = visual.default_plan(SLIDES)
    assert [s.layout for s in plan.slides] == ["cover", "focus", "focus", "focus", "cta"]
    assert (plan.spec.margin, plan.spec.title_size, plan.spec.body_size, plan.spec.line_height) == (80, 88, 44, 1.5)  # the brief's own starting spec
    assert plan.slides[0].emphasis == ["先抓這三筆"]  # what stood out before stays the default


# ---- the brain: the designer's AI, and who reads what ----
def test_the_visual_role_follows_the_ig_copy_desk_unless_it_is_set_on_its_own():
    assert brains.resolve("designer=codex,*=claude-code", "visual") == "codex"
    assert brains.resolve("designer=codex,visual=antigravity", "visual") == "antigravity"
    assert brains.resolve("threads=codex,*=claude-code", "visual") == "claude-code"
    assert desk_of("visual") == "designer" and "visual" in brains.ROLES


# ---- the template draws her design ----
@needs_chromium
def test_the_template_follows_the_design(settings):
    renderer = Renderer(settings)
    plan, _ = visual.normalize(designed(), SLIDES)
    with renderer._page(1080, 1350) as page:
        page.goto("https://render.office/template/carousel.html", wait_until="load")

        def draw(index):
            page.evaluate("(a) => window.renderSlide(a)", {"slide": SLIDES[index].model_dump(), "index": index, "total": len(SLIDES), "site": "app.uniway-tw.com",
                                                         "story": False, "art": None, "design": Renderer._design(plan, SLIDES, index)})

        draw(1)
        assert page.locator(".steps li").count() == 3 and page.locator("mark.em").count() == 2 and page.locator("h2 .seg").count() == 2
        assert page.locator("#slide").evaluate("(el) => getComputedStyle(el).getPropertyValue('--m')") == "64px"
        assert page.locator("#slide").evaluate("(el) => el.classList.contains('em-chip') && el.classList.contains('pn-foot')")
        assert page.locator(".foot .dots").evaluate("(el) => getComputedStyle(el).display") == "none"
        text = page.locator("#slide").inner_text()
        assert all(piece in text for piece in ("機票看淡旺季，越早訂越便宜", "保險要含海外醫療", "簽證費依國家另計")) and page.locator("mark.em").first.inner_text() == "機票"
        assert page.locator(".mascot-face.peek").count() == 0  # the list fills the page: no mascot over it

        draw(2)
        assert page.locator(".versus .side").count() == 2 and page.locator(".versus .tag").all_inner_texts() == ["托福", "雅思"]
        draw(3)
        assert page.locator(".stat-hero").inner_text() == "3 萬" and page.locator(".card").count() == 1
        draw(0)
        assert page.locator("h1 .seg").count() == 2 and page.locator("h1 mark.em").inner_text() == "三筆"
        draw(4)
        assert page.locator("#slide.dark").count() == 1 and page.locator("mark.em").count() == 0  # the closing page has nothing to emphasise


@needs_chromium
def test_a_different_design_draws_a_different_picture(settings, tmp_path):
    renderer = Renderer(settings)
    draft = CarouselDraft(slides=SLIDES, caption="c", hashtags=[], art_prompt="")
    plain = renderer.carousel(draft, tmp_path / "plain", plan=visual.default_plan(SLIDES))
    styled = renderer.carousel(draft, tmp_path / "styled", plan=visual.normalize(designed(), SLIDES)[0])
    assert all(a.read_bytes() != b.read_bytes() for a, b in zip(plain[:4], styled[:4]))  # the cover, steps, compare and stat pages all changed


# ---- everyone hands their pictures to Mori ----
@pytest.fixture
def studio(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", f"{install(tmp_path / 'bin')}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def build(**extra):
        env = {"OFFICE_HOME": str(tmp_path / "var"), "OFFICE_BRAIN_FALLBACK": "offline", "OFFICE_BRAINS": "chief=antigravity,reviewer=codex,*=claude-code", **extra}
        return Office(Settings.from_env(env=env))

    return build


def calls():
    path = os.environ["FAKE_LOG"]
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()] if os.path.exists(path) else []


def design_requests():
    out = []
    for call in calls():
        if "--json-schema" in call["args"] and json.loads(call["args"][call["args"].index("--json-schema") + 1])["title"] == "VisualPlan":
            out.append(call["stdin"])
    return out


def handoffs(office, to):
    return [e for e in office.store.events() if e["kind"] == "handoff" and (e["data"] or {}).get("to") == to]


@needs_chromium
def test_a_threads_post_gets_its_picture_from_mori_who_reads_the_brief_before_the_request(studio):
    office = studio()
    item = PlanItem(channel="threads", format="text", pillar="value", angle="pain", topic="語言檢定怎麼選", brief="先看目標學校")
    office.staff["threads"].produce(None, item, Briefing(day=date(2026, 10, 29), facts=FACTS), office.at(date(2026, 10, 29), time(12, 30)))
    (draft,) = [d for d in office.store.drafts() if d["channel"] == "threads"]
    assert (office.settings.media_dir / draft["media"]["image"]).is_file()
    assert any(e["agent"] == "threads" for e in handoffs(office, "designer"))  # the paper flies from 阿脆 to Mori

    (request,) = design_requests()
    assert request.index("你是繁體中文社群資訊設計師") < request.index("阿脆寫好一則 Threads 貼文") < request.index("第 1 頁（cover）")  # brief, then the request, then the copy
    assert VISUAL_BRIEF in request and MASCOT in request and "不能改字" in request
    assert "語言檢定還沒考的交換生看這裡" in request  # the request carries the whole post


@needs_chromium
def test_a_new_colleagues_threads_card_goes_through_mori_too(studio):
    office = studio()
    office.hire("阿寫", "Threads 寫手", "寫語言檢定相關的 Threads")
    office.colleague("阿寫").write_threads("托福和雅思怎麼選", office.at(date(2026, 10, 29), time(12, 30)))
    assert any(e["agent"].startswith("hire-") for e in handoffs(office, "designer"))
    (request,) = design_requests()
    assert "阿寫寫好一則 Threads 貼文" in request


@needs_chromium
def test_mori_plans_her_own_carousels_the_same_way_and_the_plan_is_kept(studio):
    office = studio()
    item = PlanItem(channel="instagram", format="carousel", pillar="value", angle="list", topic="語言檢定怎麼選", brief="先看目標學校")
    office.staff["designer"].produce(None, item, Briefing(day=date(2026, 10, 29), facts=FACTS), office.at(date(2026, 10, 29), time(19, 30)))
    carousel = next(d for d in office.store.drafts() if d["format"] == "carousel")
    assert len(carousel["media"]["images"]) == len(carousel["payload"]["slides"]) and carousel["payload"]["visual_plan"]["spec"]["accent"] == "teal"
    assert any("缺的用一般版面" in note for note in carousel["review"]["notes"])  # the fake designer plans one page; the others get the plain layout, and the boss is told
    (request,) = design_requests()
    assert request.index("你是繁體中文社群資訊設計師") < request.index("IG 輪播《語言檢定怎麼選》")
    story = next(d for d in office.store.drafts() if d["format"] == "story")
    assert (office.settings.media_dir / story["media"]["image"]).is_file()


@needs_chromium
def test_without_a_designer_ai_the_pictures_still_get_made_with_the_plain_layouts(studio):
    office = studio(OFFICE_BRAINS="chief=antigravity,reviewer=codex,visual=offline,*=claude-code")
    item = PlanItem(channel="threads", format="text", pillar="value", angle="pain", topic="語言檢定怎麼選", brief="x")
    office.staff["threads"].produce(None, item, Briefing(day=date(2026, 10, 29), facts=FACTS), office.at(date(2026, 10, 29), time(12, 30)))
    (draft,) = [d for d in office.store.drafts() if d["channel"] == "threads"]
    assert (office.settings.media_dir / draft["media"]["image"]).is_file() and design_requests() == []


@needs_chromium
def test_a_failing_designer_costs_the_layout_not_the_picture(studio, monkeypatch):
    office = studio()

    def down(*args, **kwargs):
        from office.llm import WriterError

        raise WriterError("Claude Code 沒有登入")

    monkeypatch.setattr(office.writer, "visual_plan", down)
    draft = ThreadsDraft(text="語言檢定還沒考的交換生看這裡", topic_tag="交換學生", first_reply="x", card_title="語言檢定", card_body="先看學校")
    made = office.staff["designer"].threads_card(office.staff["threads"], draft, date(2026, 10, 29))
    assert (office.settings.media_dir / made["image"]).is_file()


# ---- "make the pictures again" really makes them again ----
@needs_chromium
def test_redo_image_gives_new_pictures_and_a_new_cover_illustration_and_keeps_the_words(studio, monkeypatch):
    office = studio(OFFICE_IMAGES="codex")
    item = PlanItem(channel="instagram", format="carousel", pillar="value", angle="list", topic="語言檢定怎麼選", brief="先看目標學校")
    office.staff["designer"].produce(None, item, Briefing(day=date(2026, 10, 29), facts=FACTS), office.at(date(2026, 10, 29), time(19, 30)))
    before = next(d for d in office.store.drafts() if d["format"] == "carousel")
    office.reject(before["id"], "不喜歡")

    monkeypatch.setenv("FAKE_CHIEF", json.dumps({"reply": "好", "actions": [{"type": "redo_image", "draft_id": before["id"], "instructions": "封面標題更大、重點用色塊"}]}))
    answer = office.staff["chief"].handle(f"#{before['id']} 的圖重做，重點用色塊")["text"]
    assert f"已經請 Mori 重新設計 #{before['id']} 的圖" in answer

    import time as clock

    deadline = clock.time() + 60
    while clock.time() < deadline and office.store.draft(before["id"])["media"]["images"] == before["media"]["images"]:
        clock.sleep(0.2)
    after = office.store.draft(before["id"])
    assert after["media"]["images"] != before["media"]["images"] and after["media"]["art"] != before["media"]["art"]  # new files, new illustration
    assert after["status"] == "pending_approval" and after["payload"]["slides"] == before["payload"]["slides"]  # back in the inbox; not one word changed
    assert any("封面標題更大" in request for request in design_requests()[-1:])  # the boss's wish reached the designer
    assert (office.settings.media_dir / after["media"]["images"][0]).is_file()
    for thread in threading.enumerate():  # the chief's thread also redraws the story; end the test only when it is done
        if thread.name.startswith(f"chief-#{before['id']} "):
            thread.join(60)
    story = next(d for d in office.store.drafts() if d["format"] == "story")
    assert office.store.draft(story["id"])["status"] == "pending_approval"


def test_redo_image_is_refused_for_a_video(studio):
    office = studio(OFFICE_RENDER_MEDIA="0")
    draft_id = office.store.add_draft(run_id=None, day="2026-10-29", channel="youtube", format="short", title="影片", payload={}, status="pending_approval")
    from office.models import ChiefAction

    assert "影片請跟阿剪說" in office.staff["chief"].execute(ChiefAction(type="redo_image", draft_id=draft_id, instructions="換"))

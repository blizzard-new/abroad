"""The design Mori hands to the renderer, and the checks that keep it inside what the templates can draw.

Mori (the visual designer, an AI) decides how a set of pages is laid out: the shared spec (margins, type sizes, line
height, accent colour, how things are emphasised, where the page number sits) and, per page, which layout it uses
(a point with a note card, steps, a comparison, one big number), where the title breaks, and which words stand out.

The words themselves are not hers to change. The copywriter wrote them and Kiki checked them against the platform's
facts, so everything the plan quotes (title lines, emphasised words, steps, comparison sides) has to be text the page
already has. Anything that does not hold, and every number outside the allowed range, is corrected here with a note,
so a plan the model got wrong still produces a good page and never a wrong one.
"""

from __future__ import annotations

import re

from .models import Slide, VisualPlan, VisualSlide, VisualSpec

LIMITS = {"margin": (60, 100), "title_size": (72, 96), "body_size": (36, 44), "line_height": (1.4, 1.6)}
POINT_LAYOUTS = ("focus", "steps", "compare", "stat")
MAX_EMPHASIS, MAX_TITLE_LINES, MAX_STEPS = 2, 3, 5
HIGHLIGHT = re.compile(r"^(.+?[？！，：])(.+)$")  # "讀書計畫寫不出來？先回答這 3 題": the part after the first mark stands out


def squash(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def tidy(text, limit: int) -> str:
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", str(text or "")).strip()[:limit]


def auto_items(body: str) -> list[str]:
    """The body cut at its sentence ends: what steps and comparisons use when the plan's own items do not hold."""
    parts = [part.strip(" 、，,") for part in re.split(r"[；;。\n]+", body or "")]
    return [part for part in parts if len(part) >= 2]


def _default_emphasis(slide: Slide) -> list[str]:
    match = HIGHLIGHT.match(slide.title)
    return [match.group(2)] if match and 2 <= len(match.group(2)) <= 14 else []


def default_slide(slide: Slide) -> VisualSlide:
    layout = "cover" if slide.kind == "cover" else "cta" if slide.kind == "cta" else "focus"
    return VisualSlide(layout=layout, title_lines=[slide.title], emphasis=_default_emphasis(slide) if layout != "cta" else [], items=[], labels=[], picture="")


def default_plan(slides: list[Slide], art_prompt: str = "") -> VisualPlan:
    """The plan when nobody designed anything (no AI, or it failed): the starting spec and the plain layouts."""
    return VisualPlan(outline=[slide.title for slide in slides], spec=VisualSpec(), slides=[default_slide(s) for s in slides], art_prompt=art_prompt, issues=[])


def clamp_spec(spec: VisualSpec) -> tuple[VisualSpec, list[str]]:
    notes, values = [], {}
    for name, (low, high) in LIMITS.items():
        given = getattr(spec, name)
        clamped = min(high, max(low, given))
        values[name] = round(clamped, 2) if name == "line_height" else int(clamped)
        if values[name] != given:
            notes.append(f"{name} 超出允許範圍（{low}～{high}），改成 {values[name]}")
    return spec.model_copy(update=values), notes


def _cleaned_lines(lines: list[str], title: str) -> list[str]:
    """The title's own line breaks: only where it breaks may change, never what it says."""
    cleaned = [tidy(line, 60) for line in lines if tidy(line, 60)]
    ok = 1 <= len(cleaned) <= MAX_TITLE_LINES and squash("".join(cleaned)) == squash(title)
    return cleaned if ok else [title]


def _cleaned_emphasis(words: list[str], lines: list[str], body: str) -> list[str]:
    found: list[str] = []
    for word in words:
        word = tidy(word, 14)
        if word and word not in found and (any(word in line for line in lines) or word in body):
            found.append(word)
    return found[:MAX_EMPHASIS]


def _words_of(page: str, items: list[str]) -> bool:
    return all(squash(item) and squash(item) in squash(page) for item in items) and len({squash(i) for i in items}) == len(items)


def design_slide(slide: Slide, proposed: VisualSlide | None, number: int) -> tuple[VisualSlide, list[str]]:
    """One page's design, made safe. `proposed` is what Mori asked for (or None)."""
    notes: list[str] = []
    base = default_slide(slide)
    if proposed is None:
        return base, notes
    layout = base.layout if base.layout in {"cover", "cta"} else proposed.layout if proposed.layout in POINT_LAYOUTS else "focus"
    if base.layout not in {"cover", "cta"} and proposed.layout not in POINT_LAYOUTS:
        notes.append(f"第 {number} 頁的版面「{proposed.layout}」不能用在這一頁，改用一般版面")
    lines = _cleaned_lines(proposed.title_lines, slide.title) if proposed.title_lines else [slide.title]
    if proposed.title_lines and squash("".join(proposed.title_lines)) != squash(slide.title):
        notes.append(f"第 {number} 頁的標題斷行改動了文字，沒有採用")
    page = f"{slide.title}\n{slide.body}"
    items = [tidy(item, 80) for item in proposed.items if tidy(item, 80)] if layout in {"steps", "compare", "stat"} else []
    labels: list[str] = []
    if layout in {"steps", "compare", "stat"}:
        want = (2, MAX_STEPS) if layout == "steps" else (2, 2) if layout == "compare" else (1, 1)
        ok = want[0] <= len(items) <= want[1] and _words_of(slide.body if layout != "stat" else page, items)
        if layout == "stat":
            ok = ok and len(squash(items[0])) <= 10
        if not ok and layout != "stat":
            items = auto_items(slide.body)[:MAX_STEPS]
            ok = want[0] <= len(items) <= want[1]
            if ok:
                notes.append(f"第 {number} 頁的「{layout}」項目不是原文，改用內文原本的句子")
        if not ok:
            notes.append(f"第 {number} 頁的「{layout}」版面需要的項目不是原文裡的字，改用一般版面")
            layout, items = "focus", []
        elif layout == "compare":
            labels = [tidy(label, 6) for label in proposed.labels][:2]
            labels = labels if len(labels) == 2 and all(label and squash(label) in squash(page) for label in labels) else []
    emphasis = [] if layout == "cta" else _cleaned_emphasis(proposed.emphasis, lines, slide.body) or (base.emphasis if layout in {"cover", "focus"} else [])
    return VisualSlide(layout=layout, title_lines=lines, emphasis=emphasis, items=items, labels=labels, picture=tidy(proposed.picture, 60)), notes


def normalize(plan: VisualPlan | None, slides: list[Slide], art_prompt: str = "") -> tuple[VisualPlan, list[str]]:
    """Mori's plan, kept inside what the templates can draw: (the plan to render, what was corrected)."""
    if plan is None:
        return default_plan(slides, art_prompt), []
    spec, notes = clamp_spec(plan.spec)
    designed = []
    for index, slide in enumerate(slides):
        proposed = plan.slides[index] if index < len(plan.slides) else None
        page, page_notes = design_slide(slide, proposed, index + 1)
        designed.append(page)
        notes += page_notes
    if len(plan.slides) != len(slides):
        notes.append(f"設計給了 {len(plan.slides)} 頁，文案有 {len(slides)} 頁，多的捨去、缺的用一般版面")
    return VisualPlan(
        outline=[tidy(line, 80) for line in plan.outline if tidy(line, 80)][:12] or [s.title for s in slides],
        spec=spec, slides=designed, art_prompt=tidy(plan.art_prompt, 500) or art_prompt,
        issues=[tidy(issue, 120) for issue in plan.issues if tidy(issue, 120)][:4],
    ), notes

"""Source-backed editorial content, rendered without JavaScript or raw HTML inputs."""
from __future__ import annotations

import math
from datetime import date
from html import escape
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EditorialModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(EditorialModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    title: str
    url: str
    note: str

    @field_validator("url")
    @classmethod
    def official_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Editorial sources must use public HTTPS URLs")
        return value


class ImageCredit(EditorialModel):
    photographer: str
    source_url: str

    @field_validator("source_url")
    @classmethod
    def public_https_url(cls, value: str) -> str:
        return Source.official_url(value)


class Table(EditorialModel):
    caption: str
    headers: list[str] = Field(min_length=2, max_length=5)
    rows: list[list[str]] = Field(min_length=1)

    @model_validator(mode="after")
    def rectangular(self):
        if any(len(row) != len(self.headers) for row in self.rows):
            raise ValueError("Table rows must match headers")
        return self


class Diagram(EditorialModel):
    title: str
    steps: list[tuple[str, str]] = Field(min_length=3, max_length=5)
    caption: str


class Section(EditorialModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    title: str
    paragraphs: list[str] = Field(min_length=1)
    bullets: list[str] = Field(default_factory=list)
    table: Table | None = None
    diagram: Diagram | None = None
    refs: list[str] = Field(default_factory=list)


class Article(EditorialModel):
    slug: str = Field(pattern=r"^[a-z]+(?:-[a-z]+)*$")
    title: str
    description: str
    category: Literal["申請準備", "費用與補助", "目的地生活", "修課與住宿"]
    published: date
    modified: date
    checked: date
    image: str = Field(pattern=r"^[a-z-]+$")
    image_alt: str
    # Defaults also let the release gate normalize historical article JSON.
    image_caption: str = ""
    image_credit: ImageCredit | None = None
    summary: list[str] = Field(min_length=3, max_length=4)
    intro: list[str] = Field(min_length=1)
    sections: list[Section] = Field(min_length=4)
    faq: list[tuple[str, str]] = Field(min_length=2)
    sources: list[Source] = Field(min_length=1)
    related: list[str] = Field(min_length=2, max_length=4)
    country: Literal["japan", "south-korea", "germany"] | None = None

    @model_validator(mode="after")
    def consistency(self):
        if self.modified < self.published:
            raise ValueError("Dates must describe the actual editorial revision")
        ids = [section.id for section in self.sections]
        if len(ids) != len(set(ids)) or set(ids) & {"faq", "sources", "related", "article-top"}:
            raise ValueError("Section anchors must be unique")
        source_ids = [source.id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Source IDs must be unique")
        if any(ref not in source_ids for section in self.sections for ref in section.refs):
            raise ValueError("Missing citation source")
        if not any(section.diagram for section in self.sections):
            raise ValueError("Include a useful original diagram")
        return self

    @property
    def minutes(self) -> int:
        text = "".join(self.intro) + "".join(p for section in self.sections for p in section.paragraphs)
        return max(5, math.ceil(len(text) / 350))

    @property
    def image_path(self) -> str:
        return f"/static/assets/editorial/{self.image}.webp"


def load_articles() -> dict[str, Article]:
    result = {}
    for file in sorted(Path(__file__).with_name("editorial").glob("*.json")):
        article = Article.model_validate_json(file.read_text(encoding="utf-8"))
        if file.stem != article.slug or article.slug in result:
            raise ValueError(f"Invalid article identity: {file.name}")
        result[article.slug] = article
    if not result:
        raise ValueError("No editorial articles found; verify packaged JSON files")
    for article in result.values():
        if article.slug in article.related or any(slug not in result for slug in article.related):
            raise ValueError(f"Invalid related articles: {article.slug}")
    return result


ARTICLES = load_articles()


def paragraphs(items: list[str]) -> str:
    return "".join(f"<p>{escape(text)}</p>" for text in items)


def article_card(article: Article) -> str:
    return f'''<li class="editorial-card"><a href="/guides/{article.slug}">
<img src="{article.image_path}" width="1536" height="1024" loading="lazy" decoding="async" alt="">
<span class="editorial-card-copy"><span class="eyebrow">{escape(article.category)} · 約 {article.minutes} 分鐘</span>
<strong>{escape(article.title)}</strong><span>{escape(article.description)}</span>
<span class="card-action">閱讀指南 <span aria-hidden="true">↗</span></span></span></a></li>'''


# The four stages of the guide index, in reading order. The one-line notes only describe what the stage's guides
# cover; every fact stays in the articles and their sources.
STAGE_NOTES = {
    "申請準備": "先分清校內甄選、母校提名與合作校申請，再確認資格、寫好讀書計畫。",
    "費用與補助": "把學費、生活費、押金與補助拆開估算，找出真正要準備的金額與申請管道。",
    "目的地生活": "依國家看生活費、住宿與初期支出；數字連同官方來源與日期一起讀。",
    "修課與住宿": "出發前確認學分怎麼採認，以及宿舍與住宿怎麼申請。",
}


def guide_index() -> str:
    body = '''<div class="editorial-index"><p class="eyebrow">UNIWAY / EXCHANGE JOURNAL</p>
<h1>交換學生指南：<br>把想交換，變成準備好。</h1><p class="lead">從第一份資格清單，到抵達宿舍的那一天。用有來源的資訊，做適合自己的決定。</p>
<nav class="editorial-categories" aria-label="文章分類">'''
    stages = [(category, [a for a in ARTICLES.values() if a.category == category]) for category in STAGE_NOTES]
    stages = [(category, articles) for category, articles in stages if articles]
    body += "".join(f'<a href="#category-{i}">{category}</a>' for i, (category, _) in enumerate(stages)) + '</nav>'
    # Every stage is plain stacked content. stage-scroll.js only adds a sticky card panel on wide screens, so each
    # card appears exactly once and the page reads the same without JavaScript.
    body += f'<div class="stage-scroll" data-stage-scroll style="--stage-count:{len(stages)}">'
    for i, (category, articles) in enumerate(stages):
        body += f'''<section class="stage-block" data-stage-block aria-labelledby="category-{i}-title">
<div class="stage-copy" id="category-{i}" data-stage-copy style="--stage-row:{i + 1}">
<p class="stage-no" aria-hidden="true">{i + 1:02d}</p><h2 id="category-{i}-title">{escape(category)}</h2>
<div class="stage-detail"><div><p class="stage-desc">{escape(STAGE_NOTES[category])}</p><p class="stage-count">{len(articles)} 篇指南</p></div></div></div>
<div class="stage-cards" data-stage-cards><ul class="editorial-cards">{"".join(article_card(a) for a in articles)}</ul></div></section>'''
    return body + '</div></div>'


def article_schema(article: Article, origin: str) -> dict:
    return {"@context": "https://schema.org", "@type": "Article", "headline": article.title,
            "description": article.description, "inLanguage": "zh-Hant", "articleSection": article.category,
            "datePublished": article.published.isoformat(), "dateModified": article.modified.isoformat(),
            "mainEntityOfPage": origin + "/guides/" + article.slug,
            "image": {"@type": "ImageObject", "url": origin + article.image_path, "width": 1536, "height": 1024},
            "author": {"@type": "Organization", "name": "UniWay 編輯團隊", "url": origin + "/editorial-policy"},
            "publisher": {"@type": "Organization", "name": "UniWay", "url": origin + "/"},
            "citation": [source.url for source in article.sources]}


def render_article(article: Article) -> str:
    a = article
    body = f'''<article class="editorial" id="article-top"><div class="article-heading">
<p class="eyebrow"><a href="/guides">交換指南</a> / {escape(a.category)}</p><h1>{escape(a.title)}</h1>
<p class="lead">{escape(a.description)}</p><p class="article-byline"><a href="/editorial-policy">UniWay 編輯團隊</a> · 約 {a.minutes} 分鐘<br>
首次刊載 <time datetime="{a.published}">{a.published}</time> · 內容更新 <time datetime="{a.modified}">{a.modified}</time> · 來源核對 {a.checked}</p></div>
<div class="article-layout"><aside class="article-toc"><details open><summary>這篇會帶你了解</summary><nav aria-label="文章目錄"><ol>'''
    body += "".join(f'<li><a href="#{s.id}">{escape(s.title)}</a></li>' for s in a.sections)
    body += '<li><a href="#faq">常見問題</a></li><li><a href="#sources">官方來源與適用範圍</a></li></ol></nav></details></aside><div class="article-body">'
    body += '<aside class="article-takeaways" aria-label="先讀重點"><p class="eyebrow">先讀重點</p><ul>'
    body += ''.join(f'<li>{escape(point)}</li>' for point in a.summary) + '</ul></aside>' + paragraphs(a.intro)
    for index, section in enumerate(a.sections):
        body += f'<section id="{section.id}"><h2><span class="section-number" aria-hidden="true">{index + 1:02d}</span>{escape(section.title)}</h2>'
        body += paragraphs(section.paragraphs)
        if section.bullets:
            body += '<ul class="article-checklist">' + ''.join(f'<li>{escape(item)}</li>' for item in section.bullets) + '</ul>'
        if section.table:
            t = section.table
            body += f'<div class="article-table" tabindex="0" role="region" aria-label="{escape(t.caption)}，可橫向捲動"><table><caption>{escape(t.caption)}</caption><thead><tr>'
            body += ''.join(f'<th scope="col">{escape(h)}</th>' for h in t.headers) + '</tr></thead><tbody>'
            for row in t.rows:
                body += '<tr><th scope="row">' + escape(row[0]) + '</th>' + ''.join(f'<td>{escape(v)}</td>' for v in row[1:]) + '</tr>'
            body += '</tbody></table></div>'
        if section.diagram:
            d = section.diagram
            body += f'<figure class="article-diagram"><p class="diagram-title">{escape(d.title)}</p><ol>'
            body += ''.join(f'<li><span class="diagram-number" aria-hidden="true">{n:02d}</span><strong>{escape(label)}</strong><span>{escape(text)}</span></li>' for n, (label, text) in enumerate(d.steps, 1))
            body += '</ol><figcaption>' + escape(d.caption) + '</figcaption></figure>'
        if section.refs:
            body += '<p class="article-citation">本節來源：' + '、'.join(f'<a href="#source-{ref}">{escape(next(s.title for s in a.sources if s.id == ref))}</a>' for ref in section.refs) + '</p>'
        body += '</section>'
        if index == 1:
            caption = escape(a.image_caption)
            if a.image_credit:
                credit = a.image_credit
                caption += f' 攝影：<a href="{escape(credit.source_url)}" rel="noopener noreferrer">{escape(credit.photographer)} / Pexels</a>。'
            body += f'<figure class="article-illustration"><img src="{a.image_path}" alt="{escape(a.image_alt)}" width="1536" height="1024" loading="lazy" decoding="async"><figcaption>{caption}</figcaption></figure>'
    body += '<section id="faq"><h2>你可能還想知道</h2>'
    body += ''.join(f'<details class="article-faq"><summary>{escape(q)}</summary><p>{escape(answer)}</p></details>' for q, answer in a.faq) + '</section>'
    body += '<section class="article-sources" id="sources"><h2>官方來源與適用範圍</h2><p>數字、制度與申請條件請連同來源日期閱讀。本文的方法、表格與試算由 UniWay 整理；各校個案依當期公告認定。</p><ol>'
    body += ''.join(f'<li id="source-{s.id}"><a href="{escape(s.url)}" rel="noopener noreferrer" data-official-source>{escape(s.title)}</a><p>{escape(s.note)}</p></li>' for s in a.sources) + '</ol></section>'
    body += '<aside class="article-next"><p class="eyebrow">把資訊用在自己的選校清單</p><h2>下一步，從你的母校出發。</h2><p>找出適用的合作方案，逐一比對資格、費用與官方公告。</p><a class="article-button" href="/schools">查閱母校與合作學校 →</a> <a href="/#partners">開啟選校工具</a>'
    if a.country:
        name = {"japan": "日本", "south-korea": "韓國", "germany": "德國"}[a.country]
        body += f'<p><a href="/destinations/{a.country}">比較{name}交換選項與各母校方案</a></p>'
    body += '</aside><p class="back-top"><a href="#article-top">回到文章開頭 ↑</a></p></div></div>'
    body += '<section id="related"><h2>接著準備這些事</h2><ul class="editorial-cards">' + ''.join(article_card(ARTICLES[slug]) for slug in a.related) + '</ul></section></article>'
    return body

"""Personal selection notes and source-bound Chinese experience summaries."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .public_translation import cached_translation, needs_translation, translate_public_excerpts


class SchoolPreference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    interest: int = Field(default=0, ge=0, le=5)
    note: str = Field(default="", max_length=1000)


class ExperienceBookmark(BaseModel):
    model_config = ConfigDict(extra="forbid")
    school_name: str = Field(min_length=1, max_length=240)
    country: str = Field(default="", max_length=100)
    title: str = Field(default="", max_length=500)
    source_url: str = Field(default="", max_length=2000)
    summary: str = Field(default="", max_length=1500)
    summary_zh: str = Field(default="", max_length=1500)
    original_summary: str = Field(default="", max_length=1500)
    exchange_term: str = Field(default="", max_length=120)
    published_at: str = Field(default="", max_length=100)
    language: str = Field(default="", max_length=40)
    source_type: str = Field(default="", max_length=40)
    translation_status: str = Field(default="", max_length=40)
    themes: list[str] = Field(default_factory=list, max_length=14)
    theme_summaries: dict[str, str] = Field(default_factory=dict, max_length=14)
    theme_summaries_zh: dict[str, str] = Field(default_factory=dict, max_length=14)

    @field_validator("source_url")
    @classmethod
    def safe_link(cls, value: str) -> str:
        if value:
            url = urlsplit(value)
            if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
                raise ValueError("source_url must be an HTTP(S) source link")
        return value

    @field_validator("theme_summaries", "theme_summaries_zh")
    @classmethod
    def bounded_themes(cls, value: dict[str, str]) -> dict[str, str]:
        if any(len(key) > 40 or len(summary) > 1500 for key, summary in value.items()):
            raise ValueError("theme summaries are too long")
        return value


class RecentDiscoveryView(ExperienceBookmark):
    kind: str = Field(pattern=r"^(school|experience)$")
    viewed_at: str = Field(default="", max_length=40)


class DiscoveryWorkspace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    school_preferences: dict[str, SchoolPreference] = Field(default_factory=dict, max_length=500)
    preference_order: list[str] = Field(default_factory=list, max_length=30)
    saved_experiences: dict[str, ExperienceBookmark] = Field(default_factory=dict, max_length=300)
    recent_views: list[RecentDiscoveryView] = Field(default_factory=list, max_length=20)

    @field_validator("saved_experiences")
    @classmethod
    def source_required(cls, value: dict[str, ExperienceBookmark]) -> dict[str, ExperienceBookmark]:
        if any(not source.source_url for source in value.values()):
            raise ValueError("a saved experience must have a source link")
        return value

    @field_validator("school_preferences")
    @classmethod
    def valid_school_keys(cls, value: dict[str, SchoolPreference]) -> dict[str, SchoolPreference]:
        if any(not name.strip() or len(name) > 240 or name in {"__proto__", "constructor", "prototype"} for name in value):
            raise ValueError("invalid school name")
        return value

    @field_validator("preference_order")
    @classmethod
    def distinct_schools(cls, value: list[str]) -> list[str]:
        if any(not item.strip() or len(item) > 240 for item in value):
            raise ValueError("invalid school name")
        return list(dict.fromkeys(item.strip() for item in value))


def localize_experience_digest(digest, data_dir: Path, *, generate: bool = False):
    """Keep original excerpts; absence of a translation never becomes a fact."""
    if generate:
        excerpts = [(value, source.source_url) for source in digest.sources
                    for value in [source.summary, *source.theme_summaries.values()] if value]
        translate_public_excerpts(excerpts, data_dir)
    localized = []
    for source in digest.sources:
        def chinese(value):
            if not needs_translation(value):
                return value, "original"
            return cached_translation(value, source.source_url, data_dir) or ("", "pending")
        summary, status = chinese(source.summary)
        terms = source.exchange_term
        if not terms:
            # A publication year is not an exchange term. Only explicit labels count.
            match = re.search(r"(?:交換(?:期間|學期)|研修期間)\s*[:：]\s*([^\n。；]{3,50})", source.summary)
            terms = match.group(1).strip() if match else None
        localized.append(source.model_copy(update={
            "summary_zh": summary, "original_summary": source.summary,
            "translation_status": status, "exchange_term": terms,
            "theme_summaries_zh": {theme: chinese(value)[0] for theme, value in source.theme_summaries.items()},
        }))
    return digest.model_copy(update={"sources": localized})

"""Measure download, text and explicit reading evidence independently."""


def source_content_status(source: dict) -> dict:
    pages = source.get("pages", [])
    text_pages = sum(
        bool((p.get("text") or "").replace("\x00", "").strip()) for p in pages
    )
    sha = source.get("sha256")
    visual = source.get("visual_review", {})
    visual_valid = bool(sha and visual.get("source_sha256") == sha)
    visual_pages = set(visual.get("pdf_pages_reviewed", [])) if visual_valid else set()
    converted_pages = (
        set(visual.get("converted_pages_reviewed", [])) if visual_valid else set()
    )
    if visual_valid and visual.get("pdf_page") is not None:
        visual_pages.add(visual["pdf_page"])
    reading = source.get("reading_review", {})
    read_pages = (
        set(reading.get("pages_reviewed", []))
        if sha and reading.get("source_sha256") == sha
        else set()
    ) | visual_pages
    page_ids = {p["page"] for p in pages}
    status = source.get("status")
    return {
        "downloaded": bool(isinstance(status, int) and 200 <= status < 300 and sha),
        "page_count": len(pages),
        "text_page_count": text_pages,
        "any_text": bool(text_pages and not source.get("error")),
        "all_pages_have_text": bool(
            pages and text_pages == len(pages) and not source.get("error")
        ),
        # Text extraction itself is never evidence that a person read a page.
        "all_pages_read": bool(
            pages and page_ids <= read_pages and not source.get("error")
        ),
        "visual_reviewed_page_count": len(page_ids & visual_pages)
        + len(converted_pages),
        "visual_reviewed": bool(page_ids & visual_pages or converted_pages),
        "ocr_status": source.get("ocr_status", "not_performed"),
    }

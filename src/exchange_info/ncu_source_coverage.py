"""Measure download, text and explicit reading evidence independently."""


def attach_visual_review(source: dict, review: dict) -> None:
    """Attach SHA-bound review while keeping original extraction untouched."""
    if not source.get("sha256") or review.get("source_sha256") != source["sha256"]:
        for key in ("visual_review", "page_transcriptions", "ocr_status"):
            source.pop(key, None)
        source["visual_review_note"] = "原件已變更，既有視覺摘錄與逐頁閱讀紀錄不套用。"
        return
    source["visual_review"] = review
    page_ids = {p["page"] for p in source.get("pages", [])}
    source["page_transcriptions"] = [
        p for p in review.get("page_transcriptions", []) if p["page"] in page_ids
    ]
    if review.get("ocr_status"):
        source["ocr_status"] = review["ocr_status"]


def indexable_source_text(source: dict) -> str:
    """Keep known broken layers out of retrieval; the audit retains originals.

    Page quarantine is explicit research metadata, never a text/price heuristic.
    A replacement needs matching source and review SHAs and the same reviewed
    PDF page. A changed source remains isolated until it is reviewed again.
    """
    sha = source.get("sha256")
    visual = source.get("visual_review", {})
    visual_valid = bool(sha and visual.get("source_sha256") == sha)
    reviewed_pages = set(visual.get("pdf_pages_reviewed", [])) if visual_valid else set()
    if visual_valid and visual.get("pdf_page") is not None:
        reviewed_pages.add(visual["pdf_page"])
    passages = {
        p["page"]: p["text"]
        for p in source.get("page_transcriptions", [])
        if p["page"] in reviewed_pages and p.get("text", "").strip()
    }
    policy = source.get("index_review", {})
    quarantined = set(policy.get("quarantined_pdf_pages", []))
    replacement_valid = bool(sha and policy.get("source_sha256") == sha)
    parts = []
    for page in source.get("pages", []):
        number = page["page"]
        marker = (f"【原文圖片{page['image']}／無PDF頁碼】" if page.get("image")
                  else f"【投影片{page['slide']}／無PDF頁碼】" if page.get("slide")
                  else f"【第{number}頁】" if number is not None else "【網頁／無PDF頁碼】")
        passage = passages.get(number)
        if number in quarantined:
            note = policy.get("page_applicability_notes_zh", {}).get(str(number), "116當期適用性未核實。")
            text = (
                f"【同SHA、同頁人工視覺核對的選定原文；原始破損圖層僅供來源稽核】\n{note}\n{passage}"
                if replacement_valid and passage
                else policy.get("isolation_note_zh", "此頁已知破損文字層已隔離；尚無同SHA、同頁核對內容可供問答索引。")
            )
        else:
            text = page.get("text") or ""
            if passage:
                text += f"\n【同SHA、同頁人工視覺核對摘錄，非全文轉錄；116適用性未核實】\n{passage}"
        parts.append(f"{marker}\n{text}")
    return "\n\n".join(parts)


def attach_public_field_excerpt(source: dict, excerpt: dict) -> None:
    """Enforce a reviewed public excerpt during both collection and rebuild."""
    if source.get("error"):
        source["pages"] = []
        return
    if not source.get("sha256") or excerpt.get("source_sha256") != source["sha256"]:
        source["pages"] = []
        source["error"] = "原件已變更，須重核公開欄位摘錄；不沿用舊摘錄或複製個資。"
        return
    source["pages"] = excerpt.get("public_pages") or [
        {"page": None, "text": excerpt["public_field_excerpt"]}
    ]
    source["source_excerpt_only"] = True
    source["privacy_note"] = excerpt["note_zh"]
    if "original_sheet_count" in excerpt:
        source["excerpt_original_scope"] = {
            "source_sha256": source["sha256"],
            "sheet_count": excerpt["original_sheet_count"],
            "sheets_reviewed": excerpt.get("original_sheets_reviewed", []),
        }


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
    reading_valid = bool(sha and reading.get("source_sha256") == sha)
    read_pages = (
        set(reading.get("pages_reviewed", []))
        if reading_valid
        else set()
    ) | visual_pages
    page_ids = {p["page"] for p in pages}
    sheet_ids = {p["sheet"] for p in pages if p.get("sheet")}
    slide_ids = {p["slide"] for p in pages if p.get("slide")}
    image_ids = {p["image"] for p in pages if p.get("image")}
    visual_images = set(visual.get("images_reviewed", [])) if visual_valid else set()
    all_parts_read = (
        image_ids <= (visual_images | (set(reading.get("images_reviewed", [])) if reading_valid else set()))
        if image_ids
        else reading_valid and slide_ids <= set(reading.get("slides_reviewed", []))
        if slide_ids
        else reading_valid and sheet_ids <= set(reading.get("sheets_reviewed", []))
        if sheet_ids
        else page_ids <= read_pages
    )
    original_scope = source.get("excerpt_original_scope", {})
    if original_scope:
        # A public blank-sheet excerpt cannot hide unread example sheets.
        all_parts_read = bool(
            all_parts_read and reading_valid
            and original_scope.get("source_sha256") == sha
            and isinstance(original_scope.get("sheet_count"), int)
            and original_scope["sheet_count"] > 0
            and len(set(original_scope.get("sheets_reviewed", [])))
            == original_scope["sheet_count"]
        )
    status = source.get("status")
    response_received = bool(isinstance(status, int) and 200 <= status < 300 and sha)
    return {
        # A 200 HTML error/download page is not the requested PDF or form.
        "response_bytes_received": response_received,
        "downloaded": bool(response_received and not source.get("error")),
        "page_count": len(pages),
        "text_page_count": text_pages,
        "any_text": bool(text_pages and not source.get("error")),
        "all_pages_have_text": bool(
            pages and text_pages == len(pages) and not source.get("error")
            and not source.get("source_excerpt_only")
        ),
        # Text extraction itself is never evidence that a person read a page.
        "all_pages_read": bool(
            pages and all_parts_read and not source.get("error")
        ),
        "visual_reviewed_page_count": len(page_ids & visual_pages)
        + len(converted_pages),
        "visual_reviewed_image_count": len(image_ids & visual_images),
        "visual_reviewed": bool(page_ids & visual_pages or converted_pages or image_ids & visual_images),
        "ocr_status": source.get("ocr_status", "not_performed")
        if visual_valid
        else "not_performed",
    }

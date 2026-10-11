from scripts.export_ntu_completion_report import classify_review_axes


def row(field="documents", reference=False, confirmed=False):
    return dict(field=field, reference_present=reference, target_requirement_confirmed=confirmed)


def source(sid, status, digest=None, field="documents"):
    return {"source": dict(source_id=sid, access_status=status, sha256=digest),
            "field_candidate_counts": {field: 1}}


def test_readable_unread_document_is_work_queue_even_when_another_host_is_blocked():
    result = classify_review_axes(row(), [], [source("a", "content_available", "hash"), source("b", "http_unavailable")])
    assert result["review_progress"] == "pending_public_body_read"
    assert result["unread_candidate_body_count"] == 1
    assert not result["external_blocker_exclusive"]
    assert result["publication_status"] == "not_determined_for_target_cycle"


def test_original_scope_reference_does_not_clear_another_unread_document():
    observation = dict(sha256="old", applicability_status="older_year_reference")
    result = classify_review_axes(row(reference=True), [observation], [source("a", "content_available", "new")])
    assert result["unread_candidate_source_ids"] == ["a"]
    assert result["publication_status"] == "public_reference_in_original_scope"
    assert result["review_progress"] == "reviewed_reference_partial_more_bodies"


def test_keyword_false_positive_is_reviewed_without_claiming_official_nonpublication():
    decision = dict(outcome="wrong_scope_no_exchange_field_detail", sources=[dict(sha256="body")])
    result = classify_review_axes(row(), [], [source("a", "content_available", "body")], decision)
    assert result["unread_candidate_body_count"] == 0
    assert result["review_progress"] == "wrong_scope_no_exchange_field_detail"
    assert result["publication_status"] == "not_determined_for_target_cycle"


def test_only_explicit_future_statement_gets_future_pending_publication_state():
    result = classify_review_axes(row(), [dict(applicability_status="explicitly_pending_announcement")], [])
    assert result["publication_status"] == "official_statement_future_details_pending"
    blank = classify_review_axes(row("quota"), [], [])
    assert blank["publication_status"] == "official_NTU_selection_cell_blank"


def test_checked_reference_is_not_an_external_blocker_when_other_sources_fail():
    result = classify_review_axes(row("photos", reference=True, confirmed=True), [],
        [source("host", "http_unavailable", field="photos")])
    assert not result["external_blocker_exclusive"]


def test_published_current_home_rules_are_distinct_from_pending_school_quotas():
    home = classify_review_axes(row("home_selection", reference=True, confirmed=True), [], [])
    quota = classify_review_axes(row("quota"), [], [])
    assert home["publication_status"] == "official_NTU_shared_current_cycle_rule"
    assert quota["publication_status"] == "official_NTU_selection_cell_blank"

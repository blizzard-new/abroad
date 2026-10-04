from datetime import timedelta

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.entitlements import resolve_product_entitlements
from exchange_info.models import (
    AccountSessionRecord,
    ProductAccessTier,
    ProductEntitlementReason,
    ProductFeature,
    ProductReleaseMode,
    UserAccount,
    utc_now,
)
from exchange_info.storage import save_account_sessions, save_user_accounts


def _features(snapshot):
    return {row.feature: row for row in snapshot.features}


def _authenticated_client(tmp_path, *, product_tier=ProductAccessTier.FREE):
    account = UserAccount(display_name="封測學生", product_tier=product_tier)
    token = "closed-beta-entitlement-token"
    import hashlib

    save_user_accounts([account], tmp_path)
    save_account_sessions(
        [
            AccountSessionRecord(
                account_id=account.id,
                token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
                expires_at=utc_now() + timedelta(days=1),
            )
        ],
        tmp_path,
    )
    return TestClient(create_app(tmp_path)), {"Authorization": f"Bearer {token}"}


def test_guest_keeps_public_information_without_subscription_access() -> None:
    snapshot = resolve_product_entitlements(
        None,
        release_mode=ProductReleaseMode.CLOSED_BETA,
    )
    features = _features(snapshot)

    assert snapshot.account_tier == ProductAccessTier.GUEST
    assert snapshot.effective_tier == ProductAccessTier.GUEST
    assert snapshot.billing_enabled is False
    assert features[ProductFeature.BASIC_SEARCH_AND_COMPARE].enabled is True
    assert features[ProductFeature.SINGLE_APPLICATION_PLAN].reason == ProductEntitlementReason.LOGIN_REQUIRED
    assert features[ProductFeature.AI_SCHOOL_MATCHING].enabled is False


def test_authenticated_closed_beta_account_receives_all_subscription_features() -> None:
    snapshot = resolve_product_entitlements(
        UserAccount(display_name="封測學生"),
        release_mode=ProductReleaseMode.CLOSED_BETA,
    )
    features = _features(snapshot)

    assert snapshot.account_tier == ProductAccessTier.FREE
    assert snapshot.effective_tier == ProductAccessTier.SUBSCRIPTION
    assert all(row.enabled for row in snapshot.features)
    assert features[ProductFeature.APPLICATION_DOCUMENT_GENERATION].reason == ProductEntitlementReason.CLOSED_BETA
    assert snapshot.billing_enabled is False


def test_public_mode_preserves_free_and_subscription_boundaries() -> None:
    free_snapshot = resolve_product_entitlements(
        UserAccount(display_name="免費學生"),
        release_mode=ProductReleaseMode.PUBLIC,
    )
    subscription_snapshot = resolve_product_entitlements(
        UserAccount(display_name="訂閱學生", product_tier=ProductAccessTier.SUBSCRIPTION),
        release_mode=ProductReleaseMode.PUBLIC,
    )

    free_features = _features(free_snapshot)
    subscription_features = _features(subscription_snapshot)
    assert free_features[ProductFeature.SINGLE_APPLICATION_PLAN].enabled is True
    assert free_features[ProductFeature.MULTIPLE_APPLICATION_PLANS].reason == ProductEntitlementReason.UPGRADE_REQUIRED
    assert free_features[ProductFeature.APPLICATION_PLAN_CONFLICTS].reason == ProductEntitlementReason.UPGRADE_REQUIRED
    assert free_features[ProductFeature.SMART_REMINDERS].reason == ProductEntitlementReason.UPGRADE_REQUIRED
    assert free_features[ProductFeature.EXTERNAL_CALENDAR_SYNC].reason == ProductEntitlementReason.UPGRADE_REQUIRED
    assert free_features[ProductFeature.OFFICIAL_FORM_DOWNLOADS].enabled is True
    assert free_features[ProductFeature.APPLICATION_DOCUMENT_GENERATION].reason == ProductEntitlementReason.UPGRADE_REQUIRED
    assert free_features[ProductFeature.DOCUMENT_COMPLETENESS_REVIEW].reason == ProductEntitlementReason.UPGRADE_REQUIRED
    assert subscription_features[ProductFeature.MULTIPLE_APPLICATION_PLANS].enabled is True
    assert subscription_features[ProductFeature.MULTIPLE_APPLICATION_PLANS].reason == ProductEntitlementReason.SUBSCRIPTION
    assert subscription_features[ProductFeature.APPLICATION_PLAN_CONFLICTS].enabled is True
    assert subscription_features[ProductFeature.APPLICATION_PLAN_CONFLICTS].reason == ProductEntitlementReason.SUBSCRIPTION
    assert subscription_features[ProductFeature.SMART_REMINDERS].enabled is True
    assert subscription_features[ProductFeature.SMART_REMINDERS].reason == ProductEntitlementReason.SUBSCRIPTION
    assert subscription_features[ProductFeature.EXTERNAL_CALENDAR_SYNC].enabled is True
    assert subscription_features[ProductFeature.EXTERNAL_CALENDAR_SYNC].reason == ProductEntitlementReason.SUBSCRIPTION
    assert subscription_features[ProductFeature.APPLICATION_DOCUMENT_GENERATION].enabled is True
    assert subscription_features[ProductFeature.APPLICATION_DOCUMENT_GENERATION].reason == ProductEntitlementReason.SUBSCRIPTION
    assert subscription_features[ProductFeature.DOCUMENT_COMPLETENESS_REVIEW].enabled is True
    assert subscription_features[ProductFeature.DOCUMENT_COMPLETENESS_REVIEW].reason == ProductEntitlementReason.SUBSCRIPTION


def test_entitlement_api_is_a_shared_guest_and_account_contract(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "closed_beta")
    guest_client = TestClient(create_app(tmp_path / "guest"))
    guest = guest_client.get("/product/entitlements")

    assert guest.status_code == 200
    assert guest.json()["account_tier"] == "guest"
    assert guest.json()["billing_enabled"] is False

    account_client, headers = _authenticated_client(tmp_path / "account")
    account = account_client.get("/product/entitlements", headers=headers)

    assert account.status_code == 200
    assert account.json()["effective_tier"] == "subscription"
    assert all(row["enabled"] for row in account.json()["features"])
    openapi = account_client.get("/openapi.json").json()
    assert "/product/entitlements" in openapi["paths"]

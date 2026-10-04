from __future__ import annotations

import os

from .models import (
    ProductAccessTier,
    ProductEntitlementReason,
    ProductEntitlementSnapshot,
    ProductFeature,
    ProductFeatureEntitlement,
    ProductReleaseMode,
    UserAccount,
)


PUBLIC_FEATURES = frozenset(
    {
        ProductFeature.OFFICIAL_APPLICATION_INFORMATION,
        ProductFeature.ELIGIBILITY_AND_REQUIREMENTS,
        ProductFeature.BASIC_SEARCH_AND_COMPARE,
    }
)

FREE_ACCOUNT_FEATURES = frozenset(
    {
        ProductFeature.SINGLE_APPLICATION_PLAN,
        ProductFeature.OFFICIAL_FORM_DOWNLOADS,
        ProductFeature.BASIC_DEADLINE_REMINDERS,
        ProductFeature.COMMUNITY_ACCESS,
    }
)

SUBSCRIPTION_FEATURES = frozenset(ProductFeature) - PUBLIC_FEATURES - FREE_ACCOUNT_FEATURES


def configured_product_release_mode() -> ProductReleaseMode:
    raw_mode = os.environ.get("EXCHANGE_PRODUCT_RELEASE_MODE", "closed_beta").strip().casefold()
    try:
        return ProductReleaseMode(raw_mode)
    except ValueError:
        return ProductReleaseMode.PUBLIC


def resolve_product_entitlements(
    account: UserAccount | None,
    *,
    release_mode: ProductReleaseMode | None = None,
) -> ProductEntitlementSnapshot:
    mode = release_mode or configured_product_release_mode()
    account_tier = account.product_tier if account else ProductAccessTier.GUEST
    effective_tier = account_tier
    if account and mode == ProductReleaseMode.CLOSED_BETA:
        effective_tier = ProductAccessTier.SUBSCRIPTION

    features: list[ProductFeatureEntitlement] = []
    for feature in ProductFeature:
        if feature in PUBLIC_FEATURES:
            required_tier = "public"
            enabled = True
            reason = ProductEntitlementReason.PUBLIC
        elif not account:
            required_tier = "free" if feature in FREE_ACCOUNT_FEATURES else "subscription"
            enabled = False
            reason = ProductEntitlementReason.LOGIN_REQUIRED
        elif feature in FREE_ACCOUNT_FEATURES:
            required_tier = "free"
            enabled = True
            reason = ProductEntitlementReason.FREE
        elif effective_tier == ProductAccessTier.SUBSCRIPTION:
            required_tier = "subscription"
            enabled = True
            reason = (
                ProductEntitlementReason.CLOSED_BETA
                if mode == ProductReleaseMode.CLOSED_BETA
                and account_tier != ProductAccessTier.SUBSCRIPTION
                else ProductEntitlementReason.SUBSCRIPTION
            )
        else:
            required_tier = "subscription"
            enabled = False
            reason = ProductEntitlementReason.UPGRADE_REQUIRED

        features.append(
            ProductFeatureEntitlement(
                feature=feature,
                required_tier=required_tier,
                enabled=enabled,
                requires_login=feature not in PUBLIC_FEATURES,
                reason=reason,
            )
        )

    return ProductEntitlementSnapshot(
        release_mode=mode,
        account_tier=account_tier,
        effective_tier=effective_tier,
        billing_enabled=False,
        features=features,
    )


def product_feature_enabled(
    account: UserAccount | None,
    feature: ProductFeature,
    *,
    release_mode: ProductReleaseMode | None = None,
) -> bool:
    snapshot = resolve_product_entitlements(account, release_mode=release_mode)
    return next(row.enabled for row in snapshot.features if row.feature == feature)

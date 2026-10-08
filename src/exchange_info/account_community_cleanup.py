"""Finish the existing local community deletion lifecycle before removing an account.

Supabase owns this lifecycle in its existing atomic account deletion RPC. Local
repositories must invoke the same existing de-identification and purge operations
while identities are still linked, so failed cleanup can be retried by the owner.
"""
from .community_repositories import (
    CommunityRepositoryError,
    PrivateCommunityIdentityPurgeRequest,
    PrivateCommunityMutationStatus,
    PublicAuthorAnonymizationRequest,
    PublicAuthorAnonymizationStatus,
)


def cleanup_local_account_community(repository, account_id: str) -> None:
    if repository.backend_name != "jsonl":
        return
    for identity in repository.list_identities():
        if identity.account_id != account_id:
            continue
        result = repository.anonymize_public_author(PublicAuthorAnonymizationRequest(
            mutation_id=f"delete-public-{account_id}-{identity.id}",
            identity_id=identity.id, expected_account_id=account_id,
        ))
        if result.status != PublicAuthorAnonymizationStatus.COMMITTED:
            raise CommunityRepositoryError("公開作者去識別尚未完成，保留帳號以便重試。")
        result = repository.purge_private_identity(PrivateCommunityIdentityPurgeRequest(
            mutation_id=f"delete-private-{account_id}-{identity.id}",
            identity_id=identity.id, expected_account_id=account_id,
        ))
        if result.status != PrivateCommunityMutationStatus.COMMITTED:
            raise CommunityRepositoryError("私人社群清理尚未完成，保留帳號以便重試。")
        repository.purge_identity(identity.id, expected_account_id=account_id)

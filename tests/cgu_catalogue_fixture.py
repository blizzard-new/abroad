"""Explicit in-memory CGU source for API tests; never represents a live fetch."""
from exchange_info.cgu_catalogue import CatalogueView
from exchange_info.models import CatalogueSourceStatus


def fixed_cgu_catalogue(fetcher):
    def factory(*_):
        class FixtureCatalogue:
            def __init__(self):
                self.rows = fetcher()

            def view(self, **_):
                return CatalogueView(
                    [row.model_copy(deep=True) for row in self.rows],
                    CatalogueSourceStatus(status="saved_reference", last_success_at="2026-10-01T00:00:00Z"),
                )
        return FixtureCatalogue()
    return factory

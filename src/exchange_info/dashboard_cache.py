"""A byte-bounded cache of immutable public dashboard responses.

The owning app's lock covers get/put, including its single-flight bookkeeping.
Only the latest generation of a school/base-URL pair is retained. Expiring a
response must not retain another complete copy until 96 future cache misses.
"""
from collections import OrderedDict

DashboardResponse = tuple[bytes, bytes, str]


class DashboardResponseCache:
    def __init__(self, *, max_bytes: int = 64 * 1024 * 1024, max_entries: int = 32):
        self.max_bytes = max_bytes
        self.max_entries = max_entries
        self.payload_bytes = 0
        self._entries: OrderedDict[tuple, DashboardResponse] = OrderedDict()

    def __len__(self) -> int:
        return len(self._entries)

    def values(self):
        return self._entries.values()

    def get(self, key: tuple) -> DashboardResponse | None:
        result = self._entries.get(key)
        if result is not None:
            self._entries.move_to_end(key)
        return result

    def _remove(self, key: tuple) -> None:
        old = self._entries.pop(key)
        self.payload_bytes -= len(old[0]) + len(old[1])

    def put(self, key: tuple, result: DashboardResponse) -> None:
        for old_key in tuple(self._entries):
            if old_key[:2] == key[:2]:
                self._remove(old_key)
        size = len(result[0]) + len(result[1])
        # A large response is still returned in full; it simply is not retained.
        if size > self.max_bytes or self.max_entries <= 0:
            return
        while self._entries and (
            self.payload_bytes + size > self.max_bytes
            or len(self._entries) >= self.max_entries
        ):
            self._remove(next(iter(self._entries)))
        self._entries[key] = result
        self.payload_bytes += size

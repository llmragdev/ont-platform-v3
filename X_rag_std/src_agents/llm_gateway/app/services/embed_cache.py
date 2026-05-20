import hashlib
import time
from threading import Lock

from app.core.config import settings


class EmbedCache:
    """텍스트 해시 → 임베딩 벡터 TTL 캐시 (인메모리)."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[list[float], float]] = {}
        self._lock = Lock()
        self._ttl = settings.embed_cache_ttl
        self._max = settings.embed_cache_max

    def _key(self, text: str, model: str, tenant_id: str) -> str:
        raw = f"{tenant_id}::{model}::{text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, text: str, model: str, tenant_id: str = "default") -> list[float] | None:
        k = self._key(text, model, tenant_id)
        with self._lock:
            entry = self._store.get(k)
            if entry is None:
                return None
            vec, ts = entry
            if time.time() - ts > self._ttl:
                del self._store[k]
                return None
            return vec

    def set(self, text: str, model: str, vec: list[float], tenant_id: str = "default") -> None:
        k = self._key(text, model, tenant_id)
        with self._lock:
            if len(self._store) >= self._max:
                oldest = min(self._store, key=lambda x: self._store[x][1])
                del self._store[oldest]
            self._store[k] = (vec, time.time())

    @property
    def size(self) -> int:
        return len(self._store)


embed_cache = EmbedCache()

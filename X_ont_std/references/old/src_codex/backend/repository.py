from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile

from .data import fresh_raw_data


class DataRepository:
    def load(self) -> dict:
        raise NotImplementedError

    def save(self, raw: dict) -> None:
        raise NotImplementedError


class InMemoryDataRepository(DataRepository):
    def __init__(self, seed: dict | None = None) -> None:
        self.raw = deepcopy(seed) if seed is not None else fresh_raw_data()

    def load(self) -> dict:
        return deepcopy(self.raw)

    def save(self, raw: dict) -> None:
        self.raw = deepcopy(raw)


class JsonFileDataRepository(DataRepository):
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            raw = fresh_raw_data()
            self.save(raw)
            return raw
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, raw: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as handle:
            json.dump(raw, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temp_path = Path(handle.name)
        temp_path.replace(self.path)

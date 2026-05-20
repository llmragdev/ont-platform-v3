from __future__ import annotations

import re

from .errors import AppError


_DATASET_NAME = re.compile(r"^[A-Za-z가-힣0-9]+_[A-Za-z가-힣0-9]+_v\d+$")


class GovernanceService:
    def validate_dataset_name(self, dataset_name: str) -> str:
        if not _DATASET_NAME.fullmatch(dataset_name):
            raise AppError(
                "INVALID_GOVERNANCE_NAME",
                "dataset_name must follow [domain]_[topic]_v[number], for example 생산_공정지연_v1.",
                400,
            )
        return dataset_name

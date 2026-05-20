import os
from typing import List


class KeyPool:
    """API 키 풀 관리 (키 로테이션 지원)"""

    def __init__(self):
        keys_str = os.getenv("GEMINI_API_KEYS", "")
        self.keys: List[str] = [k.strip() for k in keys_str.split(",") if k.strip()]

        if not self.keys:
            single_key = os.getenv("GEMINI_API_KEY", "")
            if single_key:
                self.keys = [single_key]

        self.current_index = 0

    @property
    def pool_size(self) -> int:
        return len(self.keys)

    def get_key(self) -> str:
        """다음 키를 반환 (라운드 로빈)"""
        if not self.keys:
            return ""
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key


key_pool = KeyPool()

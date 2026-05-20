from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class UserInfoSettings(BaseSettings):
    database_url: str = Field(validation_alias="DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file="F:/ai_std_dev/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class UserInfoSearch(BaseModel):
    keyword: Optional[str] = None
    limit: int = 100


class UserInfoRead(BaseModel):
    user_id: int = Field(validation_alias="id")
    name: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserInfoSummary(BaseModel):
    total_count: int
    keyword: Optional[str] = None

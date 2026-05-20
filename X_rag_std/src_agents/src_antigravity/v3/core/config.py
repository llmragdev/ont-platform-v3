from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_gateway_url: str = "http://localhost:8010"
    
    class Config:
        env_file = ".env"

settings = Settings()

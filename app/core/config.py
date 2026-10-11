import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = Field(default="EcoPulse")
    app_version: str = Field(default="0.1.0")
    env: str = Field(default=os.getenv("ENV", "development"))
    storage_backend: str = Field(default=os.getenv("STORAGE_BACKEND", "local"))
    dynamodb_table_name: str = Field(default=os.getenv("DYNAMODB_TABLE_NAME", "ecopulse-records"))
    aws_region: str = Field(default=os.getenv("AWS_REGION", "us-east-1"))
    
    # Water baseline and thresholds
    default_water_baseline_per_person_liters: float = Field(
        default=float(os.getenv("DEFAULT_WATER_BASELINE_PER_PERSON_LITERS", "135.0"))
    )
    water_elevated_ratio: float = Field(default=float(os.getenv("WATER_ELEVATED_RATIO", "1.25")))
    water_unusual_ratio: float = Field(default=float(os.getenv("WATER_UNUSUAL_RATIO", "1.50")))
    water_critical_ratio: float = Field(default=float(os.getenv("WATER_CRITICAL_RATIO", "2.00")))


settings = Settings()

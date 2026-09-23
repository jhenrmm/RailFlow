from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

Profile = Literal[
    "driving-car",
    "driving-hgv",
    "foot-walking",
    "cycling-regular",
    "wheelchair",
]


class Coordinates(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class RouteAnalysisRequest(BaseModel):
    origin: Coordinates
    destination: Coordinates
    profile: Profile = "driving-car"


class WeatherSnapshot(BaseModel):
    location: str
    latitude: float
    longitude: float
    temperature_2m: float | None = None
    apparent_temperature: float | None = None
    relative_humidity_2m: float | None = None
    precipitation: float | None = None
    weather_code: int | None = None
    wind_speed_10m: float | None = None
    wind_direction_10m: float | None = None
    time: str | None = None


class RouteSummary(BaseModel):
    profile: str
    distance_km: float
    duration_min: float


class RouteAnalysisResponse(BaseModel):
    route: RouteSummary
    weather: list[WeatherSnapshot]
    analysis: str
    model: str


class HistoryEntry(BaseModel):
    id: int
    user_id: int | None
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    profile: str
    distance_m: float
    duration_s: float
    weather_json: str
    analysis: str
    model: str
    created_at: datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value: str) -> str:
        return value.lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def _lower_email(cls, value: str) -> str:
        return value.lower()


class UserResponse(BaseModel):
    id: int
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserResponse
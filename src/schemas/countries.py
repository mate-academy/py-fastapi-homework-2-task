from typing import Optional

from pydantic import BaseModel, Field


class CountryCreateSchema(BaseModel):
    code: str = Field(pattern=r"^[A-Z]{2,3}$")


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    model_config = {"from_attributes": True}

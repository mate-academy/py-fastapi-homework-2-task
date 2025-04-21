from typing import Optional

from pydantic import BaseModel, ConfigDict


class CountryResponseSchema(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CountryAddedSchema(BaseModel):
    code: str
    name: Optional[str] = None

from typing import Optional

from pydantic import BaseModel, ConfigDict


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = ConfigDict(from_attributes=True)

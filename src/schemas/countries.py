from pydantic import BaseModel
from typing_extensions import Optional


class CountrySchema(BaseModel):
    code: str
    name: Optional[str] = None


class CountryResponseSchema(CountrySchema):
    id: int
    model_config = {
        "from_attributes": True,
    }

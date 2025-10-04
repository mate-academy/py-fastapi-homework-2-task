from pydantic import BaseModel, Field, ConfigDict


class CountrySchema(BaseModel):
    id: int
    code: str = Field(..., max_length=3)
    name: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )

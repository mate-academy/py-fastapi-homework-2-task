from pydantic import BaseModel, constr


class CountryBaseSchema(BaseModel):
    code: constr(min_length=3, max_length=3, to_upper=True)
    name: str | None = None


class CountryRetrieveSchema(CountryBaseSchema):
    id: int

    class Config:
        from_attributes = True

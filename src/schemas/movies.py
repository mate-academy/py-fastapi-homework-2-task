from pydantic import BaseModel


class MovieBase(BaseModel):
    title: str
    genre: str
    price: float

class MovieCreate(MovieBase):
    pass

class MovieUpdate(MovieBase):
    pass

class MovieRead(MovieBase):
    id: int

    class Config:
        from_attributes = True

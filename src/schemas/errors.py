from pydantic import BaseModel


class HTTP404ErrorSchema(BaseModel):
    detail: str

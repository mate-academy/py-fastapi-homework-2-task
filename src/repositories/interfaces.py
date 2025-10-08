from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.sql.elements import UnaryExpression
from pydantic import BaseModel


class IAsyncRepository(ABC):
    @abstractmethod
    async def is_exist(self, *args) -> bool:
        pass

    @abstractmethod
    async def get_object(self, *args) -> Any:
        pass

    @abstractmethod
    async def get_object_or_404(self, *args) -> Any:
        pass

    @abstractmethod
    async def get_total(self, *args) -> Any:
        pass

    @abstractmethod
    async def get_objects(self, *args, offset: int, limit: int, ordering: UnaryExpression | None) -> list[Any]:
        pass

    @abstractmethod
    async def get_objects_or_404(self, *args, offset: int, limit: int, ordering: UnaryExpression | None) -> list[Any]:
        pass

    @abstractmethod
    async def create_object(self, data: dict | BaseModel) -> Any:
        pass

    @abstractmethod
    async def update_object(self, data: dict | BaseModel, *args, raise_exception: bool = False) -> Any:
        pass

    @abstractmethod
    async def delete_object(self, *args, raise_exception: bool = False) -> Any:
        pass

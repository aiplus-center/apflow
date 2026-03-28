"""
SQLite storage backend extension

Provides SQLite database backend as an ExtensionCategory.STORAGE extension.
Delegates to SQLiteDialect for shared logic.
"""

from typing import Any

from apflow.core.extensions.decorators import storage_register
from apflow.core.extensions.storage import StorageBackend
from apflow.core.storage.dialects.sqlite import SQLiteDialect


@storage_register()
class SQLiteStorage(StorageBackend):
    """SQLite storage backend extension.

    Delegates to SQLiteDialect for normalize/denormalize/connection logic.
    """

    id = "sqlite"
    name = "SQLite Storage"
    description = "Embedded SQLite database backend (default)"
    version = "1.0.0"

    @property
    def type(self) -> str:
        return "sqlite"

    def normalize_data(self, data: dict[str, Any]) -> dict[str, Any]:
        return SQLiteDialect.normalize_data(data)

    def denormalize_data(self, data: dict[str, Any]) -> dict[str, Any]:
        return SQLiteDialect.denormalize_data(data)

    def get_connection_string(self, **kwargs: Any) -> str:
        if "connection_string" in kwargs:
            return kwargs["connection_string"]
        path = kwargs.get("path", ":memory:")
        return SQLiteDialect.get_connection_string(path)

    def get_engine_kwargs(self) -> dict[str, Any]:
        return SQLiteDialect.get_engine_kwargs()


__all__ = ["SQLiteStorage"]

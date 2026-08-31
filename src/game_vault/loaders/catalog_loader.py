"""Load Pydantic catalog models from JSON resources."""

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_catalog(path: Path, model: type[T]) -> list[T]:
    """Load and validate catalog records from a JSON file.

    :param path: Path to a JSON array of model objects.
    :param model: Pydantic model used to validate each object.
    :return: Validated catalog records in source order.
    :raises OSError: If the catalog file cannot be read.
    :raises json.JSONDecodeError: If the file does not contain valid JSON.
    :raises pydantic.ValidationError: If an item does not match ``model``.
    """
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return [model.model_validate(item) for item in data]

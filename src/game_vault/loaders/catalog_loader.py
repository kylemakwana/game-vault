import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_catalog(path: Path, model: type[T]) -> list[T]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return [model.model_validate(item) for item in data]

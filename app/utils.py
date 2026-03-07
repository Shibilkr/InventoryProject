import random
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import HTTPException


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def generate_barcode() -> str:
    """Generate a valid EAN-13 barcode (12 random digits + check digit)."""
    digits = [random.randint(0, 9) for _ in range(12)]
    check = (10 - sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits)) % 10) % 10
    return "".join(map(str, digits)) + str(check)


def parse_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail=f"Invalid ObjectId: {value}")
    return ObjectId(value)


def model_to_dict(model: Any, *, exclude_none: bool = True) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=exclude_none)
    return model.dict(exclude_none=exclude_none)


def _to_json_compatible(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_to_json_compatible(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_json_compatible(val) for key, val in value.items()}
    return value


def serialize_document(doc: dict | None) -> dict:
    if doc is None:
        return {}
    serialized = _to_json_compatible(doc)
    if "_id" in serialized:
        serialized["id"] = serialized.pop("_id")
    return serialized


def serialize_documents(docs: list[dict]) -> list[dict]:
    return [serialize_document(doc) for doc in docs]

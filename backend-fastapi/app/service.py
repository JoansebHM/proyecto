import math
from typing import Any


class ValidationError(Exception):
    """Datos inválidos (HTTP 400)."""


class NotFoundError(Exception):
    """Producto inexistente (HTTP 404)."""


def _to_number(value: Any) -> float:
    if isinstance(value, bool):
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


class ItemsService:
    """'Base de datos' en memoria: se pierde al reiniciar el servidor."""

    def __init__(self) -> None:
        self._items: list[dict] = []
        self._next_id = 1

    def find_all(self) -> list[dict]:
        return self._items

    def create(self, data: dict) -> dict:
        valid = self._validate(data)
        item = {"id": self._next_id, **valid, "purchased": False}
        self._next_id += 1
        self._items.append(item)
        return item

    def update(self, item_id: int, data: dict) -> dict:
        item = self._find_one(item_id)
        fields = {k: data[k] for k in ("name", "quantity", "price") if k in data}
        if fields:
            item.update(self._validate({**item, **fields}))
        if isinstance(data.get("purchased"), bool):
            item["purchased"] = data["purchased"]
        return item

    def remove(self, item_id: int) -> None:
        item = self._find_one(item_id)
        self._items = [i for i in self._items if i is not item]

    def _find_one(self, item_id: int) -> dict:
        for item in self._items:
            if item["id"] == item_id:
                return item
        raise NotFoundError(f"Producto {item_id} no existe")

    @staticmethod
    def _validate(data: dict) -> dict:
        raw_name = data.get("name")
        name = raw_name.strip() if isinstance(raw_name, str) else ""
        quantity = _to_number(data.get("quantity"))
        price = _to_number(data.get("price"))
        if not name:
            raise ValidationError("El nombre es obligatorio")
        if not math.isfinite(quantity) or not quantity.is_integer() or quantity < 1:
            raise ValidationError("La cantidad debe ser un entero mayor a 0")
        if not math.isfinite(price) or price < 0:
            raise ValidationError("El precio debe ser un número mayor o igual a 0")
        return {"name": name, "quantity": int(quantity), "price": price}

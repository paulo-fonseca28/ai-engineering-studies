"""Read-only, validated access to the synthetic order snapshot."""
from datetime import datetime
import hashlib
from pathlib import Path
import time
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

ORDERS_PATH = Path(__file__).resolve().parents[1] / "data/orders.json"
ORDER_ID_PATTERN = r"^DEMO-[0-9]{4}$"
OrderId = Annotated[str, Field(min_length=9, max_length=9, pattern=ORDER_ID_PATTERN)]
OrderStatus = Literal["received", "preparing", "out_for_delivery", "delivered", "cancelled"]
STATUS_LABELS = {"received": "recebido", "preparing": "em preparo", "out_for_delivery": "em entrega",
                 "delivered": "entregue", "cancelled": "cancelado"}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class LookupOrderInput(StrictModel):
    order_id: OrderId


class OrderItem(StrictModel):
    sku: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=1, le=100)
    unit_price_cents: int = Field(ge=0, le=1_000_000)


class DemoOrder(StrictModel):
    order_id: OrderId
    status: OrderStatus
    updated_at: datetime
    items: list[OrderItem] = Field(min_length=1, max_length=100)
    currency: Literal["BRL"]
    total_cents: int = Field(ge=0)

    @model_validator(mode="after")
    def consistent_order(self):
        if self.updated_at.utcoffset() is None:
            raise ValueError("Order timestamp must include timezone")
        if self.total_cents != sum(item.quantity * item.unit_price_cents for item in self.items):
            raise ValueError("Order total differs from item totals")
        if len({item.sku for item in self.items}) != len(self.items):
            raise ValueError("Duplicate item SKU")
        return self


class OrderDataset(StrictModel):
    schema_version: int
    synthetic: bool
    snapshot_at: datetime
    orders: list[DemoOrder]

    @model_validator(mode="after")
    def consistent_snapshot(self):
        if self.schema_version != 1 or not self.synthetic:
            raise ValueError("Only synthetic schema v1 is supported")
        if self.snapshot_at.utcoffset() is None:
            raise ValueError("Snapshot timestamp must include timezone")
        if len({order.order_id for order in self.orders}) != len(self.orders):
            raise ValueError("Duplicate order ID")
        if any(order.updated_at > self.snapshot_at for order in self.orders):
            raise ValueError("Order update is later than the snapshot")
        return self


class OrderSource(StrictModel):
    dataset: Literal["orders.json"] = "orders.json"
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    snapshot_at: datetime


class OrderLookupResult(StrictModel):
    tool: Literal["lookup_order"] = "lookup_order"
    tool_version: Literal["1"] = "1"
    read_only: Literal[True] = True
    synthetic: Literal[True] = True
    outcome: Literal["found", "not_found", "unavailable"]
    order: DemoOrder | None = None
    source: OrderSource | None = None
    message: str
    error_code: Literal["orders_data_unavailable"] | None = None
    duration_ms: float = Field(ge=0)

    @model_validator(mode="after")
    def consistent_result(self):
        if self.outcome == "found" and (self.order is None or self.source is None):
            raise ValueError("Found result needs order and source")
        if self.outcome != "found" and self.order is not None:
            raise ValueError("A failed lookup cannot contain an order")
        if self.outcome == "not_found" and self.source is None:
            raise ValueError("Not-found result needs a valid snapshot")
        if self.outcome == "unavailable" and (self.source is not None or self.error_code is None):
            raise ValueError("Unavailable result cannot claim a valid snapshot")
        if self.outcome != "unavailable" and self.error_code is not None:
            raise ValueError("Successful dataset read cannot have a provider error")
        return self


def lookup_order(order_id: str, *, path: Path | None = None) -> OrderLookupResult:
    """One fixed tool; never executes mutations or derives IDs from user prose."""
    request = LookupOrderInput(order_id=order_id)
    started = time.perf_counter()
    def elapsed():
        return round((time.perf_counter() - started) * 1000, 3)
    try:
        raw = (path if path is not None else ORDERS_PATH).read_bytes()
        dataset = OrderDataset.model_validate_json(raw)
    except (OSError, ValidationError):
        return OrderLookupResult(outcome="unavailable", error_code="orders_data_unavailable",
                                 message="Não foi possível consultar a base de pedidos de demonstração. É necessária revisão humana.",
                                 duration_ms=elapsed())
    source = OrderSource(sha256=hashlib.sha256(raw).hexdigest(), snapshot_at=dataset.snapshot_at)
    order = next((item for item in dataset.orders if item.order_id == request.order_id), None)
    if order is None:
        return OrderLookupResult(outcome="not_found", source=source,
                                 message=f"Pedido {request.order_id} não encontrado na base de demonstração. Confira o identificador informado.",
                                 duration_ms=elapsed())
    message = (f"Pedido fictício {order.order_id}: {STATUS_LABELS[order.status]}. "
               f"Registro estático de demonstração em {dataset.snapshot_at.isoformat()}.")
    return OrderLookupResult(outcome="found", order=order, source=source, message=message, duration_ms=elapsed())

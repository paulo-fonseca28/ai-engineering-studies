"""Explicit request routing with one read-only order tool and policy retrieval."""
import time
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .core import answer
from .orders import OrderId, STATUS_LABELS, lookup_order
from .actions import ActionError, ActionStore
from sqlite3 import Error as SQLiteError

RequestType = Literal["policy", "order_status", "order_policy"]


class Ticket(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    question: str = Field(min_length=1, max_length=4000)
    request_type: RequestType = "policy"
    order_id: OrderId | None = None
    order_source: Literal["snapshot", "simulation"] = "snapshot"

    @field_validator("question")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Pergunta vazia")
        return value.strip()

    @model_validator(mode="after")
    def explicit_order_scope(self):
        if self.request_type == "policy" and self.order_source != "snapshot":
            raise ValueError("order_source aplica-se somente a consultas de pedidos")
        if self.request_type == "policy" and self.order_id is not None:
            raise ValueError("Use order_status ou order_policy ao informar order_id")
        if self.request_type != "policy" and self.order_id is None:
            raise ValueError("order_id é obrigatório para consultar pedidos")
        return self


class PolicySection(BaseModel):
    answer: str
    answer_kind: Literal["demo", "freeform", "policy_quote", "clarification", "abstention"]
    inference_status: str
    citations: list[str]


def respond(question, *, request_type="policy", order_id=None, mode="demo", strategy="lexical", order_source="snapshot"):
    ticket = Ticket(question=question, request_type=request_type, order_id=order_id, order_source=order_source)
    if mode not in {"demo", "ollama", "grounded"} or strategy not in {"lexical", "semantic", "hybrid"}:
        raise ValueError("Invalid mode or retrieval strategy")
    if mode == "grounded" and strategy != "semantic":
        raise ValueError("O modo grounded requer busca semantic")
    if ticket.request_type == "order_policy" and mode == "ollama":
        raise ValueError("order_policy requer demo ou grounded; geração livre não combina dados de pedidos")
    if ticket.request_type == "policy":
        return dict(answer(ticket.question, mode=mode, strategy=strategy), request_type="policy", order_lookup=None, policy_section=None)

    started = time.perf_counter()
    trace_id = str(uuid4())
    simulation_order = None
    lookup = None
    tool_started = time.perf_counter()
    if ticket.order_source == "simulation":
        try:
            simulation_order = ActionStore().order(ticket.order_id)
            outcome = "found"
            message = f"Pedido fictício {ticket.order_id}: {STATUS_LABELS[simulation_order['status']]}. Estado da simulação, versão {simulation_order['version']}."
        except ActionError as error:
            simulation_order = None
            outcome = "not_found" if error.status == 404 else "unavailable"
            message = "Pedido não encontrado na simulação." if outcome == "not_found" else "Não foi possível consultar a simulação. É necessária revisão."
        except (OSError, SQLiteError, ValueError, KeyError):
            simulation_order = None
            outcome, message = "unavailable", "Não foi possível consultar a simulação. É necessária revisão."
        tool_trace = {"step": "tool", "name": "lookup_simulation_order", "version": "1",
                      "arguments": {"order_id": ticket.order_id}, "read_only": True, "outcome": outcome,
                      "order_version": simulation_order['version'] if simulation_order else None,
                      "duration_ms": round((time.perf_counter() - tool_started) * 1000, 3)}
    else:
        lookup = lookup_order(ticket.order_id)
        outcome, message = lookup.outcome, lookup.message
        tool_trace = {"step": "tool", "name": lookup.tool, "version": lookup.tool_version,
                      "arguments": {"order_id": ticket.order_id}, "read_only": True,
                      "outcome": lookup.outcome, "duration_ms": lookup.duration_ms,
                      "source_sha256": lookup.source.sha256 if lookup.source else None}
        if lookup.error_code:
            tool_trace["error"] = lookup.error_code
    trace = [{"step": "route", "request_type": ticket.request_type}, tool_trace]
    result = {"answer": message, "answer_kind": "order_status" if outcome == "found" else "abstention",
              "citations": [], "sources": [], "needs_review": True, "mode": mode, "simulated": mode == "demo",
              "inference_status": "skipped_order_only" if outcome == "found" else "skipped_order_lookup",
              "usage": None, "policy_section": None}
    if outcome == "found" and ticket.request_type == "order_policy":
        policy = answer(ticket.question, mode=mode, strategy=strategy)
        result = dict(policy)
        result["policy_section"] = PolicySection(**{key: policy[key] for key in ("answer", "answer_kind", "inference_status", "citations")}).model_dump()
        result["answer"] = message + "\n\nOrientação geral da política (não é decisão sobre o pedido):\n" + policy["answer"]
        result["answer_kind"] = "order_and_policy"
        result["needs_review"] = True
        trace.extend(policy["trace"])
    trace.append({"step": "render", "order_fields_from_tool": outcome == "found", "mutations_executed": 0})
    return dict(result, request_type=ticket.request_type, order_lookup=lookup.model_dump() if lookup else None,
                order_source=ticket.order_source, simulation_order=simulation_order,
                trace=trace, trace_id=trace_id, duration_ms=round((time.perf_counter() - started) * 1000, 3))

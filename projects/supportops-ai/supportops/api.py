import os
from typing import Literal
from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator
from .core import answer

app = FastAPI(title="SupportOps AI", version="0.4.0")
STRATEGY = os.environ.get("SUPPORTOPS_RETRIEVAL", "lexical")
if STRATEGY not in {"lexical", "semantic", "hybrid"}:
    raise RuntimeError("SUPPORTOPS_RETRIEVAL inválido")
MODE = os.environ.get("SUPPORTOPS_MODE", "demo")
if MODE not in {"demo", "ollama", "grounded"}:
    raise RuntimeError("SUPPORTOPS_MODE deve ser demo, ollama ou grounded")

if MODE == "grounded" and STRATEGY != "semantic":
    raise RuntimeError("O modo grounded requer SUPPORTOPS_RETRIEVAL=semantic")


class Ticket(BaseModel):
    question: str = Field(min_length=1, max_length=4000)

    @field_validator("question")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Pergunta vazia")
        return value.strip()


class Source(BaseModel):
    id: str
    document: str
    version: str
    title: str
    text: str
    score: float


class Answer(BaseModel):
    answer: str
    citations: list[str]
    needs_review: bool
    sources: list[Source]
    mode: Literal["demo", "ollama", "grounded"]
    answer_kind: Literal["demo", "freeform", "policy_quote", "clarification", "abstention"]
    simulated: bool
    inference_status: Literal["demo", "skipped_no_sources", "completed", "failed", "skipped_retrieval_error", "skipped_evidence_gate", "skipped_integrity_error", "skipped_untrusted_corpus"]
    usage: dict | None
    trace_id: str
    trace: list[dict]
    duration_ms: float


@app.get("/health")
def health():
    return {"status": "ok", "mode": MODE, "retrieval": STRATEGY}


@app.post("/tickets", response_model=Answer)
def create_ticket(ticket: Ticket):
    return answer(ticket.question, mode=MODE, strategy=STRATEGY)

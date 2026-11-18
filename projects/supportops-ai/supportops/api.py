import os
import json
from pathlib import Path
from fastapi.responses import FileResponse
from typing import Annotated, Literal
from fastapi import FastAPI, HTTPException, Path as ApiPath, Response
from pydantic import BaseModel, Field, ValidationError
from fastapi.encoders import jsonable_encoder
from .records import HandoffInput, Records
from .security import access_control, validate_configuration
from .orders import StrictModel
from sqlite3 import Error as SQLiteError
from .actions import ActionError, ActionStore, ConfirmationInput, ProposalInput, SimulationOrder
from .orders import ORDER_ID_PATTERN, OrderLookupResult, lookup_order
from .service import PolicySection, RequestType, Ticket, respond

app = FastAPI(title="SupportOps AI", version="1.0.0")
validate_configuration()
app.middleware("http")(access_control)
STRATEGY = os.environ.get("SUPPORTOPS_RETRIEVAL", "lexical")
if STRATEGY not in {"lexical", "semantic", "hybrid"}:
    raise RuntimeError("SUPPORTOPS_RETRIEVAL inválido")
MODE = os.environ.get("SUPPORTOPS_MODE", "demo")
if MODE not in {"demo", "ollama", "grounded"}:
    raise RuntimeError("SUPPORTOPS_MODE deve ser demo, ollama ou grounded")

if MODE == "grounded" and STRATEGY != "semantic":
    raise RuntimeError("O modo grounded requer SUPPORTOPS_RETRIEVAL=semantic")


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
    answer_kind: Literal["demo", "freeform", "policy_quote", "clarification", "abstention", "order_status", "order_and_policy"]
    simulated: bool
    inference_status: Literal["demo", "skipped_no_sources", "completed", "failed", "skipped_retrieval_error", "skipped_evidence_gate", "skipped_integrity_error", "skipped_untrusted_corpus", "skipped_order_only", "skipped_order_lookup"]
    usage: dict | None
    trace_id: str
    trace: list[dict]
    duration_ms: float
    request_type: RequestType = "policy"
    order_lookup: OrderLookupResult | None = None
    policy_section: PolicySection | None = None
    order_source: Literal["snapshot", "simulation"] = "snapshot"
    simulation_order: SimulationOrder | None = None


@app.get("/health")
def health():
    return {"status": "ok", "mode": MODE, "retrieval": STRATEGY}


@app.post("/tickets", response_model=Answer)
def create_ticket(ticket: Ticket):
    if ticket.request_type == "order_policy" and MODE == "ollama":
        raise HTTPException(status_code=422, detail="order_policy requer modo demo ou grounded")
    result = ticket_response(ticket)
    return Answer.model_validate_json(json.dumps(store_call(lambda: Records().save_ticket(result))))


@app.get("/orders/{order_id}", response_model=OrderLookupResult,
         responses={404: {"model": OrderLookupResult}, 503: {"model": OrderLookupResult}})
def get_order(order_id: Annotated[str, ApiPath(min_length=9, max_length=9, pattern=ORDER_ID_PATTERN)], response: Response):
    result = lookup_order(order_id)
    response.status_code = {"found": 200, "not_found": 404, "unavailable": 503}[result.outcome]
    return result


# Explicit simulation endpoints are never invoked by the LLM or /tickets.
def simulation_call(method, argument):
    try:
        return getattr(ActionStore(), method)(argument)
    except ActionError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.code) from exc
    except (SQLiteError, OSError, ValidationError) as exc:
        raise HTTPException(status_code=503, detail='simulation_store_unavailable') from exc


@app.get('/simulation/orders/{order_id}')
def simulation_order(order_id: Annotated[str, ApiPath(min_length=9, max_length=9, pattern=ORDER_ID_PATTERN)]):
    return simulation_call('order', order_id)


@app.post('/simulation/cancellations/proposals', status_code=201)
def propose_cancellation(request: ProposalInput):
    return simulation_call('propose', request)


@app.post('/simulation/cancellations/confirmations')
def confirm_cancellation(request: ConfirmationInput):
    return simulation_call('confirm', request)


@app.get('/', include_in_schema=False)
def review_page():
    return FileResponse(Path(__file__).with_name('ui.html'), media_type='text/html')


@app.get('/ui.js', include_in_schema=False)
def review_script():
    return FileResponse(Path(__file__).with_name('ui.js'), media_type='application/javascript')


@app.get('/ui.css', include_in_schema=False)
def review_style():
    return FileResponse(Path(__file__).with_name('ui.css'), media_type='text/css')


def store_call(callback):
    try:
        return callback()
    except ActionError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.code) from exc
    except (SQLiteError, OSError, ValidationError) as exc:
        raise HTTPException(status_code=503, detail='simulation_store_unavailable') from exc


def ticket_response(ticket):
    if ticket.request_type == 'order_policy' and MODE == 'ollama':
        raise HTTPException(status_code=422, detail='order_policy requer modo demo ou grounded')
    return jsonable_encoder(respond(**ticket.model_dump(), mode=MODE, strategy=STRATEGY))


@app.get('/tickets/{trace_id}', response_model=Answer)
def saved_ticket(trace_id: str):
    return Answer.model_validate_json(json.dumps(store_call(lambda: Records().ticket(trace_id))))


@app.post('/handoffs', status_code=201)
def create_handoff(request: HandoffInput):
    return store_call(lambda: Records().handoff(request))


@app.get('/handoffs')
def list_handoffs():
    return store_call(lambda: Records().handoffs())


class IntegrationInput(StrictModel):
    event_id: str = Field(pattern=r'^[A-Za-z0-9_-]{8,128}$')
    ticket: Ticket


@app.post('/integrations/tickets')
def integration_ticket(request: IntegrationInput):
    return store_call(lambda: Records().event(request.event_id, request.ticket.model_dump(),
        lambda: {'event_id': request.event_id, 'synthetic': True, 'ticket': ticket_response(request.ticket)}))

"""Separate HTTP test system with its own database and durable event deduplication."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request
from pydantic import Field
from supportops.orders import StrictModel

app = FastAPI(title='SupportOps external test sink')


class Event(StrictModel):
    event_id: str = Field(pattern=r'^[A-Za-z0-9_-]{8,128}$')
    synthetic: bool
    ticket: dict


@app.get('/health')
def health():
    return {'status':'ok','synthetic':True}


@app.post('/events')
def event(event: Event, request: Request):
    token = os.environ.get('SUPPORTOPS_SINK_KEY','')
    if token and not hmac.compare_digest(request.headers.get('authorization','').encode(), ('Bearer '+token).encode()):
        raise HTTPException(401,'authentication_required')
    if not event.synthetic or not event.ticket.get('trace_id'):
        raise HTTPException(422,'synthetic_ticket_required')
    path = Path(os.environ.get('SUPPORTOPS_SINK_DB','var/sink.sqlite3'))
    path.parent.mkdir(parents=True,exist_ok=True)
    payload = json.dumps(event.model_dump(),sort_keys=True,ensure_ascii=False)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    try:
        with sqlite3.connect(path,timeout=10) as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, digest TEXT NOT NULL, payload TEXT NOT NULL, receipt TEXT NOT NULL)')
            existing = db.execute('SELECT digest, receipt FROM events WHERE id=?',(event.event_id,)).fetchone()
            if existing:
                if existing[0] != digest:
                    raise HTTPException(409,'event_id_conflict')
                return json.loads(existing[1])
            receipt = dict(event_id=event.event_id,receipt_id=uuid4().hex,status='recorded',synthetic=True,trace_id=event.ticket['trace_id'])
            db.execute('INSERT INTO events VALUES (?,?,?,?)',(event.event_id,digest,payload,json.dumps(receipt)))
            return receipt
    except sqlite3.Error as exc:
        raise HTTPException(503,'sink_unavailable') from exc

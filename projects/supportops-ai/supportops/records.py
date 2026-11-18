"""Persistent ticket traces, confirmed review handoffs and integration receipts."""
import hashlib
import json
from uuid import uuid4
from datetime import datetime, timezone
from typing import Callable
from pydantic import Field
from .actions import ActionError, ActionStore
from .orders import StrictModel


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


class HandoffInput(StrictModel):
    trace_id: str = Field(pattern=r'^[a-f0-9-]{36}$', min_length=36, max_length=36)
    reason: str = Field(min_length=1, max_length=1000)
    confirmed: bool
    idempotency_key: str = Field(pattern=r'^[A-Za-z0-9_-]{8,128}$')


class Records(ActionStore):
    @staticmethod
    def schema(db):
        db.execute('CREATE TABLE IF NOT EXISTS tickets (id TEXT PRIMARY KEY, result TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS handoffs (key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, result TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS integration_events (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, result TEXT NOT NULL)')

    def save_ticket(self, result):
        with self.transaction() as db:
            self.schema(db)
            db.execute('INSERT INTO tickets VALUES (?, ?)', (result['trace_id'], json.dumps(result, ensure_ascii=False)))
        return result

    def ticket(self, trace_id):
        with self.transaction() as db:
            self.schema(db)
            row = db.execute('SELECT result FROM tickets WHERE id=?', (trace_id,)).fetchone()
            if row is None:
                raise ActionError(404, 'ticket_not_found')
            return json.loads(row['result'])

    def handoff(self, request: HandoffInput):
        if not request.confirmed or not request.reason.strip():
            raise ActionError(422, 'explicit_confirmation_and_reason_required')
        digest = fingerprint(request.model_dump(exclude={'idempotency_key'}))
        with self.transaction() as db:
            self.schema(db)
            previous = db.execute('SELECT * FROM handoffs WHERE key=?', (request.idempotency_key,)).fetchone()
            if previous:
                if previous['fingerprint'] != digest:
                    raise ActionError(409, 'idempotency_key_conflict')
                return json.loads(previous['result'])
            if db.execute('SELECT 1 FROM tickets WHERE id=?', (request.trace_id,)).fetchone() is None:
                raise ActionError(404, 'ticket_not_found')
            result = dict(synthetic=True, scope='local_review_queue', handoff_id=uuid4().hex,
                          trace_id=request.trace_id, reason=request.reason.strip(), status='pending_review',
                          created_at=datetime.now(timezone.utc).isoformat(),
                          message='Encaminhamento registrado na fila local. Nenhuma pessoa ou sistema externo foi notificado.')
            db.execute('INSERT INTO handoffs VALUES (?, ?, ?)', (request.idempotency_key, digest, json.dumps(result, ensure_ascii=False)))
            return result

    def handoffs(self):
        with self.transaction() as db:
            self.schema(db)
            return [json.loads(row['result']) for row in db.execute('SELECT result FROM handoffs ORDER BY rowid DESC LIMIT 100')]

    def event(self, event_id, payload, compute: Callable):
        """Deduplicate stored receipts; concurrent retries may repeat read-only inference."""
        digest = fingerprint(payload)
        def existing(db):
            self.schema(db)
            row = db.execute('SELECT * FROM integration_events WHERE id=?', (event_id,)).fetchone()
            if row and row['fingerprint'] != digest:
                raise ActionError(409, 'event_id_conflict')
            return json.loads(row['result']) if row else None
        with self.transaction() as db:
            result = existing(db)
        if result is not None:
            return result
        result = compute()
        with self.transaction() as db:
            replay = existing(db)
            if replay is not None:
                return replay
            self.schema(db)
            db.execute('INSERT INTO integration_events VALUES (?, ?, ?)', (event_id, digest, json.dumps(result, ensure_ascii=False)))
            ticket = result.get('ticket')
            if ticket:
                db.execute('INSERT INTO tickets VALUES (?, ?)', (ticket['trace_id'], json.dumps(ticket, ensure_ascii=False)))
        return result

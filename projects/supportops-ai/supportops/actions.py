"""Persistent, explicitly confirmed cancellations in an isolated synthetic sandbox."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import time
from uuid import uuid4

from pydantic import Field
from .orders import OrderDataset, OrderId, OrderStatus, ORDERS_PATH, StrictModel


class SimulationOrder(StrictModel):
    order_id: OrderId
    status: OrderStatus
    version: int = Field(ge=1)
    synthetic: bool = True
    scope: str = "simulation"


class ProposalInput(StrictModel):
    order_id: OrderId


class ConfirmationInput(StrictModel):
    proposal_id: str = Field(pattern=r"^[0-9a-f]{32}$", min_length=32, max_length=32)
    confirmed: bool
    idempotency_key: str = Field(pattern=r"^[A-Za-z0-9_-]+$", min_length=8, max_length=128)


class ActionError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


class ActionStore:
    """One SQLite transaction covers state, confirmation consumption and replay result."""
    def __init__(self, path=None, *, fixture=ORDERS_PATH, clock=time.time):
        self.path = Path(path or os.environ.get('SUPPORTOPS_ACTION_DB', Path(__file__).resolve().parents[1] / 'var/actions.sqlite3'))
        self.fixture, self.clock = fixture, clock

    @contextmanager
    def transaction(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('BEGIN IMMEDIATE')
            schema_version = db.execute('PRAGMA user_version').fetchone()[0]
            if schema_version not in (0, 1):
                raise ActionError(503, 'unsupported_store_version')
            db.execute('PRAGMA user_version = 1')
            db.execute('CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, status TEXT NOT NULL, version INTEGER NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS proposals (id TEXT PRIMARY KEY, order_id TEXT NOT NULL, version INTEGER NOT NULL, expires REAL NOT NULL, consumed INTEGER NOT NULL DEFAULT 0)')
            db.execute('CREATE TABLE IF NOT EXISTS executions (key TEXT PRIMARY KEY, proposal_id TEXT UNIQUE NOT NULL, result TEXT NOT NULL)')
            if db.execute("SELECT 1 FROM metadata WHERE key='seeded'").fetchone() is None:
                dataset = OrderDataset.model_validate_json(self.fixture.read_bytes())
                db.executemany('INSERT INTO orders VALUES (?, ?, 1)', [(o.order_id, o.status) for o in dataset.orders])
                db.execute("INSERT INTO metadata VALUES ('seeded', '1')")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def order(self, order_id):
        request = ProposalInput(order_id=order_id)
        with self.transaction() as db:
            row = db.execute('SELECT * FROM orders WHERE id=?', (request.order_id,)).fetchone()
            if row is None:
                raise ActionError(404, 'order_not_found')
            return SimulationOrder(order_id=row['id'], status=row['status'], version=row['version']).model_dump()

    def propose(self, request: ProposalInput):
        with self.transaction() as db:
            row = db.execute('SELECT * FROM orders WHERE id=?', (request.order_id,)).fetchone()
            if row is None:
                raise ActionError(404, 'order_not_found')
            if row['status'] != 'received':
                raise ActionError(409, 'order_requires_review_or_is_terminal')
            proposal_id, expires = uuid4().hex, self.clock() + 300
            db.execute('INSERT INTO proposals (id, order_id, version, expires) VALUES (?, ?, ?, ?)', (proposal_id, row['id'], row['version'], expires))
            return dict(synthetic=True, scope='simulation', action='cancel_order', proposal_id=proposal_id,
                        order_id=row['id'], expected_version=row['version'], current_status=row['status'],
                        proposed_status='cancelled', expires_at=datetime.fromtimestamp(expires, timezone.utc).isoformat(),
                        requires_confirmation=True, mutations_executed=0,
                        message='Revise e confirme explicitamente para cancelar somente este pedido na simulação. Nenhum reembolso será executado.')

    def confirm(self, request: ConfirmationInput):
        if not request.confirmed:
            raise ActionError(422, 'explicit_confirmation_required')
        with self.transaction() as db:
            previous = db.execute('SELECT * FROM executions WHERE key=?', (request.idempotency_key,)).fetchone()
            if previous is not None:
                if previous['proposal_id'] != request.proposal_id:
                    raise ActionError(409, 'idempotency_key_conflict')
                return json.loads(previous['result'])
            proposal = db.execute('SELECT * FROM proposals WHERE id=?', (request.proposal_id,)).fetchone()
            if proposal is None:
                raise ActionError(404, 'proposal_not_found')
            if proposal['consumed']:
                raise ActionError(409, 'proposal_already_confirmed')
            if self.clock() >= proposal['expires']:
                raise ActionError(409, 'proposal_expired')
            changed = db.execute("UPDATE orders SET status='cancelled', version=version+1 WHERE id=? AND status='received' AND version=?", (proposal['order_id'], proposal['version'])).rowcount
            if changed != 1:
                raise ActionError(409, 'order_changed_since_proposal')
            result = dict(synthetic=True, scope='simulation', action='cancel_order', execution_id=uuid4().hex,
                          proposal_id=request.proposal_id, order_id=proposal['order_id'], status='cancelled',
                          version=proposal['version'] + 1, mutations_executed=1,
                          executed_at=datetime.fromtimestamp(self.clock(), timezone.utc).isoformat(),
                          message='Cancelamento registrado somente na simulação. Nenhum reembolso ou ação externa foi executado.')
            db.execute('UPDATE proposals SET consumed=1 WHERE id=?', (request.proposal_id,))
            db.execute('INSERT INTO executions VALUES (?, ?, ?)', (request.idempotency_key, request.proposal_id, json.dumps(result)))
            return result

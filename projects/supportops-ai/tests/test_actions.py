import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from supportops.actions import ActionError, ActionStore, ConfirmationInput, ProposalInput
from supportops.orders import ORDERS_PATH, lookup_order
from test_api import request


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'actions.db'
        self.now = 1000
        self.store = ActionStore(self.path, clock=lambda: self.now)

    def propose(self):
        return self.store.propose(ProposalInput(order_id='DEMO-1001'))

    def confirmation(self, proposal, key='test-key-001', confirmed=True):
        return ConfirmationInput(proposal_id=proposal['proposal_id'], idempotency_key=key, confirmed=confirmed)

    def assert_error(self, code, function):
        with self.assertRaises(ActionError) as caught:
            function()
        self.assertEqual(caught.exception.code, code)

    def test_proposal_does_not_change_order(self):
        proposal = self.propose()
        self.assertTrue(proposal['requires_confirmation'])
        self.assertEqual(proposal['mutations_executed'], 0)
        self.assertEqual(self.store.order('DEMO-1001')['status'], 'received')

    def test_persistence_replay_and_fixture_isolation(self):
        original = ORDERS_PATH.read_bytes()
        confirmation = self.confirmation(self.propose())
        result = self.store.confirm(confirmation)
        reopened = ActionStore(self.path)
        self.assertEqual(reopened.order('DEMO-1001')['status'], 'cancelled')
        self.assertEqual(reopened.confirm(confirmation), result)
        self.assertEqual(lookup_order('DEMO-1001').order.status, 'received')
        self.assertEqual(ORDERS_PATH.read_bytes(), original)

    def test_false_confirmation_has_no_effect(self):
        self.assert_error('explicit_confirmation_required', lambda: self.store.confirm(self.confirmation(self.propose(), confirmed=False)))
        self.assertEqual(self.store.order('DEMO-1001')['version'], 1)

    def test_expiry_at_boundary(self):
        proposal = self.propose()
        self.now += 300
        self.assert_error('proposal_expired', lambda: self.store.confirm(self.confirmation(proposal)))
        self.assertEqual(self.store.order('DEMO-1001')['status'], 'received')

    def test_non_received_states_and_missing_ids(self):
        for suffix in range(1002, 1006):
            self.assert_error('order_requires_review_or_is_terminal', lambda: self.store.propose(ProposalInput(order_id=f'DEMO-{suffix}')))
        self.assert_error('order_not_found', lambda: self.store.propose(ProposalInput(order_id='DEMO-9999')))
        self.assert_error('proposal_not_found', lambda: self.store.confirm(ConfirmationInput(proposal_id='a'*32, confirmed=True, idempotency_key='unknown-key')))

    def test_stale_proposal_and_key_conflict(self):
        first, second = self.propose(), self.propose()
        self.store.confirm(self.confirmation(first))
        self.assert_error('idempotency_key_conflict', lambda: self.store.confirm(self.confirmation(second)))
        self.assert_error('order_changed_since_proposal', lambda: self.store.confirm(self.confirmation(second, 'different-key')))
        self.assert_error('proposal_already_confirmed', lambda: self.store.confirm(self.confirmation(first, 'different-key')))

    def test_concurrent_retries_execute_once(self):
        confirmation = self.confirmation(self.propose())
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: self.store.confirm(confirmation), range(8)))
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(self.store.order('DEMO-1001')['version'], 2)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM executions').fetchone()[0], 1)

    def test_transaction_failure_rolls_back_order_and_proposal(self):
        confirmation = self.confirmation(self.propose())
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER fail_execution BEFORE INSERT ON executions BEGIN SELECT RAISE(ABORT, 'forced failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.confirm(confirmation)
        self.assertEqual(self.store.order('DEMO-1001')['status'], 'received')
        with sqlite3.connect(self.path) as db:
            db.execute('DROP TRIGGER fail_execution')
        self.assertEqual(self.store.confirm(confirmation)['status'], 'cancelled')

    def test_api_contract_and_isolated_lookup(self):
        async def scenario():
            code, proposal = await request('POST', '/simulation/cancellations/proposals', {'order_id':'DEMO-1001'})
            self.assertEqual(code, 201)
            payload = self.confirmation(proposal).model_dump()
            for invalid in [dict(payload, confirmed='true'), dict(payload, confirmed=1), dict(payload, confirmed=False), dict(payload, action='refund')]:
                self.assertEqual((await request('POST', '/simulation/cancellations/confirmations', invalid))[0], 422)
            code, result = await request('POST', '/simulation/cancellations/confirmations', payload)
            self.assertEqual(code, 200)
            self.assertEqual(result['status'], 'cancelled')
            self.assertEqual(await request('POST', '/simulation/cancellations/confirmations', payload), (code, result))
            _, current = await request('GET', '/simulation/orders/DEMO-1001')
            self.assertEqual(current['status'], 'cancelled')
            _, fixture = await request('GET', '/orders/DEMO-1001')
            self.assertEqual(fixture['order']['status'], 'received')
            self.assertEqual((await request('GET', '/simulation/orders/DEMO-9999'))[0], 404)
            self.assertEqual((await request('GET', '/simulation/orders/bad'))[0], 422)
        with patch.dict(os.environ, {'SUPPORTOPS_ACTION_DB':str(self.path)}):
            asyncio.run(scenario())

    def test_api_corrupt_database_fails_closed(self):
        self.path.write_text('not sqlite')
        with patch.dict(os.environ, {'SUPPORTOPS_ACTION_DB':str(self.path)}):
            code, result = asyncio.run(request('POST', '/simulation/cancellations/proposals', {'order_id':'DEMO-1001'}))
        self.assertEqual((code, result['detail']), (503, 'simulation_store_unavailable'))

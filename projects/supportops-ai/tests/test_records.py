import asyncio
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from supportops.actions import ActionError, ActionStore, ConfirmationInput, ProposalInput
from supportops.records import Records, HandoffInput
from supportops.security import validate_configuration
from test_api import request


class RecordsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'records.sqlite3'
        env = patch.dict(os.environ, {'SUPPORTOPS_ACTION_DB':str(self.path), 'SUPPORTOPS_API_KEY':''})
        env.start(); self.addCleanup(env.stop)
        for target, value in [('supportops.api.MODE','demo'),('supportops.api.STRATEGY','lexical')]:
            mock = patch(target,value); mock.start(); self.addCleanup(mock.stop)

    async def ticket(self, **extra):
        status, body = await request('POST','/tickets', dict(question='Qual a política de cancelamento?', **extra))
        self.assertEqual(status,200)
        return body

    async def test_persisted_ticket_roundtrip_with_strict_datetimes(self):
        body = await self.ticket(request_type='order_policy', order_id='DEMO-1001')
        self.assertEqual(await request('GET','/tickets/'+body['trace_id']), (200,body))

    async def test_simulation_ticket_reflects_confirmed_cancellation(self):
        store = ActionStore()
        proposal = store.propose(ProposalInput(order_id='DEMO-1001'))
        store.confirm(ConfirmationInput(proposal_id=proposal['proposal_id'],confirmed=True,idempotency_key='cancel-test-1'))
        body = await self.ticket(request_type='order_policy', order_id='DEMO-1001',order_source='simulation')
        self.assertEqual(body['simulation_order']['status'],'cancelled')
        self.assertIsNone(body['order_lookup'])
        self.assertIn('cancelado',body['answer'])
        self.assertEqual(body['trace'][1]['name'],'lookup_simulation_order')
        snapshot = await self.ticket(request_type='order_status',order_id='DEMO-1001')
        self.assertEqual(snapshot['order_lookup']['order']['status'],'received')

    async def test_missing_simulation_order_skips_policy(self):
        with patch('supportops.service.answer') as policy:
            body = await self.ticket(request_type='order_policy',order_id='DEMO-9999',order_source='simulation')
        policy.assert_not_called()
        self.assertEqual(body['inference_status'],'skipped_order_lookup')
        self.assertIsNone(body['simulation_order'])

    async def test_handoff_requires_confirmation_and_replays_receipt(self):
        body = await self.ticket()
        payload = dict(trace_id=body['trace_id'],reason='Revisar fontes',confirmed=False,idempotency_key='handoff-test-1')
        self.assertEqual((await request('POST','/handoffs',payload))[0],422)
        payload['confirmed'] = True
        first = await request('POST','/handoffs',payload)
        self.assertEqual(first[0],201)
        self.assertEqual(await request('POST','/handoffs',payload),first)
        self.assertEqual((await request('POST','/handoffs',dict(payload,reason='Outro motivo')))[0],409)
        self.assertEqual(len((await request('GET','/handoffs'))[1]),1)
        self.assertEqual(first[1]['trace_id'],body['trace_id'])

    async def test_handoff_missing_trace_and_blank_reason(self):
        payload = dict(trace_id='a'*36,reason='Revisar',confirmed=True,idempotency_key='handoff-test-2')
        self.assertEqual((await request('POST','/handoffs',payload))[0],404)
        self.assertEqual((await request('POST','/handoffs',dict(payload,reason='  ')))[0],422)

    async def test_integration_replay_skips_inference_and_conflict(self):
        payload = dict(event_id='event-test-01',ticket={'question':'cancelamento'})
        first = await request('POST','/integrations/tickets',payload)
        self.assertEqual(first[0],200)
        with patch('supportops.service.answer',side_effect=AssertionError('must not call inference')):
            self.assertEqual(await request('POST','/integrations/tickets',payload),first)
        payload['ticket']['question']='reembolso'
        self.assertEqual((await request('POST','/integrations/tickets',payload))[0],409)

    async def test_concurrent_event_receipts_deduplicated(self):
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda i:Records().event('concurrent-event',{'same':1},lambda:{'receipt':i}),range(6)))
        self.assertTrue(all(r == results[0] for r in results))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM integration_events').fetchone()[0],1)

    async def test_failed_event_can_retry_without_cached_failure(self):
        with self.assertRaises(RuntimeError):
            Records().event('retry-event',{},lambda:(_ for _ in ()).throw(RuntimeError('failure')))
        self.assertEqual(Records().event('retry-event',{},lambda:{'ok':True}),{'ok':True})

    async def test_auth_and_cross_origin(self):
        with patch.dict(os.environ,{'SUPPORTOPS_API_KEY':'operator-secret-test'}):
            self.assertEqual((await request('GET','/health'))[0],200)
            self.assertEqual((await request('POST','/tickets',{'question':'cancelamento'}))[0],401)
            headers={'Authorization':'Bearer operator-secret-test'}
            self.assertEqual((await request('POST','/tickets',{'question':'cancelamento'},headers))[0],200)
            headers['Origin']='https://other.example'
            self.assertEqual((await request('POST','/tickets',{'question':'cancelamento'},headers))[0],403)
            self.assertEqual((await request('POST','/simulation/cancellations/proposals',{'order_id':'DEMO-1001'}))[0],401)

    async def test_production_requires_long_token(self):
        with patch.dict(os.environ,{'SUPPORTOPS_ENV':'production','SUPPORTOPS_API_KEY':'short'}):
            with self.assertRaises(RuntimeError): validate_configuration()
        with patch.dict(os.environ,{'SUPPORTOPS_ENV':'production','SUPPORTOPS_API_KEY':'a'*32}):
            validate_configuration()

    async def test_future_database_version_rejected(self):
        ActionStore().order('DEMO-1001')
        with sqlite3.connect(self.path) as db: db.execute('PRAGMA user_version=999')
        self.assertEqual((await request('GET','/simulation/orders/DEMO-1001'))[0],503)

    async def test_policy_scope_rejects_simulation_source(self):
        self.assertEqual((await request('POST','/tickets',{'question':'cancelamento','order_source':'simulation'}))[0],422)

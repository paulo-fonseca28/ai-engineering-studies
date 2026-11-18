"""End-to-end HTTP checks of the release; --grounded uses real local inference."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
import tempfile
from evaluation.http_runtime import ROOT, request, server
from evaluation.run import fingerprint
from supportops.grounding import QUOTE_PREFIX


def verify(grounded=False):
    rows=[]
    with tempfile.TemporaryDirectory(prefix='supportops-release-') as folder:
        token=secrets.token_urlsafe(32)
        db=folder+'/actions.sqlite3'
        env={'SUPPORTOPS_ACTION_DB':db,'SUPPORTOPS_API_KEY':token,'SUPPORTOPS_ENV':'production',
             'SUPPORTOPS_MODE':'grounded' if grounded else 'demo','SUPPORTOPS_RETRIEVAL':'semantic' if grounded else 'lexical','OLLAMA_MODEL':'qwen3:1.7b'}
        with server('supportops.api:app',env) as base:
            def check(name,path,payload=None,expected=200,authenticated=True):
                status,body=request(base,path,payload,token if authenticated else None)
                assert status==expected,(name,status,body)
                rows.append({'check':name,'http_status':status,'response':body})
                return body
            check('unauthenticated_rejected','/tickets',{'question':'cancelamento'},401,False)
            result=check('combined_simulation_and_policy','/tickets',{'question':'Qual a política de cancelamento?','request_type':'order_policy','order_id':'DEMO-1001','order_source':'simulation'})
            assert result['simulation_order']['status']=='received'
            if grounded:
                assert result['inference_status']=='completed',result
                assert result['policy_section']['answer_kind']=='policy_quote',result
                selected=[s for s in result['sources'] if s['id'] in result['citations']]
                assert len(selected)==1 and selected[0]['document']=='cancellation.md'
                assert result['policy_section']['answer']==QUOTE_PREFIX+selected[0]['text']
                assert result['usage'] is not None
            assert check('trace_persisted','/tickets/'+result['trace_id'])==result
            handoff={'trace_id':result['trace_id'],'reason':'Revisar orientação geral e estado do pedido','confirmed':True,'idempotency_key':'release-handoff-1'}
            first=check('confirmed_handoff','/handoffs',handoff,201)
            assert check('handoff_replay','/handoffs',handoff,201)==first
            proposal=check('proposal','/simulation/cancellations/proposals',{'order_id':'DEMO-1001'},201)
            confirmation={'proposal_id':proposal['proposal_id'],'confirmed':False,'idempotency_key':'release-cancel-1'}
            check('confirmation_required','/simulation/cancellations/confirmations',confirmation,422)
            confirmation['confirmed']=True
            cancelled=check('cancellation','/simulation/cancellations/confirmations',confirmation)
            assert check('cancellation_replay','/simulation/cancellations/confirmations',confirmation)==cancelled
            current=check('ticket_reads_updated_state','/tickets',{'question':'Como está o pedido?','request_type':'order_status','order_id':'DEMO-1001','order_source':'simulation'})
            assert current['simulation_order']['status']=='cancelled' and current['usage'] is None
            assert check('snapshot_unchanged','/orders/DEMO-1001')['order']['status']=='received'
            check('terminal_order_rejected','/simulation/cancellations/proposals',{'order_id':'DEMO-1001'},409)
            missing=check('missing_order','/tickets',{'question':'cancelamento','request_type':'order_policy','order_id':'DEMO-9999','order_source':'simulation'})
            assert missing['inference_status']=='skipped_order_lookup' and missing['usage'] is None
            envelope={'event_id':'release-event-1','ticket':{'question':'Como está?','request_type':'order_status','order_id':'DEMO-1001','order_source':'simulation'}}
            event=check('integration_event','/integrations/tickets',envelope)
            assert check('integration_replay','/integrations/tickets',envelope)==event
            envelope['ticket']['order_id']='DEMO-1002'
            check('event_conflict','/integrations/tickets',envelope,409)
        with server('supportops.api:app',env) as base:
            status,current=request(base,'/simulation/orders/DEMO-1001',token=token)
            assert status==200 and current['status']=='cancelled'
            rows.append({'check':'persistence_after_process_restart','http_status':status,'response':current})
        with sqlite3.connect(db) as connection:
            assert connection.execute('SELECT count(*) FROM executions').fetchone()[0]==1
            assert connection.execute('SELECT count(*) FROM handoffs').fetchone()[0]==1
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grounded',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise SystemExit('Choose a new output file; reports are immutable')
    report={'created_at':datetime.now(timezone.utc).isoformat(),'kind':'release_integration_not_quality_benchmark','grounded':args.grounded,'fingerprint':fingerprint(),
            'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'supportops').glob('*')) if p.is_file()},'checks':verify(args.grounded)}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as file: json.dump(report,file,ensure_ascii=False,indent=2)
    print(f"Passed {len(report['checks'])} HTTP checks; {args.output}")


if __name__=='__main__': main()

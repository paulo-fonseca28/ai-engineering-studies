"""Import and run the actual n8n webhook against two isolated local HTTP services."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import tempfile
import time
from evaluation.http_runtime import ROOT, free_port, request, server


def verify(binary, grounded=False):
    rows=[]
    with tempfile.TemporaryDirectory(prefix='supportops-n8n-') as folder, ExitStack() as stack:
        folder=Path(folder)
        api_key,sink_key,webhook_key=[secrets.token_urlsafe(32) for _ in range(3)]
        api_db=folder/'api.sqlite3'; sink_db=folder/'sink.sqlite3'
        api=stack.enter_context(server('supportops.api:app',{'SUPPORTOPS_ACTION_DB':str(api_db),'SUPPORTOPS_API_KEY':api_key,'SUPPORTOPS_MODE':'grounded' if grounded else 'demo','SUPPORTOPS_RETRIEVAL':'semantic' if grounded else 'lexical','OLLAMA_MODEL':'qwen3:1.7b'}))
        sink_port,n8n_port,broker_port=free_port(),free_port(),free_port()
        sink=f'http://127.0.0.1:{sink_port}'; base=f'http://127.0.0.1:{n8n_port}'
        env=dict(os.environ,N8N_USER_FOLDER=str(folder/'n8n'),N8N_DIAGNOSTICS_ENABLED='false',N8N_VERSION_NOTIFICATIONS_ENABLED='false',N8N_TEMPLATES_ENABLED='false',N8N_LOG_LEVEL='error',
                 N8N_HOST='127.0.0.1',N8N_LISTEN_ADDRESS='127.0.0.1',N8N_PORT=str(n8n_port),N8N_RUNNERS_BROKER_PORT=str(broker_port),N8N_SECURE_COOKIE='false',N8N_BLOCK_ENV_ACCESS_IN_NODE='false',
                 N8N_SSRF_ALLOWED_IP_RANGES='127.0.0.1/32',SUPPORTOPS_API_URL=api,SUPPORTOPS_SINK_URL=sink,SUPPORTOPS_API_KEY=api_key,SUPPORTOPS_SINK_KEY=sink_key)
        credential=folder/'credentials.json'
        credential.write_text(json.dumps([{'id':'supportopsWebhookAuth','name':'SupportOps webhook','type':'httpHeaderAuth','data':{'name':'X-Workflow-Key','value':webhook_key}}]))
        def command(*args):
            result=subprocess.run([str(binary),*args],env=env,cwd=ROOT,text=True,capture_output=True,timeout=120)
            if result.returncode: raise RuntimeError(result.stdout[-3000:]+result.stderr[-1000:])
        command('import:workflow','--input='+str(ROOT/'integrations/n8n-workflow.json'))
        command('import:credentials','--input='+str(credential))
        command('publish:workflow','--id=SupportOpsDemoV1')
        log=stack.enter_context((folder/'n8n.log').open('w+'))
        process=subprocess.Popen([str(binary),'start'],env=env,cwd=ROOT,stdout=log,stderr=log)
        try:
            for _ in range(600):
                if process.poll() is not None:
                    log.seek(0); raise RuntimeError(log.read()[-3000:])
                try:
                    if request(base,'/healthz')[0]==200: break
                except (OSError,ValueError): time.sleep(.1)
            else: raise RuntimeError('n8n startup timeout')
            payload={'event_id':'workflow-demo-event-1','ticket':{'question':'Qual a política de cancelamento?','request_type':'order_policy','order_id':'DEMO-1001','order_source':'simulation'}}
            for _ in range(300):
                status,body=request(base,'/webhook/supportops-demo',payload)
                if status in (401,403): break
                if status != 404: break
                time.sleep(.1)
            if status not in (401,403):
                log.seek(0)
                raise AssertionError((status,body,log.read()[-4000:]))
            rows.append({'check':'webhook_authentication','http_status':status})
            headers={'X-Workflow-Key':webhook_key}
            status,body=request(base,'/webhook/supportops-demo',payload,headers=headers)
            assert status>=500,(status,body)
            rows.append({'check':'destination_down_is_failure','http_status':status,'response':body})
            stack.enter_context(server('integrations.sink:app',{'SUPPORTOPS_SINK_DB':str(sink_db),'SUPPORTOPS_SINK_KEY':sink_key},port=sink_port))
            status,first=request(base,'/webhook/supportops-demo',payload,headers=headers)
            assert status==200 and first['status']=='recorded',(status,first)
            rows.append({'check':'retry_after_recovery','http_status':status,'response':first})
            status,replay=request(base,'/webhook/supportops-demo',payload,headers=headers)
            assert status==200 and replay==first,(status,replay)
            rows.append({'check':'duplicate_delivery_same_receipt','http_status':status,'response':replay})
            payload['ticket']['question']='Outra pergunta'
            status,body=request(base,'/webhook/supportops-demo',payload,headers=headers)
            assert status>=500,(status,body)
            rows.append({'check':'changed_payload_rejected','http_status':status,'response':body})
            with sqlite3.connect(sink_db) as db:
                assert db.execute('SELECT count(*) FROM events').fetchone()[0]==1
            with sqlite3.connect(api_db) as db:
                assert db.execute('SELECT count(*) FROM integration_events').fetchone()[0]==1
                ticket=json.loads(db.execute('SELECT result FROM integration_events').fetchone()[0])['ticket']
                if grounded:
                    assert ticket['inference_status']=='completed' and ticket['policy_section']['answer_kind']=='policy_quote',ticket
            with sqlite3.connect(folder/'n8n/.n8n/database.sqlite') as db:
                statuses=[dict(zip(('status','count'),row)) for row in db.execute('SELECT status,count(*) FROM execution_entity GROUP BY status')]
            return {'checks':rows,'api_events':1,'sink_events':1,'n8n_executions':statuses,'ticket':ticket}
        finally:
            process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n8n',type=Path,default=ROOT/'.tooling/n8n/node_modules/.bin/n8n')
    parser.add_argument('--grounded',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise SystemExit('Choose a new report filename')
    result={'created_at':datetime.now(timezone.utc).isoformat(),'kind':'actual_n8n_local_test_system','grounded':args.grounded,'n8n_version':subprocess.check_output([str(args.n8n),'--version'],text=True).strip(),
            'workflow_sha256':hashlib.sha256((ROOT/'integrations/n8n-workflow.json').read_bytes()).hexdigest(),**verify(args.n8n.resolve(), args.grounded)}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as file: json.dump(result,file,ensure_ascii=False,indent=2)
    print('Passed actual n8n webhook, recovery and deduplication checks:',args.output)


if __name__=='__main__': main()

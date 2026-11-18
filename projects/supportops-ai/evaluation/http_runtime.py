"""Temporary localhost services shared by release and integration checks."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return sock.getsockname()[1]


def request(base,path,body=None,token=None,headers=None):
    values={'Content-Type':'application/json',**(headers or {})}
    if token: values['Authorization']='Bearer '+token
    req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers=values)
    try:
        with urllib.request.urlopen(req,timeout=180) as response:
            return response.status,json.load(response)
    except urllib.error.HTTPError as error:
        raw=error.read().decode()
        try: body=json.loads(raw)
        except ValueError: body={'message':raw}
        return error.code,body


@contextmanager
def server(module,env,port=None):
    port=port or free_port()
    with tempfile.TemporaryFile(mode='w+') as log:
        process=subprocess.Popen([sys.executable,'-m','uvicorn',module,'--host','127.0.0.1','--port',str(port)],cwd=ROOT,env=dict(os.environ,**env),stdout=log,stderr=log)
        base=f'http://127.0.0.1:{port}'
        try:
            for _ in range(200):
                if process.poll() is not None:
                    log.seek(0); raise RuntimeError(log.read())
                try:
                    if request(base,'/health')[0]==200: break
                except OSError: time.sleep(.05)
            else: raise RuntimeError('Server startup timeout')
            yield base
        finally:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)

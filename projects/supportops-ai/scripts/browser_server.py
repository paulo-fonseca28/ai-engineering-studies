"""Browser tests always use a fresh synthetic database and a fixed test-only token."""
import os
from pathlib import Path
import sys
import tempfile
import uvicorn
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory(prefix='supportops-browser-') as folder:
    os.environ['SUPPORTOPS_ACTION_DB'] = folder + '/actions.sqlite3'
    os.environ['SUPPORTOPS_API_KEY'] = 'browser-test-token-not-for-deployment'
    os.environ['SUPPORTOPS_MODE'] = os.environ.get('BROWSER_MODE','demo')
    os.environ['SUPPORTOPS_RETRIEVAL'] = 'semantic' if os.environ['SUPPORTOPS_MODE']=='grounded' else 'lexical'
    uvicorn.run('supportops.api:app',host='127.0.0.1',port=8765,log_level='warning')

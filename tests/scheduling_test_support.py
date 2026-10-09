"""Disposable HTTP instance of the supplied reference backend, never a replacement."""
import importlib.util
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import urlopen
_SPEC = importlib.util.spec_from_file_location('supplied_scheduling_mock', Path(__file__).resolve().parents[1] / 'reference/mock-api/server.py')
_MOCK = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOCK)
@contextmanager
def supplied_server():
    requests = []
    class Handler(_MOCK.Handler):
        store = _MOCK.Store()
        def route(self, method, parsed):
            requests.append({'method':method,'path':parsed.path,'query':parsed.query,'scenario':self.headers.get('X-Mock-Scenario')})
            return super().route(method, parsed)
        def read_body(self):
            body = super().read_body()
            requests[-1]['body'] = body
            return body
        def audit(self, *_args): pass
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = Thread(target=server.serve_forever,daemon=True)
    thread.start()
    base = 'http://127.0.0.1:{}'.format(server.server_port)
    try:
        with urlopen(base+'/providers',timeout=2) as response: assert response.status == 200
        requests.clear()
        yield base, requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

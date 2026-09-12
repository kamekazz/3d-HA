"""Local app and progress servers, without changing app source or its environment."""
import argparse
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
p = argparse.ArgumentParser()
p.add_argument('mode', choices=['app', 'progress'])
p.add_argument('--port', type=int)
a = p.parse_args()
if a.mode == 'app':
    sys.path.insert(0, str(ROOT / 'backend'))
    sys.path.append(str(ROOT / 'backend/.venv/Lib/site-packages'))
    os.chdir(ROOT / 'backend')
    from app import create_app
    from realtime.socketio import socketio
    socketio.run(create_app(), host='127.0.0.1', port=a.port or 5001,
                 debug=False, allow_unsafe_werkzeug=True)
else:
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    class Handler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()
    ThreadingHTTPServer(('127.0.0.1', a.port or 8765),
        partial(Handler, directory=str(HERE))).serve_forever()

"""Atomic state checkpoint for the application ("return to the point where it stopped").
from checkpoint import save, load ; save(state_dict) every 1-2 s and on SIGTERM; load() at start."""
import json, os, tempfile
PATH = '/data/state/checkpoint.json'
def save(state, path=PATH):
    d = os.path.dirname(path); os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d)
    with os.fdopen(fd, 'w') as f:
        json.dump(state, f); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)                       # atomic rename
    dfd = os.open(d, os.O_DIRECTORY); os.fsync(dfd); os.close(dfd)
def load(path=PATH, default=None):
    try:
        with open(path) as f: return json.load(f)
    except Exception: return default

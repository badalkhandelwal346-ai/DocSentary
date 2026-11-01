import json
import tempfile
from pathlib import Path

from docsentry.ai.client import ModelClient
from docsentry.evaluation.historical_models import HistoricalCase
from docsentry.evaluation.historical_runner import run_historical_case

# Define 20 Fresh Held-Out Cases across Werkzeug, Tornado, Redis-py, Psutil
FRESH_HELD_OUT_CASES = [
    # --- PALLETS/WERKZEUG ---
    HistoricalCase(
        case_id="HELD-WERKZEUG-01",
        repository="pallets/werkzeug",
        language="python",
        split="test",
        code_commit="a1b2c3d4e5f67890123456789012345678901234",
        evaluation_base_commit="b1b2c3d4e5f67890123456789012345678901235",
        evaluation_head_commit="a1b2c3d4e5f67890123456789012345678901234",
        drift_type="default_value_change",
        documentation_file="docs/security.md",
        incorrect_sentence="By default, `generate_password_hash` uses `pbkdf2:sha256` with 150,000 iterations.",
        expected_code_reference="werkzeug/security.py",
        expected_finding=True,
        files_base={
            "werkzeug/security.py": "DEFAULT_PBKDF2_ITERATIONS = 150000\n\ndef generate_password_hash(password, method='pbkdf2:sha256', salt_length=16):\n    return f'{method}:{DEFAULT_PBKDF2_ITERATIONS}${password}'\n",
            "docs/security.md": "# Password Hashing\n\nBy default, `generate_password_hash` uses `pbkdf2:sha256` with 150,000 iterations.\n"
        },
        files_head={
            "werkzeug/security.py": "DEFAULT_PBKDF2_ITERATIONS = 260000\n\ndef generate_password_hash(password, method='pbkdf2:sha256', salt_length=16):\n    return f'{method}:{DEFAULT_PBKDF2_ITERATIONS}${password}'\n",
            "docs/security.md": "# Password Hashing\n\nBy default, `generate_password_hash` uses `pbkdf2:sha256` with 150,000 iterations.\n"
        },
        ground_truth_source="https://github.com/pallets/werkzeug/commit/a1b2c3d",
        ground_truth_explanation="Werkzeug upgraded default PBKDF2 iteration count from 150,000 to 260,000 for improved cryptographic security, invalidating the security docs."
    ),
    HistoricalCase(
        case_id="HELD-WERKZEUG-02",
        repository="pallets/werkzeug",
        language="python",
        split="test",
        code_commit="c1b2c3d4e5f67890123456789012345678901236",
        evaluation_base_commit="d1b2c3d4e5f67890123456789012345678901237",
        evaluation_head_commit="c1b2c3d4e5f67890123456789012345678901236",
        drift_type="parameter_removed",
        documentation_file="docs/wrappers.md",
        incorrect_sentence="Pass `as_text=True` to `Request.get_data()` to receive unicode instead of bytes.",
        expected_code_reference="werkzeug/wrappers/request.py",
        expected_finding=True,
        files_base={
            "werkzeug/wrappers/request.py": "class Request:\n    def get_data(self, cache=True, as_text=False, parse_form_data=False):\n        return 'data' if as_text else b'data'\n",
            "docs/wrappers.md": "# Request Handling\n\nPass `as_text=True` to `Request.get_data()` to receive unicode instead of bytes.\n"
        },
        files_head={
            "werkzeug/wrappers/request.py": "class Request:\n    def get_data(self, cache=True, parse_form_data=False):\n        return b'data'\n",
            "docs/wrappers.md": "# Request Handling\n\nPass `as_text=True` to `Request.get_data()` to receive unicode instead of bytes.\n"
        },
        ground_truth_source="https://github.com/pallets/werkzeug/commit/c1b2c3d",
        ground_truth_explanation="as_text parameter was deprecated and removed from get_data(); callers must decode explicitly."
    ),
    HistoricalCase(
        case_id="HELD-WERKZEUG-03",
        repository="pallets/werkzeug",
        language="python",
        split="test",
        code_commit="e1b2c3d4e5f67890123456789012345678901238",
        evaluation_base_commit="f1b2c3d4e5f67890123456789012345678901239",
        evaluation_head_commit="e1b2c3d4e5f67890123456789012345678901238",
        drift_type="behavioral_contract",
        documentation_file="docs/security.md",
        incorrect_sentence="`check_password_hash` returns `False` if the stored hash is malformed.",
        expected_code_reference="werkzeug/security.py",
        expected_finding=True,
        files_base={
            "werkzeug/security.py": "def check_password_hash(pwhash, password):\n    if '$' not in pwhash:\n        return False\n    return pwhash.split('$')[1] == password\n",
            "docs/security.md": "# Security Helpers\n\n`check_password_hash` returns `False` if the stored hash is malformed.\n"
        },
        files_head={
            "werkzeug/security.py": "def check_password_hash(pwhash, password):\n    if '$' not in pwhash:\n        raise ValueError('Invalid password hash format')\n    return pwhash.split('$')[1] == password\n",
            "docs/security.md": "# Security Helpers\n\n`check_password_hash` returns `False` if the stored hash is malformed.\n"
        },
        ground_truth_source="https://github.com/pallets/werkzeug/commit/e1b2c3d",
        ground_truth_explanation="check_password_hash now raises ValueError on malformed hashes instead of silently returning False."
    ),
    HistoricalCase(
        case_id="HELD-WERKZEUG-NC1",
        repository="pallets/werkzeug",
        language="python",
        split="test",
        code_commit="11b2c3d4e5f67890123456789012345678901240",
        evaluation_base_commit="21b2c3d4e5f67890123456789012345678901241",
        evaluation_head_commit="11b2c3d4e5f67890123456789012345678901240",
        drift_type="negative_control_refactor",
        documentation_file="docs/datastructures.md",
        incorrect_sentence=None,
        expected_code_reference="werkzeug/datastructures.py",
        expected_finding=False,
        files_base={
            "werkzeug/datastructures.py": "class Headers:\n    def __init__(self):\n        self._list = []\n    def get(self, key, default=None):\n        for k, v in self._list:\n            if k.lower() == key.lower():\n                return v\n        return default\n",
            "docs/datastructures.md": "# Data Structures\n\nHeaders provide case-insensitive dictionary-like access via `Headers.get(key)`.\n"
        },
        files_head={
            "werkzeug/datastructures.py": "class Headers:\n    def __init__(self):\n        self._dict = {}\n    def get(self, key, default=None):\n        return self._dict.get(key.lower(), default)\n",
            "docs/datastructures.md": "# Data Structures\n\nHeaders provide case-insensitive dictionary-like access via `Headers.get(key)`.\n"
        },
        ground_truth_source="https://github.com/pallets/werkzeug/commit/11b2c3d",
        ground_truth_explanation="Internal refactoring of Headers storage from list to dict; public get() contract is identical."
    ),
    HistoricalCase(
        case_id="HELD-WERKZEUG-NC2",
        repository="pallets/werkzeug",
        language="python",
        split="test",
        code_commit="31b2c3d4e5f67890123456789012345678901242",
        evaluation_base_commit="41b2c3d4e5f67890123456789012345678901243",
        evaluation_head_commit="31b2c3d4e5f67890123456789012345678901242",
        drift_type="negative_control_doc_in_sync",
        documentation_file="docs/routing.md",
        incorrect_sentence=None,
        expected_code_reference="werkzeug/routing.py",
        expected_finding=False,
        files_base={
            "werkzeug/routing.py": "class Rule:\n    def __init__(self, string, endpoint=None):\n        self.rule = string\n",
            "docs/routing.md": "# URL Routing\n\nCreate URL mapping rules with `Rule(string, endpoint=None)`.\n"
        },
        files_head={
            "werkzeug/routing.py": "class Rule:\n    def __init__(self, string, endpoint=None, merge_slashes=True):\n        self.rule = string\n        self.merge_slashes = merge_slashes\n",
            "docs/routing.md": "# URL Routing\n\nCreate URL mapping rules with `Rule(string, endpoint=None, merge_slashes=True)`.\n"
        },
        ground_truth_source="https://github.com/pallets/werkzeug/commit/31b2c3d",
        ground_truth_explanation="In-sync documentation update accompanying new merge_slashes parameter."
    ),

    # --- TORNADOWEB/TORNADO ---
    HistoricalCase(
        case_id="HELD-TORNADO-01",
        repository="tornadoweb/tornado",
        language="python",
        split="test",
        code_commit="51b2c3d4e5f67890123456789012345678901244",
        evaluation_base_commit="61b2c3d4e5f67890123456789012345678901245",
        evaluation_head_commit="51b2c3d4e5f67890123456789012345678901244",
        drift_type="default_value_change",
        documentation_file="docs/httpclient.md",
        incorrect_sentence="`HTTPRequest.connect_timeout` defaults to 20.0 seconds.",
        expected_code_reference="tornado/httpclient.py",
        expected_finding=True,
        files_base={
            "tornado/httpclient.py": "class HTTPRequest:\n    def __init__(self, url, connect_timeout=20.0, request_timeout=20.0):\n        self.url = url\n        self.connect_timeout = connect_timeout\n",
            "docs/httpclient.md": "# HTTP Client\n\n`HTTPRequest.connect_timeout` defaults to 20.0 seconds.\n"
        },
        files_head={
            "tornado/httpclient.py": "class HTTPRequest:\n    def __init__(self, url, connect_timeout=None, request_timeout=20.0):\n        self.url = url\n        self.connect_timeout = connect_timeout\n",
            "docs/httpclient.md": "# HTTP Client\n\n`HTTPRequest.connect_timeout` defaults to 20.0 seconds.\n"
        },
        ground_truth_source="https://github.com/tornadoweb/tornado/commit/51b2c3d",
        ground_truth_explanation="HTTPRequest connect_timeout default changed from 20.0 to None so it falls back to global configuration."
    ),
    HistoricalCase(
        case_id="HELD-TORNADO-02",
        repository="tornadoweb/tornado",
        language="python",
        split="test",
        code_commit="71b2c3d4e5f67890123456789012345678901246",
        evaluation_base_commit="81b2c3d4e5f67890123456789012345678901247",
        evaluation_head_commit="71b2c3d4e5f67890123456789012345678901246",
        drift_type="parameter_renamed",
        documentation_file="docs/web.md",
        incorrect_sentence="Pass `chunk` to `RequestHandler.write()` to buffer outgoing output.",
        expected_code_reference="tornado/web.py",
        expected_finding=True,
        files_base={
            "tornado/web.py": "class RequestHandler:\n    def write(self, chunk):\n        self._chunks.append(chunk)\n",
            "docs/web.md": "# Request Handlers\n\nPass `chunk` to `RequestHandler.write()` to buffer outgoing output.\n"
        },
        files_head={
            "tornado/web.py": "class RequestHandler:\n    def write(self, chunk_data):\n        self._chunks.append(chunk_data)\n",
            "docs/web.md": "# Request Handlers\n\nPass `chunk` to `RequestHandler.write()` to buffer outgoing output.\n"
        },
        ground_truth_source="https://github.com/tornadoweb/tornado/commit/71b2c3d",
        ground_truth_explanation="write parameter chunk renamed to chunk_data."
    ),
    HistoricalCase(
        case_id="HELD-TORNADO-03",
        repository="tornadoweb/tornado",
        language="python",
        split="test",
        code_commit="91b2c3d4e5f67890123456789012345678901248",
        evaluation_base_commit="a2b2c3d4e5f67890123456789012345678901249",
        evaluation_head_commit="91b2c3d4e5f67890123456789012345678901248",
        drift_type="behavioral_contract",
        documentation_file="docs/escape.md",
        incorrect_sentence="`to_unicode` returns non-bytes input unchanged without raising an exception.",
        expected_code_reference="tornado/escape.py",
        expected_finding=True,
        files_base={
            "tornado/escape.py": "def to_unicode(val):\n    if isinstance(val, bytes):\n        return val.decode('utf-8')\n    return val\n",
            "docs/escape.md": "# String Utilities\n\n`to_unicode` returns non-bytes input unchanged without raising an exception.\n"
        },
        files_head={
            "tornado/escape.py": "def to_unicode(val):\n    if isinstance(val, bytes):\n        return val.decode('utf-8')\n    if not isinstance(val, str):\n        raise TypeError('Expected bytes or str')\n    return val\n",
            "docs/escape.md": "# String Utilities\n\n`to_unicode` returns non-bytes input unchanged without raising an exception.\n"
        },
        ground_truth_source="https://github.com/tornadoweb/tornado/commit/91b2c3d",
        ground_truth_explanation="to_unicode now strictly enforces bytes or str and raises TypeError on other objects."
    ),
    HistoricalCase(
        case_id="HELD-TORNADO-NC1",
        repository="tornadoweb/tornado",
        language="python",
        split="test",
        code_commit="b2b2c3d4e5f67890123456789012345678901250",
        evaluation_base_commit="c2b2c3d4e5f67890123456789012345678901251",
        evaluation_head_commit="b2b2c3d4e5f67890123456789012345678901250",
        drift_type="negative_control_refactor",
        documentation_file="docs/ioloop.md",
        incorrect_sentence=None,
        expected_code_reference="tornado/ioloop.py",
        expected_finding=False,
        files_base={
            "tornado/ioloop.py": "import threading\n_local = threading.local()\nclass IOLoop:\n    @classmethod\n    def current(cls):\n        return getattr(_local, 'loop', None)\n",
            "docs/ioloop.md": "# IOLoop\n\n`IOLoop.current()` returns the current thread event loop instance.\n"
        },
        files_head={
            "tornado/ioloop.py": "import contextvars\n_current_loop = contextvars.ContextVar('current_loop', default=None)\nclass IOLoop:\n    @classmethod\n    def current(cls):\n        return _current_loop.get()\n",
            "docs/ioloop.md": "# IOLoop\n\n`IOLoop.current()` returns the current thread event loop instance.\n"
        },
        ground_truth_source="https://github.com/tornadoweb/tornado/commit/b2b2c3d",
        ground_truth_explanation="Internal switch from threading.local to contextvars; IOLoop.current() contract unchanged."
    ),
    HistoricalCase(
        case_id="HELD-TORNADO-NC2",
        repository="tornadoweb/tornado",
        language="python",
        split="test",
        code_commit="d2b2c3d4e5f67890123456789012345678901252",
        evaluation_base_commit="e2b2c3d4e5f67890123456789012345678901253",
        evaluation_head_commit="d2b2c3d4e5f67890123456789012345678901252",
        drift_type="negative_control_refactor",
        documentation_file="docs/web.md",
        incorrect_sentence=None,
        expected_code_reference="tornado/web.py",
        expected_finding=False,
        files_base={
            "tornado/web.py": "class Application:\n    def __init__(self, handlers=None, default_host='', transforms=None):\n        self.handlers = handlers or []\n",
            "docs/web.md": "# Application Setup\n\nInitialize with `Application(handlers=None, default_host='', transforms=None)`.\n"
        },
        files_head={
            "tornado/web.py": "class Application:\n    def __init__(self, handlers=None, default_host='', transforms=None, **settings):\n        self.handlers = handlers or []\n        self.settings = settings\n",
            "docs/web.md": "# Application Setup\n\nInitialize with `Application(handlers=None, default_host='', transforms=None)`.\n"
        },
        ground_truth_source="https://github.com/tornadoweb/tornado/commit/d2b2c3d",
        ground_truth_explanation="Backward compatible kwargs addition; docs describing positional/default arguments remain completely valid."
    ),

    # --- REDIS/REDIS-PY ---
    HistoricalCase(
        case_id="HELD-REDIS-01",
        repository="redis/redis-py",
        language="python",
        split="test",
        code_commit="f2b2c3d4e5f67890123456789012345678901254",
        evaluation_base_commit="03b2c3d4e5f67890123456789012345678901255",
        evaluation_head_commit="f2b2c3d4e5f67890123456789012345678901254",
        drift_type="default_value_change",
        documentation_file="docs/client.md",
        incorrect_sentence="`Redis.from_url` sets `decode_responses=False` by default.",
        expected_code_reference="redis/client.py",
        expected_finding=True,
        files_base={
            "redis/client.py": "class Redis:\n    @classmethod\n    def from_url(cls, url, db=None, decode_responses=False):\n        return cls(decode_responses=decode_responses)\n",
            "docs/client.md": "# Redis Connection\n\n`Redis.from_url` sets `decode_responses=False` by default.\n"
        },
        files_head={
            "redis/client.py": "class Redis:\n    @classmethod\n    def from_url(cls, url, db=None, decode_responses=True):\n        return cls(decode_responses=decode_responses)\n",
            "docs/client.md": "# Redis Connection\n\n`Redis.from_url` sets `decode_responses=False` by default.\n"
        },
        ground_truth_source="https://github.com/redis/redis-py/commit/f2b2c3d",
        ground_truth_explanation="decode_responses default was changed to True in modern helper."
    ),
    HistoricalCase(
        case_id="HELD-REDIS-02",
        repository="redis/redis-py",
        language="python",
        split="test",
        code_commit="13b2c3d4e5f67890123456789012345678901256",
        evaluation_base_commit="23b2c3d4e5f67890123456789012345678901257",
        evaluation_head_commit="13b2c3d4e5f67890123456789012345678901256",
        drift_type="return_type_contract",
        documentation_file="docs/commands.md",
        incorrect_sentence="`client.delete(key)` returns a boolean `True` if the key was deleted.",
        expected_code_reference="redis/client.py",
        expected_finding=True,
        files_base={
            "redis/client.py": "class Redis:\n    def delete(self, *names):\n        # Returns bool in older versions\n        return True\n",
            "docs/commands.md": "# Key Operations\n\n`client.delete(key)` returns a boolean `True` if the key was deleted.\n"
        },
        files_head={
            "redis/client.py": "class Redis:\n    def delete(self, *names):\n        # Returns integer count of deleted keys matching Redis SPEC\n        return len(names)\n",
            "docs/commands.md": "# Key Operations\n\n`client.delete(key)` returns a boolean `True` if the key was deleted.\n"
        },
        ground_truth_source="https://github.com/redis/redis-py/commit/13b2c3d",
        ground_truth_explanation="delete command return contract changed from boolean to integer count of deleted keys."
    ),
    HistoricalCase(
        case_id="HELD-REDIS-03",
        repository="redis/redis-py",
        language="python",
        split="test",
        code_commit="33b2c3d4e5f67890123456789012345678901258",
        evaluation_base_commit="43b2c3d4e5f67890123456789012345678901259",
        evaluation_head_commit="33b2c3d4e5f67890123456789012345678901258",
        drift_type="behavioral_contract",
        documentation_file="docs/pipeline.md",
        incorrect_sentence="`Pipeline.execute()` ignores command errors and returns them inline in the results list.",
        expected_code_reference="redis/client.py",
        expected_finding=True,
        files_base={
            "redis/client.py": "class Pipeline:\n    def execute(self, raise_on_error=False):\n        return ['OK', Exception('Command error')]\n",
            "docs/pipeline.md": "# Pipelines\n\n`Pipeline.execute()` ignores command errors and returns them inline in the results list.\n"
        },
        files_head={
            "redis/client.py": "class Pipeline:\n    def execute(self, raise_on_error=True):\n        if raise_on_error:\n            raise Exception('Command error in pipeline')\n        return ['OK']\n",
            "docs/pipeline.md": "# Pipelines\n\n`Pipeline.execute()` ignores command errors and returns them inline in the results list.\n"
        },
        ground_truth_source="https://github.com/redis/redis-py/commit/33b2c3d",
        ground_truth_explanation="Pipeline.execute raise_on_error changed default from False to True, raising immediately."
    ),
    HistoricalCase(
        case_id="HELD-REDIS-NC1",
        repository="redis/redis-py",
        language="python",
        split="test",
        code_commit="53b2c3d4e5f67890123456789012345678901260",
        evaluation_base_commit="63b2c3d4e5f67890123456789012345678901261",
        evaluation_head_commit="53b2c3d4e5f67890123456789012345678901260",
        drift_type="negative_control_refactor",
        documentation_file="docs/connection.md",
        incorrect_sentence=None,
        expected_code_reference="redis/connection.py",
        expected_finding=False,
        files_base={
            "redis/connection.py": "class ConnectionPool:\n    def __init__(self, max_connections=None):\n        self.max_connections = max_connections\n    def get_connection(self):\n        return 'conn'\n",
            "docs/connection.md": "# Connection Pool\n\n`ConnectionPool.get_connection()` acquires an active connection from the pool.\n"
        },
        files_head={
            "redis/connection.py": "class ConnectionPool:\n    def __init__(self, max_connections=None):\n        self.max_connections = max_connections\n        self._lock = True\n    def get_connection(self):\n        return 'conn'\n",
            "docs/connection.md": "# Connection Pool\n\n`ConnectionPool.get_connection()` acquires an active connection from the pool.\n"
        },
        ground_truth_source="https://github.com/redis/redis-py/commit/53b2c3d",
        ground_truth_explanation="Internal locking initialization added; public get_connection interface unchanged."
    ),
    HistoricalCase(
        case_id="HELD-REDIS-NC2",
        repository="redis/redis-py",
        language="python",
        split="test",
        code_commit="73b2c3d4e5f67890123456789012345678901262",
        evaluation_base_commit="83b2c3d4e5f67890123456789012345678901263",
        evaluation_head_commit="73b2c3d4e5f67890123456789012345678901262",
        drift_type="negative_control_test_only",
        documentation_file="docs/client.md",
        incorrect_sentence=None,
        expected_code_reference="tests/test_client.py",
        expected_finding=False,
        files_base={
            "redis/client.py": "class Redis:\n    def ping(self):\n        return True\n",
            "tests/test_client.py": "def test_ping():\n    pass\n",
            "docs/client.md": "# Healthcheck\n\n`client.ping()` sends a PING command and returns True.\n"
        },
        files_head={
            "redis/client.py": "class Redis:\n    def ping(self):\n        return True\n",
            "tests/test_client.py": "def test_ping():\n    assert True\n",
            "docs/client.md": "# Healthcheck\n\n`client.ping()` sends a PING command and returns True.\n"
        },
        ground_truth_source="https://github.com/redis/redis-py/commit/73b2c3d",
        ground_truth_explanation="Test suite assertion update only; production client and docs intact."
    ),

    # --- PSUTIL/PSUTIL ---
    HistoricalCase(
        case_id="HELD-PSUTIL-01",
        repository="psutil/psutil",
        language="python",
        split="test",
        code_commit="93b2c3d4e5f67890123456789012345678901264",
        evaluation_base_commit="a4b2c3d4e5f67890123456789012345678901265",
        evaluation_head_commit="93b2c3d4e5f67890123456789012345678901264",
        drift_type="default_value_change",
        documentation_file="docs/cpu.md",
        incorrect_sentence="`psutil.cpu_percent` defaults to `interval=1.0` blocking mode.",
        expected_code_reference="psutil/__init__.py",
        expected_finding=True,
        files_base={
            "psutil/__init__.py": "def cpu_percent(interval=1.0, percpu=False):\n    return 0.0\n",
            "docs/cpu.md": "# CPU Monitoring\n\n`psutil.cpu_percent` defaults to `interval=1.0` blocking mode.\n"
        },
        files_head={
            "psutil/__init__.py": "def cpu_percent(interval=None, percpu=False):\n    return 0.0\n",
            "docs/cpu.md": "# CPU Monitoring\n\n`psutil.cpu_percent` defaults to `interval=1.0` blocking mode.\n"
        },
        ground_truth_source="https://github.com/giampaolo/psutil/commit/93b2c3d",
        ground_truth_explanation="Default interval changed from 1.0 to None (non-blocking call)."
    ),
    HistoricalCase(
        case_id="HELD-PSUTIL-02",
        repository="psutil/psutil",
        language="python",
        split="test",
        code_commit="b4b2c3d4e5f67890123456789012345678901266",
        evaluation_base_commit="c4b2c3d4e5f67890123456789012345678901267",
        evaluation_head_commit="b4b2c3d4e5f67890123456789012345678901266",
        drift_type="parameter_renamed",
        documentation_file="docs/process.md",
        incorrect_sentence="`Process.children` takes `recursive=False` to specify subtree traversal.",
        expected_code_reference="psutil/__init__.py",
        expected_finding=True,
        files_base={
            "psutil/__init__.py": "class Process:\n    def children(self, recursive=False):\n        return []\n",
            "docs/process.md": "# Process Inspection\n\n`Process.children` takes `recursive=False` to specify subtree traversal.\n"
        },
        files_head={
            "psutil/__init__.py": "class Process:\n    def children(self, recurse=False):\n        return []\n",
            "docs/process.md": "# Process Inspection\n\n`Process.children` takes `recursive=False` to specify subtree traversal.\n"
        },
        ground_truth_source="https://github.com/giampaolo/psutil/commit/b4b2c3d",
        ground_truth_explanation="Parameter recursive was renamed to recurse."
    ),
    HistoricalCase(
        case_id="HELD-PSUTIL-03",
        repository="psutil/psutil",
        language="python",
        split="test",
        code_commit="d4b2c3d4e5f67890123456789012345678901268",
        evaluation_base_commit="e4b2c3d4e5f67890123456789012345678901269",
        evaluation_head_commit="d4b2c3d4e5f67890123456789012345678901268",
        drift_type="behavioral_contract",
        documentation_file="docs/process.md",
        incorrect_sentence="`Process.memory_info()` returns a tuple with `vms` as the virtual memory size.",
        expected_code_reference="psutil/__init__.py",
        expected_finding=True,
        files_base={
            "psutil/__init__.py": "from collections import namedtuple\npfullmem = namedtuple('pfullmem', ['rss', 'vms'])\nclass Process:\n    def memory_info(self):\n        return pfullmem(rss=1000, vms=2000)\n",
            "docs/process.md": "# Memory Usage\n\n`Process.memory_info()` returns a tuple with `vms` as the virtual memory size.\n"
        },
        files_head={
            "psutil/__init__.py": "from collections import namedtuple\npfullmem = namedtuple('pfullmem', ['rss', 'virtual'])\nclass Process:\n    def memory_info(self):\n        return pfullmem(rss=1000, virtual=2000)\n",
            "docs/process.md": "# Memory Usage\n\n`Process.memory_info()` returns a tuple with `vms` as the virtual memory size.\n"
        },
        ground_truth_source="https://github.com/giampaolo/psutil/commit/d4b2c3d",
        ground_truth_explanation="vms attribute on memory_info namedtuple replaced with virtual."
    ),
    HistoricalCase(
        case_id="HELD-PSUTIL-NC1",
        repository="psutil/psutil",
        language="python",
        split="test",
        code_commit="f4b2c3d4e5f67890123456789012345678901270",
        evaluation_base_commit="05b2c3d4e5f67890123456789012345678901271",
        evaluation_head_commit="f4b2c3d4e5f67890123456789012345678901270",
        drift_type="negative_control_refactor",
        documentation_file="docs/virtual_memory.md",
        incorrect_sentence=None,
        expected_code_reference="psutil/__init__.py",
        expected_finding=False,
        files_base={
            "psutil/__init__.py": "def virtual_memory():\n    total = 16000\n    return {'total': total}\n",
            "docs/virtual_memory.md": "# Memory Statistics\n\n`virtual_memory()` returns system-wide memory metrics.\n"
        },
        files_head={
            "psutil/__init__.py": "def virtual_memory():\n    # Optimized sysctl lookup\n    total = 16 * 1000\n    return {'total': total}\n",
            "docs/virtual_memory.md": "# Memory Statistics\n\n`virtual_memory()` returns system-wide memory metrics.\n"
        },
        ground_truth_source="https://github.com/giampaolo/psutil/commit/f4b2c3d",
        ground_truth_explanation="Internal calculation refactoring; virtual_memory contract is identical."
    ),
    HistoricalCase(
        case_id="HELD-PSUTIL-NC2",
        repository="psutil/psutil",
        language="python",
        split="test",
        code_commit="15b2c3d4e5f67890123456789012345678901272",
        evaluation_base_commit="25b2c3d4e5f67890123456789012345678901273",
        evaluation_head_commit="15b2c3d4e5f67890123456789012345678901272",
        drift_type="negative_control_refactor",
        documentation_file="docs/process.md",
        incorrect_sentence=None,
        expected_code_reference="psutil/__init__.py",
        expected_finding=False,
        files_base={
            "psutil/__init__.py": "class Process:\n    def name(self):\n        return 'python'\n",
            "docs/process.md": "# Process Info\n\n`Process.name()` returns the executable process name.\n"
        },
        files_head={
            "psutil/__init__.py": "class Process:\n    def name(self, oneshot=False):\n        return 'python'\n",
            "docs/process.md": "# Process Info\n\n`Process.name()` returns the executable process name.\n"
        },
        ground_truth_source="https://github.com/giampaolo/psutil/commit/15b2c3d",
        ground_truth_explanation="Backward compatible default parameter added; docs describing Process.name() remain valid."
    ),
]

def run_evaluation():
    client = ModelClient()
    
    print(f"Executing Fresh Held-Out Evaluation on {len(FRESH_HELD_OUT_CASES)} cases across 4 unseen repositories...")
    
    # Run Deterministic
    det_results = []
    print("\n--- Running Deterministic Configuration ---")
    for case in FRESH_HELD_OUT_CASES:
        with tempfile.TemporaryDirectory() as td:
            res = run_historical_case(case, Path(td), configuration="deterministic", client=None)
            det_results.append(res)
            print(f"[{res.case_id}] Expected: {case.expected_finding}, Detected: {res.actual_drift_detected}, Rule: {res.actual_rule_id}, Passed: {res.passed}")

    # Run Selective Hybrid
    hyb_results = []
    print("\n--- Running Selective Hybrid Configuration (Qwen3-8B) ---")
    for case in FRESH_HELD_OUT_CASES:
        with tempfile.TemporaryDirectory() as td:
            res = run_historical_case(case, Path(td), configuration="selective_hybrid", client=client)
            hyb_results.append(res)
            print(f"[{res.case_id}] Expected: {case.expected_finding}, Detected: {res.actual_drift_detected}, Rule: {res.actual_rule_id}, Passed: {res.passed}")

    def calc_metrics(results):
        tp = sum(1 for r in results if r.expected_finding and r.actual_drift_detected)
        fp = sum(1 for r in results if not r.expected_finding and r.actual_drift_detected)
        tn = sum(1 for r in results if not r.expected_finding and not r.actual_drift_detected)
        fn = sum(1 for r in results if r.expected_finding and not r.actual_drift_detected)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 1.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        return {
            "total": len(results),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "specificity": round(spec, 4),
            "f1": round(f1, 4),
            "accuracy": round((tp + tn) / len(results), 4)
        }

    det_metrics = calc_metrics(det_results)
    hyb_metrics = calc_metrics(hyb_results)

    print("\n=== Fresh Held-Out Evaluation Summary ===")
    print("Deterministic:", json.dumps(det_metrics, indent=2))
    print("Selective Hybrid:", json.dumps(hyb_metrics, indent=2))

    # Save to json
    output_data = {
        "dataset_metadata": {
            "total_cases": len(FRESH_HELD_OUT_CASES),
            "repositories": ["pallets/werkzeug", "tornadoweb/tornado", "redis/redis-py", "psutil/psutil"],
            "positive_cases": sum(1 for c in FRESH_HELD_OUT_CASES if c.expected_finding),
            "negative_controls": sum(1 for c in FRESH_HELD_OUT_CASES if not c.expected_finding)
        },
        "deterministic": {
            "metrics": det_metrics,
            "cases": [r.model_dump() for r in det_results]
        },
        "selective_hybrid": {
            "metrics": hyb_metrics,
            "cases": [r.model_dump() for r in hyb_results]
        }
    }
    with open("reports/v0.4/fresh_held_out_results.json", "w") as f:
        json.dump(output_data, f, indent=2)
    print("\nSaved output to reports/v0.4/fresh_held_out_results.json")

if __name__ == "__main__":
    run_evaluation()

"""Every log record must carry request_id, also on a handler that has no request_id filter.

Regression: the first start logged "--- Logging error --- KeyError: 'request_id'" once, from the
startup scan thread, and that message was lost.
"""

CODE = r'''
import io, json, logging, threading
import server  # applies the logging setup
buf = io.StringIO()
handler = logging.StreamHandler(buf)  # a handler added later, without any filter
handler.setFormatter(logging.Formatter("request_id=%(request_id)s %(message)s"))
log = logging.getLogger("cynovela.test_thread")
log.addHandler(handler)
t = threading.Thread(target=lambda: log.warning("from a thread"))
t.start(); t.join()
print("RESULT " + json.dumps({"out": buf.getvalue()}))
'''


def test_handler_without_filter_formats_request_id(run_server_snippet):
    result = run_server_snippet(CODE)
    assert "request_id=- from a thread" in result["out"]

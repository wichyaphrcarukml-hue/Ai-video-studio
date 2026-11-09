"""Run a story-series script (usually tts.py) so edge-tts works behind the cloud session's HTTPS proxy.

edge-tts uses aiohttp, which ignores HTTPS_PROXY, and trusts only certifi's CA bundle, so it cannot reach
speech.platform.bing.com through the proxy. This wrapper passes the proxy to every Communicate() call and
points certifi at the proxy's CA bundle, then runs the given script unchanged.

  python3 tools/cloud/tts_proxy.py ~/.claude/skills/threejs-story-series/scripts/tts.py edge
"""
import os
import runpy
import sys

import certifi
import edge_tts

CA = os.environ.get("CCR_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")
if os.path.exists(CA):
    certifi.where = lambda: CA

_orig_init = edge_tts.Communicate.__init__


def _init(self, *a, **k):
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        k.setdefault("proxy", proxy)
    _orig_init(self, *a, **k)


edge_tts.Communicate.__init__ = _init

if len(sys.argv) < 2:
    sys.exit(__doc__)
script = os.path.abspath(sys.argv[1])
sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(script))  # tts.py imports common.py from its own folder
runpy.run_path(script, run_name="__main__")

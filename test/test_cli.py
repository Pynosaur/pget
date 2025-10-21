import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from pget.app import cli as pget_cli
from pget.app import core as pget_core


class TestCLI(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["PGET_HOME"] = self.tmpdir.name

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        os.environ.pop("PGET_HOME", None)

    def test_list_installed_initially_empty(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = pget_cli.main(["list"]) 
        self.assertEqual(rc, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_list_upstream_uses_api(self):
        # Patch _http_get to return a fake repo listing
        original_http_get = pget_core._http_get
        payload = json.dumps([
            {"name": "pget"},
            {"name": ".github"},
            {"name": "yday"},
        ]).encode("utf-8")

        def fake_http_get(url: str, headers=None):
            if url.startswith("https://api.github.com/orgs/"):
                return 200, payload
            return 404, b""

        try:
            pget_core._http_get = fake_http_get  # type: ignore
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = pget_cli.main(["list", "-u"]) 
            self.assertEqual(rc, 0)
            lines = buf.getvalue().strip().splitlines()
            # .github should be filtered out
            self.assertIn("pget", lines)
            self.assertIn("yday", lines)
            self.assertNotIn(".github", lines)
        finally:
            pget_core._http_get = original_http_get  # type: ignore


if __name__ == "__main__":
    unittest.main()



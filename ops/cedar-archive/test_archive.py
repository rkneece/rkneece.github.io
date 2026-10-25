import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("archive", Path(__file__).with_name("archive.py"))
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.remote = {}
        self.calls = []
        self.corrupt = False

    def fake_command(self, args, check=True):
        self.calls.append(args)
        if args[0] == "git":
            return subprocess.CompletedProcess(args, 0, "abc123\n", "")
        source, target = args[3:5]
        if source.startswith("gs://"):
            data = self.remote[source]
            Path(target).write_bytes(data + b"corrupt" if self.corrupt else data)
            return subprocess.CompletedProcess(args, 0, "", "")
        self.assertIn("--if-generation-match=0", args)
        if target in self.remote:
            return subprocess.CompletedProcess(args, 1, "", "precondition failed")
        self.remote[target] = Path(source).read_bytes()
        return subprocess.CompletedProcess(args, 0, "", "")

    def test_create_only_retry_preserves_remote_bytes(self):
        with tempfile.TemporaryDirectory() as scratch, patch.object(archive, "command", self.fake_command):
            source = Path(scratch) / "a.png"
            source.write_bytes(b"original")
            archive.put_verified(source, "gs://test/object")
            archive.put_verified(source, "gs://test/object")
            self.assertEqual(self.remote["gs://test/object"], b"original")
            source.write_bytes(b"replacement")
            with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                archive.put_verified(source, "gs://test/object")
            self.assertEqual(self.remote["gs://test/object"], b"original")

    def test_corrupt_download_is_not_reported_as_saved(self):
        with tempfile.TemporaryDirectory() as scratch, patch.object(archive, "command", self.fake_command):
            source = Path(scratch) / "a.png"
            source.write_bytes(b"original")
            self.corrupt = True
            with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                archive.put_verified(source, "gs://test/object")

    def test_completed_receipt_and_per_file_record_survive_independently(self):
        with tempfile.TemporaryDirectory() as scratch, patch.object(archive, "command", self.fake_command):
            root = Path(scratch)
            source = root / "NW01_native.png"
            source.write_bytes(b"native-image")
            receipt = root / "receipt.json"
            argv = ["archive.py", "--root", scratch, "--issue", "16", "--receipt", str(receipt), str(source)]
            with patch("sys.argv", argv), patch.dict(os.environ, {"GITHUB_REPOSITORY": "rkneece/43-cedar-blender"}, clear=True), contextlib.redirect_stdout(io.StringIO()):
                archive.main()
            result = json.loads(receipt.read_text())
            asset = result["assets"][0]
            self.assertEqual(asset["path"], "NW01_native.png")
            record = json.loads(self.remote[asset["record_uri"]])
            self.assertEqual(record["asset"]["sha256"], asset["sha256"])
            self.assertTrue(record["issue"].endswith("/16"))
            self.assertEqual(self.remote[asset["uri"]], source.read_bytes())
            self.assertEqual(archive.hashlib.sha256(self.remote[result["manifest_uri"]]).hexdigest(), result["manifest_sha256"])

    def test_reject_symlinks_and_credentials(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            target = root / "target.png"
            target.write_bytes(b"a")
            link = root / "link.png"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "Symlinks"):
                archive.selected_paths(root, [link], False)
            credential = root / "gha-creds-test.json"
            credential.write_text("{}")
            with self.assertRaisesRegex(ValueError, "Credential"):
                archive.selected_paths(root, [credential], False)


if __name__ == "__main__":
    unittest.main()

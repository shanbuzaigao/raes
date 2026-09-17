"""Public-only packaging and preserved byte/source boundaries."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from check_repository import inspect, public_files
from package_release import package
from raes_core.freeze import freeze_new, sha256_bytes
from raes_core.io import pretty_json, load_json

class ReleaseTests(unittest.TestCase):
    def test_public_inventory_excludes_internal(self):
        names = public_files(ROOT)
        self.assertTrue(names)
        self.assertTrue(all('_internal' not in Path(n).parts for n in names))
        self.assertEqual(inspect(ROOT), [])

    def test_public_zip_exact_allowlist_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)/'public.zip'
            n, sha = package(ROOT, output)
            self.assertEqual(len(sha), 64)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(sorted(z.namelist()), ['raes/'+x for x in public_files(ROOT)])
                self.assertEqual(n, len(z.namelist()))
                self.assertIsNone(z.testzip())
            with self.assertRaises(ValueError): package(ROOT, output)

    def test_package_rejects_internal_even_when_allowlisted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/'_internal').mkdir()
            (root/'_internal/note.md').write_text('private')
            (root/'PUBLIC_FILES.txt').write_text('_internal/note.md\n')
            with self.assertRaises(ValueError): public_files(root)

    def test_manifest_cannot_write_into_its_closed_scope(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d);(root/'inputs').mkdir();(root/'inputs/a.txt').write_text('a')
            with self.assertRaises(ValueError):
                freeze_new(root, ['inputs/a.txt'], root/'inputs/manifest.json', scopes=['inputs'])
            self.assertFalse((root/'inputs/manifest.json').exists())

    def test_prompt_preserves_CRLF_eligibility_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            cb = load_json(ROOT/'examples/synthetic/inputs/codebook.json')
            raw = (ROOT/'examples/synthetic/inputs/eligibility.json').read_bytes().replace(b'\n', b'\r\n')
            (folder/'eligibility.json').write_bytes(raw)
            cb['eligibility']['sha256'] = sha256_bytes(raw)
            (folder/'codebook.json').write_text(pretty_json(cb), encoding='utf-8')
            (folder/'context.json').write_text('{}')
            cmd = [sys.executable, '-B', str(ROOT/'tools/render_prompt.py'), '--codebook', str(folder/'codebook.json'),
                   '--template', str(ROOT/'templates/prompts/coding_system.md'), '--context', str(folder/'context.json'),
                   '--output', str(folder/'prompt.md')]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(raw, (folder/'prompt.md').read_bytes())

    def test_reproduce_refuses_output_in_source_tree(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT/'examples/synthetic/reproduce.py'),
                                 '--output', str(ROOT/'example-must-not-be-created')], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((ROOT/'example-must-not-be-created').exists())

if __name__ == '__main__': unittest.main()

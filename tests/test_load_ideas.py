import json
import os
import tempfile
import unittest
from pathlib import Path

import run_business_plans_pipeline as pipeline


class TestLoadIdeas(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.dirpath = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def write_file(self, name: str, content: str) -> Path:
        p = self.dirpath / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_load_json_list(self):
        data = [{"id": 1, "title": "One"}, {"id": 2, "title": "Two"}]
        p = self.dirpath / "ideas.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        loaded = pipeline.load_ideas(p)
        self.assertIsInstance(loaded, list)
        self.assertEqual(len(loaded), 2)

    def test_load_json_not_list_raises(self):
        p = self.dirpath / "ideas.json"
        p.write_text(json.dumps({"id": 1}), encoding="utf-8")
        with self.assertRaises(ValueError):
            pipeline.load_ideas(p)

    def test_load_csv_basic(self):
        content = "id,idea\n1,First idea\n2,Second idea\n"
        p = self.write_file("ideas.csv", content)
        loaded = pipeline.load_ideas(p)
        self.assertIsInstance(loaded, list)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["id"], 1)
        self.assertEqual(loaded[0]["title"], "First idea")

    def test_load_csv_with_headers_and_blank_lines(self):
        content = "id,idea\n\n1,One\n\n"  # repeated blank lines
        p = self.write_file("ideas.csv", content)
        loaded = pipeline.load_ideas(p)
        self.assertEqual(len(loaded), 1)

    def test_load_csv_malformed_id_skips(self):
        content = "id,idea\nX,NoId\n2,Valid\n"
        p = self.write_file("ideas.csv", content)
        loaded = pipeline.load_ideas(p)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["id"], 2)

    def test_missing_file_raises(self):
        p = self.dirpath / "missing.csv"
        with self.assertRaises(FileNotFoundError):
            pipeline.load_ideas(p)


if __name__ == "__main__":
    unittest.main()

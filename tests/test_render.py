import contextlib
import importlib.util
import io
import json
import os
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("render", ROOT / "scripts/render.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def session():
    return {
        "title": "Boundary example", "summary": "Synthetic data only",
        "steps": [{
            "id": "one", "title": "One", "code": "value = 1",
            "explanation": ["Assignment"], "inputs": [], "outputs": ["1"],
            "question": {"prompt": "What value?", "hint": "Read assignment", "answer": "1", "transfer": "Change to 2"},
        }],
    }


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.code = []
        self.in_code = False

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "code":
            self.in_code = True

    def handle_endtag(self, tag):
        if tag == "code":
            self.in_code = False

    def handle_data(self, data):
        if self.in_code:
            self.code.append(data)


class InputBoundaries(unittest.TestCase):
    def test_code_is_inert_and_template_tokens_remain_literal(self):
        data = session()
        payload = '{{STEPS}} </code><img src=x onerror="alert(1)"> & <script>alert(2)</script>'
        data["steps"][0]["code"] = payload
        markup = Markup()
        markup.feed(renderer.render(renderer.validate_document(data, "learn"), "learn"))
        self.assertEqual("".join(markup.code), payload)
        self.assertNotIn("img", markup.tags)
        self.assertEqual(markup.tags.count("script"), 1)  # Only the reader's own script.

    def test_diagram_cannot_link_out_or_traverse(self):
        for value in ("../x.html", "%2e%2e/x.html", "x/%2f../a.html", "/x.html", "https://example.com/a.html", "a\\b.html", "x.html#fragment", "\nx.html"):
            with self.subTest(value=value), self.assertRaises(renderer.ValidationError):
                renderer.valid_diagram(value)
        self.assertEqual(renderer.valid_diagram("diagrams/flow.html"), "diagrams/flow.html")

    def test_mode_contract_and_identifier_collisions(self):
        data = session()
        del data["steps"][0]["question"]
        renderer.validate_document(data, "explain")
        with self.assertRaises(renderer.ValidationError):
            renderer.validate_document(data, "learn")
        for ids in (("one", "one"), ("one", "one-title"), ("content",)):
            data = session()
            data["steps"] = [dict(data["steps"][0], id=value) for value in ids]
            with self.subTest(ids=ids), self.assertRaises(renderer.ValidationError):
                renderer.validate_document(data, "learn")

    def test_hardlink_output_cannot_destroy_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "session.json"
            target = Path(directory) / "guide.html"
            original = json.dumps(session()).encode()
            source.write_bytes(original)
            os.link(source, target)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(renderer.main([str(source), str(target)]), 2)
            self.assertEqual(source.read_bytes(), original)

    def test_invalid_input_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "session.json"
            target = Path(directory) / "guide.html"
            target.write_text("keep", encoding="utf-8")
            for invalid in (b'{"steps":', b"\xff", b'{"steps":[]}'):
                source.write_bytes(invalid)
                errors = io.StringIO()
                with contextlib.redirect_stderr(errors):
                    self.assertEqual(renderer.main([str(source), str(target)]), 2)
                self.assertNotIn("Traceback", errors.getvalue())
                self.assertEqual(target.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()

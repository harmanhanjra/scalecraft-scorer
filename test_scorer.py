import csv, io, json, os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def _load(fname, modname):
    spec = importlib.util.spec_from_file_location(modname, os.path.join(os.path.dirname(os.path.abspath(__file__)), fname))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
sc = _load('scalecraft-scorer.py', 'sc')

def lead(**kw):
    base = {"name": "Test Biz", "city": "Berlin", "website": "", "phone": "", "email": "", "notes": ""}
    base.update(kw); return base

class ScoreTests(unittest.TestCase):
    def test_no_website_scores_high(self):
        s = sc.score_lead(lead())
        self.assertGreater(s["score"], 50)
        self.assertIn("no website listed", s["reasons"])

    def test_social_only_penalized_up(self):
        s = sc.score_lead(lead(website="https://facebook.com/testbiz"))
        self.assertIn("social page instead of real site", s["reasons"])
        self.assertGreater(s["score"], 50)

    def test_modern_site_with_custom_email_scores_low(self):
        s = sc.score_lead(lead(website="https://testbiz.io", email="hi@testbiz.io"))
        self.assertLessEqual(s["score"], 50)

    def test_pain_keywords_boost(self):
        plain = sc.score_lead(lead(website="https://testbiz.io", email="hi@testbiz.io"))["score"]
        painful = sc.score_lead(lead(website="https://testbiz.io", email="hi@testbiz.io",
                                notes="still takes bookings on paper, very manual"))["score"]
        self.assertGreater(painful, plain)

    def test_free_email_penalized(self):
        s = sc.score_lead(lead(website="https://testbiz.io", email="testbiz@gmail.com"))
        self.assertIn("free email provider", s["reasons"])

    def test_score_bounded(self):
        s = sc.score_lead(lead(notes="outdated old site no website manual paper spreadsheet by hand call to book"))
        self.assertLessEqual(s["score"], 100)

class RankTests(unittest.TestCase):
    def test_sorted_desc_with_rank(self):
        scored = sc.score_leads([lead(name="A"), lead(name="B", website="https://b.io", email="x@b.io")])
        self.assertEqual(scored[0]["name"], "A")
        self.assertEqual([s["rank"] for s in scored], [1, 2])

class CliTests(unittest.TestCase):
    def _csv(self, rows):
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=["name","city","category","website","phone","email","notes"])
        w.writeheader(); w.writerows(rows)
        f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
        f.write(buf.getvalue()); f.close(); return f.name

    def test_cli_json_out(self):
        path = self._csv([lead(name="A"), lead(name="B", website="https://b.io", email="x@b.io")])
        try:
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = sc.main(["--in", path])
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(data[0]["name"], "A")
        finally:
            os.unlink(path)

    def test_cli_min_score_filters(self):
        path = self._csv([lead(name="A"), lead(name="B", website="https://b.io", email="x@b.io")])
        try:
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = sc.main(["--in", path, "--min-score", "70"])
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            self.assertTrue(all(d["score"] >= 70 for d in data))
        finally:
            os.unlink(path)

    def test_cli_missing_file(self):
        import contextlib
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = sc.main(["--in", "/nonexistent.csv"])
        self.assertEqual(rc, 1)

if __name__ == "__main__":
    unittest.main()

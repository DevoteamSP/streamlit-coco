"""Ask CoCo, part "data": the CSV text built in the browser from the rows received (node runs the part with a stub registry)."""
# ruff: noqa: E501

import json
import shutil
import subprocess
import unittest
from pathlib import Path

PART = (
    Path(__file__).resolve().parents[1] / "streamlit_coco" / "static" / "coco" / "parts" / "data.js"
)


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class CsvTest(unittest.TestCase):
    def csv(self, columns, rows):
        script = (
            "const src = require('fs').readFileSync(process.argv[1], 'utf8'); let fn;"
            "new Function('part', src)((n, f) => { fn = f; });"
            "const C = {h: {esc: String, fold() {}, ic() {}, icon() {}, L: (k) => k, E: (k) => k}, state: () => ({}), block: {}, decorate: {step: [], answer: []}, takeover: [], escape: [], on() {}};"
            "fn(C); const t = JSON.parse(process.argv[2]); console.log(JSON.stringify(C.h.tableCsv(t)));"
        )
        table = {"columns": [{"name": c} for c in columns], "rows": rows}
        done = subprocess.run(
            ["node", "-e", script, str(PART), json.dumps(table)],
            capture_output=True,
            encoding="utf-8",
            check=True,
            timeout=60,
        )
        return json.loads(done.stdout)

    def test_plain(self):
        self.assertEqual(self.csv(["A", "B"], [["x", "1 530"]]), "A,B\r\nx,1 530\r\n")

    def test_quotes_separators_newlines(self):
        self.assertEqual(
            self.csv(["A"], [['say "hi"'], ["a,b"], ["a;b"], ["l1\nl2"]]),
            'A\r\n"say ""hi"""\r\n"a,b"\r\n"a;b"\r\n"l1\nl2"\r\n',
        )

    def test_formula_injection(self):
        out = self.csv(["A"], [["=1+1"], ["+1"], ["-2"], ["@SUM(A1)"], ["ok=1"]])
        self.assertEqual(out, "A\r\n'=1+1\r\n'+1\r\n'-2\r\n'@SUM(A1)\r\nok=1\r\n")


if __name__ == "__main__":
    unittest.main()

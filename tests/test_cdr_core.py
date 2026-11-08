"""Run with:  python -m unittest discover -s tests"""
import csv
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import cdr_core  # noqa: E402

KEYS = ("orientation", "judgment", "community", "home", "care")


class TestScoring(unittest.TestCase):
    def test_golden_all_combinations(self):
        """All 12,500 valid combinations. Golden file generated from the original
        main.py (29/12/23), with one correction (Nov 2026): Rule 7 ties ABOVE M now
        choose the tied score closest to M (84 combinations, e.g. M=1, [0,2,2,3,3] -> 2,
        previously 3)."""
        with open(os.path.join(HERE, "golden_cdr.csv"), newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 12500)
        for r in rows:
            m = float(r["memory"])
            boxes = [float(r[k]) for k in KEYS]
            cdr, rule = cdr_core.calculate_cdr(m, boxes)
            self.assertEqual((float(cdr), rule), (float(r["cdr_global"]), cdr_core.RULES[int(r["rule"])]),
                             msg=f"memory={m} boxes={boxes}")

    def test_known_examples(self):
        cases = [(3, [3, 2, 2, 1, 1], 2), (1, [0, 0, 0, 0, 0], 0.5), (0, [0.5, 0.5, 0, 0, 0], 0.5),
                 (0, [0.5, 0, 0, 0, 0], 0), (0.5, [1, 1, 1, 0, 0], 1), (2, [1, 1, 1, 3, 3], 2),
                 (1, [0, 2, 2, 3, 3], 2), (1, [3, 0.5, 3, 2, 2], 2)]  # Rule 7, ties above M
        for m, boxes, expected in cases:
            self.assertEqual(cdr_core.calculate_cdr(m, boxes)[0], expected)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            cdr_core.calculate_cdr(1, [0, 0, 0, 0, 0.5])  # personal care cannot be 0.5
        with self.assertRaises(ValueError):
            cdr_core.calculate_cdr(4, [0, 0, 0, 0, 0])


class TestCSV(unittest.TestCase):
    def test_positional_six_columns(self):
        text = "Memory,box1,box2,box3,box4,box5\n3,3,2,2,1,1\n1,0,0,0,0,0\n"
        header, rows, out, _ = cdr_core.process_csv(text)
        self.assertEqual(header[-3:], ["CDR_global", "Rule_applied", "CDR_note"])
        self.assertEqual([r[-3] for r in rows], ["2", "0.5"])
        self.assertTrue(rows[0][-2].startswith("Rule 7"))

    def test_id_column_semicolon_decimal_comma_and_errors(self):
        text = ("ID;Memoria;Orientation;Judgment;Community;Home;PersonalCare\n"
                "A01;0,5;1;1;1;0;0\n"
                "A02;1;0;0;;0;0\n"
                "A03;1;0;0;0;0;0,5\n")
        header, rows, out, summary = cdr_core.process_csv(text)
        self.assertEqual(rows[0][:1] + rows[0][-3:-1], ["A01", "1", cdr_core.RULES[2]])
        _, rows2, _, _ = cdr_core.process_csv("ID;Memory;box1;box2;box3;box4;box5\nA;1;0;0;0;0;0\n")
        self.assertEqual(rows2[0][-3], "0,5")  # decimal comma for semicolon files
        self.assertEqual(rows[1][-1], "missing score(s)")
        self.assertIn("Personal Care", rows[2][-1])
        self.assertIn(";", out.splitlines()[0])
        self.assertIn("1 rows scored, 2 rows", summary)

    def test_rerun_on_output_replaces_columns(self):
        _, _, out, _ = cdr_core.process_csv("Memory,box1,box2,box3,box4,box5\n0,0,0,0,0,0\n")
        header, rows, _, _ = cdr_core.process_csv(out)
        self.assertEqual(header.count("CDR_global"), 1)

    def test_unidentifiable_columns(self):
        with self.assertRaises(ValueError):
            cdr_core.process_csv("ID,a,b,c,d,e,f\n1,0,0,0,0,0,0\n")


if __name__ == "__main__":
    unittest.main()

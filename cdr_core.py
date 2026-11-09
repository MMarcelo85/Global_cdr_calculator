"""CDR Global scoring (Morris, 1993) and CSV batch processing.

Standard library only, so it can be shared by the Streamlit app (main.py)
and the desktop app (desktop_app.py), and packaged into a small executable.
"""
import csv
import io
from collections import Counter

SCORES = (0, 0.5, 1, 2, 3)
CARE_SCORES = (0, 1, 2, 3)  # Personal care cannot be scored 0.5

DOMAINS = [
    ("memory", "Memory"),
    ("orientation", "Orientation"),
    ("judgment", "Judgment and Problem Solving"),
    ("community", "Community Affairs"),
    ("home", "Home and Hobbies"),
    ("care", "Personal Care"),
]

RULES = {
    1: "Rule 1: If M = 0, CDR = 0 unless there is impairment (0.5 or greater) in two or more secondary categories, in which case CDR = 0.5.",
    2: "Rule 2: When M = 0.5, CDR = 1 if at least three of the other categories are scored one or greater. Else CDR = 0.5.",
    3: "Rule 3: CDR = M if at least three secondary categories are given the same score as memory.",
    4: "Rule 4: When three secondary categories are scored on one side of M and two secondary categories are scored on the other side of M, CDR = M.",
    5: "Rule 5: Whenever three or more secondary categories are given a score greater or less than the memory score, CDR = score of majority of secondary categories on whichever side of M has the greater number of secondary categories.",
    6: "Rule 6: When M = 1 or greater, CDR cannot be 0; in this circumstance, CDR = 0.5 when the majority of secondary categories are 0.",
    7: "Rule 7: With ties in the secondary categories on one side of M, choose the tied scores closest to M for CDR (e.g., M and another secondary category = 3, two secondary categories = 2, and two secondary categories = 1; CDR = 2).",
    8: "Rule 8: When only one or two secondary categories are given the same score as M, CDR = M as long as no more than two secondary categories are on either side of M.",
}

REFERENCE = "Morris, J.C. (1993). The clinical dementia rating (CDR): Current version and scoring rules. Neurology, 43(11), 2412-2414."
RULES_URL = "https://knightadrc.wustl.edu/professionals-clinicians/cdr-dementia-staging-instrument/cdr-scoring-rules/"


def _value_counts(values):
    """Distinct values ordered by count (descending); ties keep first-appearance order."""
    return [v for v, _ in Counter(values).most_common()]


def _score(memory, sc):
    """Return (cdr_global, rule_number). Rule order matches the original app (29/12/23)."""
    lower = sum(s < memory for s in sc)
    higher = sum(s > memory for s in sc)
    equal = sum(s == memory for s in sc)
    n0, n05, n1, n2, n3 = (sc.count(v) for v in (0, 0.5, 1, 2, 3))

    counted = Counter(sc)
    max_count = max(counted.values())
    ties = [v for v, n in counted.items() if n == max_count]

    # Rule 7: ties on one side of M
    if len(ties) == 2 and memory >= 1:
        if (ties[0] > memory and ties[1] > memory) or (ties[0] < memory and ties[1] < memory):
            c0, c1 = _value_counts(sc)[:2]
            d0, d1 = memory - c0, memory - c1
            if c0 < 1 and c1 < 1 and memory == 1:
                return 0.5, 7
            if c0 < memory and c1 < memory and d0 < d1:
                return c0, 7
            if c0 < memory and c1 < memory and d0 > d1:
                return c1, 7
            if c0 > memory and c1 > memory:  # ties above M: the lower score is the closest to M
                return min(c0, c1), 7
            if d0 == d1:
                return min(c0, c1), 7
    elif len(ties) == 2 and memory == 0:
        if ties[0] > memory and ties[1] > memory:
            c0, c1 = _value_counts(sc)[:2]
            return min(c0, c1), 7

    # Rule 8
    if equal in (1, 2) and lower <= 2 and higher <= 2:
        return memory, 8

    # Rule 1
    if memory == 0:
        return (0.5 if n05 + n1 + n2 + n3 >= 2 else 0), 1

    # Rule 2
    if memory == 0.5:
        return (1 if n1 + n2 + n3 >= 3 else 0.5), 2

    # Rule 3
    if sc.count(memory) >= 3 and memory > 0.5:
        return memory, 3

    # Rule 6
    if memory >= 1 and n0 > n05 and n0 > n1 and n0 > n2 and n0 > n3:
        return 0.5, 6

    # Rule 4
    if (lower, higher) in ((2, 3), (3, 2)):
        return memory, 4

    # Rule 5
    if memory > 0.5 and (lower >= 3 or higher >= 3):
        cats = _value_counts(sc)
        if len(cats) == 1:
            return cats[0], 5
        if len(cats) == 4 and lower == 3:
            if cats[0] == memory:
                return max(c for c in cats if c != memory), 5
            return cats[0], 5
        if memory != cats[0] and cats[0] != 0:
            return cats[0], 5
        if memory != cats[1] and cats[1] != 0:
            return cats[1], 5
        return 0.5, 5

    raise ValueError(f"No CDR rule applies to memory={memory}, boxes={sc}")  # never reached for valid input


def validate(memory, boxes):
    """Return an error message, or None if the six scores are valid."""
    if len(boxes) != 5:
        return "expected 5 secondary categories"
    for (key, label), value in zip(DOMAINS, [memory] + list(boxes)):
        allowed = CARE_SCORES if key == "care" else SCORES
        if value not in allowed:
            return f"invalid {label} score: {fmt(value)}"
    return None


def calculate_cdr(memory, boxes):
    """memory: 0, 0.5, 1, 2 or 3. boxes: [orientation, judgment, community, home, care].
    Returns (cdr_global, rule_text)."""
    error = validate(memory, boxes)
    if error:
        raise ValueError(error)
    cdr, rule = _score(memory, list(boxes))
    return cdr, RULES[rule]


def fmt(x):
    """Format a score: 0, 0.5, 1, 2, 3."""
    return f"{x:g}" if isinstance(x, (int, float)) else str(x)


# ---------------------------------------------------------------- CSV batch

# Accepted column names (case, spaces, underscores and accents ignored).
ALIASES = {
    "memory": {"memory", "memoria", "mem", "m", "cdrmem"},
    "orientation": {"orientation", "orientacion", "orient", "box1", "cdrorient"},
    "judgment": {"judgment", "judgement", "judgmentandproblemsolving", "juicio", "judg", "box2", "cdrjudge"},
    "community": {"community", "communityaffairs", "comunidad", "commun", "box3", "cdrcommun"},
    "home": {"home", "homeandhobbies", "homehobb", "hogar", "box4", "cdrhome"},
    "care": {"personalcare", "perscare", "care", "cuidadopersonal", "cuidado", "box5", "cdrcare"},
}

OUT_SCORE = "CDR_global"
OUT_RULE = "Rule_applied"
OUT_NOTE = "CDR_note"


def _norm(name):
    name = name.strip().lower()
    for a, b in zip("áéíóúñ", "aeioun"):
        name = name.replace(a, b)
    return "".join(ch for ch in name if ch.isalnum())


def _parse_score(text):
    text = (text or "").strip().replace(",", ".")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return text


def find_columns(header):
    """Map each domain to a column index. Uses column names if all six are found;
    otherwise, if the file has exactly 6 columns, uses them in order
    (Memory, Orientation, Judgment, Community, Home, Personal care)."""
    normed = [_norm(h) for h in header]
    mapping = {}
    for key, names in ALIASES.items():
        for i, n in enumerate(normed):
            if n in names and i not in mapping.values():
                mapping[key] = i
                break
    if len(mapping) == 6:
        return [mapping[k] for k, _ in DOMAINS]
    data_cols = [i for i, n in enumerate(normed) if n not in {_norm(OUT_SCORE), _norm(OUT_RULE), _norm(OUT_NOTE)}]
    if len(data_cols) == 6:
        return data_cols
    raise ValueError(
        "Could not identify the CDR columns. Use either exactly 6 columns in this order: "
        "Memory, Orientation, Judgment, Community, Home, Personal care; or name the columns "
        "Memory, Orientation, Judgment, Community, Home, PersonalCare (other columns such as "
        f"IDs are kept). Columns found: {', '.join(header)}"
    )


def decode(data):
    """Decode uploaded bytes (UTF-8 with or without BOM, else Latin-1)."""
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def process_csv(text):
    """Score every row of a CSV text.
    Returns (header, rows, output_csv_text, summary). Original columns are kept
    unchanged; CDR_global, Rule_applied and CDR_note are added (replaced if present).
    Rows with missing or invalid scores are kept, with the reason in CDR_note."""
    sample = text[:5000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    all_rows = [r for r in reader if any(cell.strip() for cell in r)]
    if not all_rows:
        raise ValueError("The file is empty.")
    header, data = all_rows[0], all_rows[1:]

    # Drop output columns from a previous run so they are recalculated.
    keep = [i for i, h in enumerate(header) if h.strip() not in (OUT_SCORE, OUT_RULE, OUT_NOTE)]
    header = [header[i] for i in keep]
    data = [[(r[i] if i < len(r) else "") for i in keep] for r in data]

    cols = find_columns(header)
    out_header = header + [OUT_SCORE, OUT_RULE, OUT_NOTE]
    out_rows, n_ok, n_bad = [], 0, 0
    for r in data:
        values = [_parse_score(r[i]) if i < len(r) else None for i in cols]
        if any(v is None for v in values):
            score, rule, note = "", "", "missing score(s)"
        else:
            error = validate(values[0], values[1:])
            if error:
                score, rule, note = "", "", error
            else:
                cdr, rule_n = _score(values[0], values[1:])
                score, rule, note = fmt(cdr), RULES[rule_n], ""
                if delimiter == ";":  # Excel in Spanish/European locales: decimal comma
                    score = score.replace(".", ",")
        n_ok += note == ""
        n_bad += note != ""
        out_rows.append(r + [score, rule, note])

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter, lineterminator="\n")
    writer.writerow(out_header)
    writer.writerows(out_rows)
    used = ", ".join(header[i] for i in cols)
    summary = f"{n_ok} rows scored, {n_bad} rows with missing/invalid scores (see {OUT_NOTE}). Columns used: {used}."
    return out_header, out_rows, buf.getvalue(), summary


# ---------------------------------------------------------------- self-test

# One case per rule (checked against the full golden file by tests/test_cdr_core.py).
SELF_TEST_CASES = [
    (0, [0, 0, 0, 0, 0], 0, 1),
    (0.5, [0, 0, 0, 0, 0], 0.5, 2),
    (1, [0, 0, 1, 1, 1], 1, 3),
    (1, [0, 0, 0.5, 2, 2], 1, 4),
    (1, [0, 0, 0.5, 1, 1], 0.5, 5),
    (1, [0, 0, 0, 0, 0], 0.5, 6),
    (1, [0, 2, 2, 3, 3], 2, 7),  # Rule 7 as corrected in v2.0.0 (the old code gave 3)
    (1, [3, 0.5, 3, 2, 2], 2, 7),
    (0.5, [0, 0, 0.5, 0.5, 1], 0.5, 8),
]


def self_test():
    """Quick check of scoring and CSV handling, used on the packaged executable
    (desktop_app.py --self-test). Returns a list of failure messages (empty = OK)."""
    failures = []
    for memory, boxes, expected, rule in SELF_TEST_CASES:
        got = calculate_cdr(memory, boxes)
        if got != (expected, RULES[rule]):
            failures.append(f"M={fmt(memory)} {boxes}: got {fmt(got[0])} ({got[1][:7]}), "
                            f"expected {fmt(expected)} (Rule {rule})")
    for memory, boxes in ((0, [0, 0, 0, 0, 0.5]), (9, [1, 0, 0, 0, 0])):
        if validate(memory, boxes) is None:
            failures.append(f"invalid scores accepted: M={fmt(memory)} {boxes}")
    checks = [
        ("ID;Memoria;Orientación;Juicio;Comunidad;Hogar;Cuidado personal\n"
         "A1;0,5;0;0;0;0;0\nA2;1;0;0;;0;0\n", ["0,5", ""]),
        ("PTID\tMEMORY\tORIENT\tJUDGMENT\tCOMMUN\tHOMEHOBB\tPERSCARE\n"
         "X\t1\t0\t0\t0\t0\t0\n", ["0.5"]),
        ("Memory,box1,box2,box3,box4,box5\n1,0,2,2,3,3\n", ["2"]),
    ]
    for text, expected in checks:
        try:
            header, rows, _, _ = process_csv(text)
            got = [r[header.index(OUT_SCORE)] for r in rows]
        except ValueError as e:
            got = str(e)
        if got != expected:
            failures.append(f"CSV {text.splitlines()[0][:30]}...: got {got}, expected {expected}")
    return failures

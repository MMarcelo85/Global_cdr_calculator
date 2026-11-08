"""CDR Global Calculator - desktop version (Windows / Linux).

Run:    python desktop_app.py
Build:  pyinstaller --onefile --windowed --name CDR_Global_Calculator desktop_app.py
"""
import os
import tkinter as tk
import webbrowser
from tkinter import filedialog, font as tkfont, messagebox, ttk

import cdr_core

APP_TITLE = "CDR Global Calculator"
APP_VERSION = "2.0.0"
AUTHOR = "Marcelo A. Maito"
CONTACT = "mmaito@udesa.edu.ar"
REPO_URL = "https://github.com/MMarcelo85/Global_cdr_calculator"
BASE_SIZE = 11  # base font size (pt) for all text; titles are set separately

# Same text as the LICENSE file (checked by tests/test_cdr_core.py).
LICENSE_TEXT = """MIT License

Copyright (c) 2023 Marcelo A. Maito

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


def font(size, bold=False):
    """System default font with another size/weight (call after tk.Tk())."""
    f = tkfont.nametofont("TkDefaultFont").copy()
    f.configure(size=size, weight="bold" if bold else "normal")
    return f


def text_panel(parent):
    """Read-only scrollable text area with heading ('h') style. Returns (frame, text, add_link)."""
    frame = ttk.Frame(parent, padding=16)
    text = tk.Text(frame, wrap="word", relief="flat", padx=8, pady=8, font=font(BASE_SIZE))
    text.tag_configure("h", font=font(BASE_SIZE + 1, True))
    sb = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=sb.set)
    text.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def add_link(url):
        tag = f"link{len(text.tag_names())}"
        text.tag_configure(tag, foreground="#1f4e9c", underline=True)
        text.tag_bind(tag, "<Button-1>", lambda e: webbrowser.open(url))
        text.tag_bind(tag, "<Enter>", lambda e: text.config(cursor="hand2"))
        text.tag_bind(tag, "<Leave>", lambda e: text.config(cursor=""))
        text.insert("end", url + "\n", tag)

    return frame, text, add_link


def build_case_tab(parent):
    frame = ttk.Frame(parent, padding=16)
    ttk.Label(frame, text="Select the score for memory and secondary categories.",
              font=font(BASE_SIZE + 2, True)).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))

    variables = []
    for row, (key, label) in enumerate(cdr_core.DOMAINS, start=1):
        options = cdr_core.CARE_SCORES if key == "care" else cdr_core.SCORES
        text = label + (" (cannot be 0.5)" if key == "care" else "")
        ttk.Label(frame, text=text).grid(row=row, column=0, sticky="w", padx=(0, 16), pady=4)
        var = tk.StringVar(value="0")
        for value in options:
            col = cdr_core.SCORES.index(value) + 1  # same column for the same score in every row
            ttk.Radiobutton(frame, text=cdr_core.fmt(value), value=cdr_core.fmt(value), variable=var,
                            command=lambda: update()).grid(row=row, column=col, sticky="w", padx=8)
        variables.append(var)

    ttk.Separator(frame).grid(row=8, column=0, columnspan=6, sticky="ew", pady=14)
    score_label = ttk.Label(frame, font=font(18, True), foreground="#1f4e9c")
    score_label.grid(row=9, column=0, columnspan=6, sticky="w")
    ttk.Label(frame, text="Applied rule:", font=font(BASE_SIZE + 1, True)).grid(
        row=10, column=0, columnspan=6, sticky="w", pady=(10, 2))
    rule_label = ttk.Label(frame, wraplength=780, justify="left")
    rule_label.grid(row=11, column=0, columnspan=6, sticky="w")

    def update():
        values = [float(v.get()) for v in variables]
        cdr, rule = cdr_core.calculate_cdr(values[0], values[1:])
        score_label.config(text=f"CDR Global Score: {cdr_core.fmt(cdr)}")
        rule_label.config(text=rule)

    update()
    return frame


def build_csv_tab(parent):
    frame = ttk.Frame(parent, padding=16)
    instructions = (
        "Open a CSV file to calculate the CDR Global for every row.\n"
        "Use either exactly 6 columns in this order: Memory, Orientation, Judgment, Community, Home, "
        "Personal care; or name the columns Memory, Orientation, Judgment, Community, Home, PersonalCare "
        "(other columns, such as IDs, are kept). Comma or semicolon separated files are accepted.\n"
        f"The results file adds the columns {cdr_core.OUT_SCORE}, {cdr_core.OUT_RULE} and "
        f"{cdr_core.OUT_NOTE} (reason when a row could not be scored). The original file is not modified."
    )
    ttk.Label(frame, text=instructions, wraplength=840, justify="left").pack(anchor="w")

    buttons = ttk.Frame(frame)
    buttons.pack(anchor="w", pady=10)
    summary = ttk.Label(frame, wraplength=840, justify="left")
    summary.pack(anchor="w", pady=(0, 6))

    table_frame = ttk.Frame(frame)
    table_frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(table_frame, show="headings")
    ysb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    xsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    ysb.grid(row=0, column=1, sticky="ns")
    xsb.grid(row=1, column=0, sticky="ew")
    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)

    state = {"csv": None, "name": None}

    def open_file():
        path = filedialog.askopenfilename(title="Open CSV file",
                                          filetypes=[("CSV files", "*.csv *.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "rb") as f:
                header, rows, out_csv, text = cdr_core.process_csv(cdr_core.decode(f.read()))
        except (OSError, ValueError) as e:
            messagebox.showerror(APP_TITLE, str(e))
            return
        state["csv"], state["name"], state["dir"] = out_csv, os.path.basename(path), os.path.dirname(path)
        summary.config(text=f"{os.path.basename(path)}: {text}")
        tree.delete(*tree.get_children())
        tree["columns"] = [str(i) for i in range(len(header))]
        for i, h in enumerate(header):
            tree.heading(str(i), text=h)
            width = {cdr_core.OUT_RULE: 500, cdr_core.OUT_NOTE: 240, cdr_core.OUT_SCORE: 110}.get(h, 100)
            tree.column(str(i), width=width, minwidth=60, stretch=False)
        for r in rows:
            tree.insert("", "end", values=r)
        save_button.state(["!disabled"])

    def save_file():
        if not state["csv"]:
            return
        default = os.path.splitext(state["name"])[0] + "_CDR_global.csv"
        path = filedialog.asksaveasfilename(title="Save results", initialdir=state["dir"],
                                            initialfile=default, defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            # utf-8-sig so Excel shows accents correctly
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(state["csv"])
        except OSError as e:
            messagebox.showerror(APP_TITLE, str(e))
            return
        messagebox.showinfo(APP_TITLE, f"Results saved to:\n{path}")

    ttk.Button(buttons, text="Open CSV file...", command=open_file).pack(side="left")
    save_button = ttk.Button(buttons, text="Save results as CSV...", command=save_file)
    save_button.pack(side="left", padx=8)
    save_button.state(["disabled"])
    return frame


def build_rules_tab(parent):
    frame, text, add_link = text_panel(parent)
    text.insert("end", "CDR Scoring Rules\n", "h")
    add_link(cdr_core.RULES_URL)
    text.insert("end", cdr_core.REFERENCE + "\n\n")
    text.insert("end", "Rules:\n", "h")
    for n in range(1, 7):
        text.insert("end", f"{n}. {cdr_core.RULES[n].split(': ', 1)[1]}\n\n")
    text.insert("end", "Unusual circumstances occur occasionally in Alzheimer's disease and may be expected in "
                       "non-Alzheimer dementia as well are scored as follows:\n", "h")
    for n in (7, 8):
        text.insert("end", f"{n}. {cdr_core.RULES[n].split(': ', 1)[1]}\n\n")
    text.insert("end", f"Please, write to {CONTACT} if you find any scoring errors.\n")
    text.config(state="disabled")
    return frame


def build_about_tab(parent):
    frame, text, add_link = text_panel(parent)
    text.insert("end", f"{APP_TITLE}\n", "h")
    text.insert("end", f"Version {APP_VERSION}\n\n")
    text.insert("end", "Calculates the Clinical Dementia Rating (CDR) Global score from the six CDR boxes "
                       "using the scoring rules of Morris (1993), shows the rule applied, and scores whole "
                       "CSV files.\n\n")
    text.insert("end", f"Author: {AUTHOR}\nContact: {CONTACT}\nSource code and downloads:\n")
    add_link(REPO_URL)
    text.insert("end", "\nReference:\n", "h")
    text.insert("end", cdr_core.REFERENCE + "\n")
    add_link(cdr_core.RULES_URL)
    text.insert("end", "\nDisclaimer:\n", "h")
    text.insert("end", "This tool supports, but does not replace, clinical judgment. The CDR Global must be "
                       "based on boxes scored by a trained rater. Please report any scoring error to "
                       f"{CONTACT}.\n\n")
    text.insert("end", "License:\n", "h")
    text.insert("end", LICENSE_TEXT + "\n")
    text.insert("end", "Third-party components:\n", "h")
    text.insert("end", "This program includes Python (Python Software Foundation License) and Tcl/Tk "
                       "(BSD-style license), packaged with PyInstaller.\n")
    text.config(state="disabled")
    return frame


def main():
    try:  # sharp text on high-DPI Windows screens
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("940x700")
    root.minsize(720, 540)

    # Bigger base font for every widget (tabs, labels, buttons, table).
    for name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont", "TkCaptionFont"):
        tkfont.nametofont(name).configure(size=BASE_SIZE)
    row_height = tkfont.nametofont("TkDefaultFont").metrics("linespace") + 8
    ttk.Style().configure("Treeview", rowheight=row_height)

    header = ttk.Frame(root, padding=(16, 12, 16, 0))
    header.pack(fill="x")
    ttk.Label(header, text=APP_TITLE, font=font(16, True)).pack(anchor="w")
    ttk.Label(header, text="Calculate the CDR Global from the CDR boxes (Morris, 1993).").pack(anchor="w")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)
    notebook.add(build_case_tab(notebook), text="Score a case")
    notebook.add(build_csv_tab(notebook), text="Score a CSV file")
    notebook.add(build_rules_tab(notebook), text="Rules")
    notebook.add(build_about_tab(notebook), text="About")

    root.mainloop()


if __name__ == "__main__":
    main()

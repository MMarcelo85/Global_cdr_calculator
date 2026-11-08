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
CONTACT = "mmaito@udesa.edu.ar"


def font(size, bold=False):
    """System default font with another size/weight (call after tk.Tk())."""
    f = tkfont.nametofont("TkDefaultFont").copy()
    f.configure(size=size, weight="bold" if bold else "normal")
    return f


def build_case_tab(parent):
    frame = ttk.Frame(parent, padding=16)
    ttk.Label(frame, text="Select the score for memory and secondary categories.",
              font=font(11, True)).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))

    variables = []
    for row, (key, label) in enumerate(cdr_core.DOMAINS, start=1):
        options = cdr_core.CARE_SCORES if key == "care" else cdr_core.SCORES
        text = label + (" (cannot be 0.5)" if key == "care" else "")
        ttk.Label(frame, text=text).grid(row=row, column=0, sticky="w", padx=(0, 16), pady=3)
        var = tk.StringVar(value="0")
        for col, value in enumerate(options, start=1):
            ttk.Radiobutton(frame, text=cdr_core.fmt(value), value=cdr_core.fmt(value), variable=var,
                            command=lambda: update()).grid(row=row, column=col, sticky="w", padx=6)
        variables.append(var)

    ttk.Separator(frame).grid(row=8, column=0, columnspan=6, sticky="ew", pady=14)
    score_label = ttk.Label(frame, font=font(18, True), foreground="#1f4e9c")
    score_label.grid(row=9, column=0, columnspan=6, sticky="w")
    ttk.Label(frame, text="Applied rule:", font=font(10, True)).grid(
        row=10, column=0, columnspan=6, sticky="w", pady=(10, 2))
    rule_label = ttk.Label(frame, wraplength=620, justify="left")
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
    ttk.Label(frame, text=instructions, wraplength=680, justify="left").pack(anchor="w")

    buttons = ttk.Frame(frame)
    buttons.pack(anchor="w", pady=10)
    summary = ttk.Label(frame, wraplength=680, justify="left")
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
            width = {cdr_core.OUT_RULE: 420, cdr_core.OUT_NOTE: 200, cdr_core.OUT_SCORE: 90}.get(h, 80)
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
    frame = ttk.Frame(parent, padding=16)
    text = tk.Text(frame, wrap="word", relief="flat", padx=8, pady=8, font=font(10))
    text.tag_configure("h", font=font(11, True))
    text.tag_configure("link", foreground="#1f4e9c", underline=True)
    text.tag_bind("link", "<Button-1>", lambda e: webbrowser.open(cdr_core.RULES_URL))
    text.tag_bind("link", "<Enter>", lambda e: text.config(cursor="hand2"))
    text.tag_bind("link", "<Leave>", lambda e: text.config(cursor=""))

    text.insert("end", "CDR Scoring Rules\n", "h")
    text.insert("end", cdr_core.RULES_URL + "\n", "link")
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

    sb = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=sb.set)
    text.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return frame


def main():
    try:  # sharp text on high-DPI Windows screens
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("780x600")
    root.minsize(640, 480)

    header = ttk.Frame(root, padding=(16, 12, 16, 0))
    header.pack(fill="x")
    ttk.Label(header, text=APP_TITLE, font=font(16, True)).pack(anchor="w")
    ttk.Label(header, text="Calculate the CDR Global from the CDR boxes (Morris, 1993).").pack(anchor="w")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)
    notebook.add(build_case_tab(notebook), text="Score a case")
    notebook.add(build_csv_tab(notebook), text="Score a CSV file")
    notebook.add(build_rules_tab(notebook), text="Rules")

    root.mainloop()


if __name__ == "__main__":
    main()

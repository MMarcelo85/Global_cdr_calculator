# Global CDR Calculator

### Simple app to calculate CDR Global

* [CDR Scoring Rules](https://knightadrc.wustl.edu/professionals-clinicians/cdr-dementia-staging-instrument/cdr-scoring-rules/)
**Morris, J.C. (1993). The clinical dementia rating (CDR): Current version and scoring rules. Neurology, 43(11), 2412-2414.**

Two versions with the same scoring code (`cdr_core.py`):

* **Web app:** [run it on Streamlit](https://globalcdrcalculator.streamlit.app/) (`main.py`).
* **Desktop app (Windows / Linux, no installation, works offline):** download
  `CDR_Global_Calculator_Windows.exe` or `CDR_Global_Calculator_Linux` from the
  [Releases page](https://github.com/MMarcelo85/Global_cdr_calculator/releases) and double-click it.
  * Windows may show "Windows protected your PC" (the program is not digitally signed):
    click **More info → Run anyway**.
  * Linux: the first time, run `chmod +x CDR_Global_Calculator_Linux` (or tick "Allow executing file as program" in Properties).
  * Linux packages (adds the app to the applications menu), also on the Releases page:
    * Flatpak: `flatpak install --user CDR_Global_Calculator.flatpak`
    * Snap: `sudo snap install --dangerous CDR_Global_Calculator.snap`
      (`--dangerous` is needed because the snap is not published in the Snap Store).

Both versions let you score a single case (showing the applied rule), view all the rules,
and score a whole CSV file.

### CSV files

* Either exactly 6 columns in this order: Memory, Orientation, Judgment, Community, Home, Personal care
  (e.g. `Memory, box1, box2, box3, box4, box5`),
* or any number of columns where the six CDR columns are named Memory, Orientation, Judgment, Community,
  Home, PersonalCare (Spanish names such as Memoria, Orientación, Juicio, Comunidad, Hogar, Cuidado personal
  and NACC names such as MEMORY, ORIENT, JUDGMENT, COMMUN, HOMEHOBB, PERSCARE also work). Other columns,
  such as IDs, are kept unchanged.
* Comma or semicolon separated; decimal point or decimal comma (`0.5` / `0,5`).
* The output adds `CDR_global`, `Rule_applied` and `CDR_note`. Rows with missing or invalid scores
  (e.g. Personal care = 0.5) are kept, with the reason in `CDR_note`. The original file is never modified.

### Rules:
1. If M = 0, CDR = 0 unless there is impairment (0.5 or greater) in two or more secondary categories, in which case CDR = 0.5.
2. When M = 0.5, CDR = 1 if at least three of the other categories are scored one or greater. Else CDR = 0.5.
3. CDR = M if at least three secondary categories are given the same score as memory.
4. When three secondary categories are scored on one side of M and two secondary categories are scored on the other side of M, CDR=M.
5. Whenever three or more secondary categories are given a score greater or less than the memory score, CDR = score of majority of secondary categories on whichever side of M has the greater number of secondary categories.
6. When M = 1 or greater, CDR cannot be 0; in this circumstance, CDR = 0.5 when the majority of secondary categories are 0.

###### Unusual circumstances occur occasionally in Alzheimer's disease and may be expected in non-Alzheimer dementia as well are scored as follows:

7. With ties in the secondary categories on one side of M, choose the tied scores closest to M for CDR (e.g., M and another secondary category = 3, two secondary categories = 2, and two secondary categories = 1; CDR = 2).
8. When only one or two secondary categories are given the same score as M, CDR = M as long as no more than two secondary categories are on either side of M.

### Development

* Tests: `python -m unittest discover -s tests` (includes all 12,500 possible score combinations).
* Run the web app: `pip install -r requirements.txt` then `streamlit run main.py`.
* Run the desktop app: `python desktop_app.py` (standard library only).
* Build executables: push a tag (`git tag v2.0.0 && git push origin v2.0.0`) and GitHub Actions
  builds the Windows and Linux executables and attaches them to a Release
  (`.github/workflows/build-desktop.yml`). Local build: `pyinstaller --onefile --windowed --name CDR_Global_Calculator desktop_app.py`.

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pandas as pd
import streamlit as st

import cdr_core

st.title("CDR Global calculator.")
st.subheader("A simple app to calculate the CDR global from the CDR boxes.")
st.markdown(" ##### Please, test it, use it and write to mmaito@udesa.edu.ar if you find any scoring errors.")
st.header(f"[CDR Scoring Rules]({cdr_core.RULES_URL})")

rules_md = "\n".join(f"{n}. {text.split(': ', 1)[1]}" for n, text in cdr_core.RULES.items() if n <= 6)
unusual_md = "\n".join(f"{n}. {text.split(': ', 1)[1]}" for n, text in cdr_core.RULES.items() if n > 6)
st.markdown(f"""
**{cdr_core.REFERENCE}**

### Rules:
{rules_md}

###### Unusual circumstances occur occasionally in Alzheimer's disease and may be expected in non-Alzheimer dementia as well are scored as follows:

{unusual_md}
""")

st.markdown("##### Please, select the score for memory and secondary scores.")

values = []
for key, label in cdr_core.DOMAINS:
    options = cdr_core.CARE_SCORES if key == "care" else cdr_core.SCORES
    help_text = "Personal care cannot be scored 0.5" if key == "care" else None
    values.append(st.radio(f"**{label}**", options=options, index=0, horizontal=True, help=help_text))

cdr_global, rule = cdr_core.calculate_cdr(values[0], values[1:])

st.metric(label="**:blue[CDR Global Score]**", value=cdr_core.fmt(cdr_global))
st.markdown("##### Applied rule:")
st.write(rule)

st.markdown("---")
st.markdown(f""" ##### Please, upload your csv file to have your CDR global calculated.
Use either exactly 6 columns in this order: Memory, Orientation, Judgment, Community, Home, Personal care;
or name the columns Memory, Orientation, Judgment, Community, Home, PersonalCare (other columns, such as IDs, are kept).
Comma or semicolon separated files are accepted. The program returns the same csv with the columns
`{cdr_core.OUT_SCORE}`, `{cdr_core.OUT_RULE}` and `{cdr_core.OUT_NOTE}` (reason when a row could not be scored).""")

uploaded_file = st.file_uploader(label="File to calculate CDR Global", type=["csv", "txt"], accept_multiple_files=False)
if uploaded_file:
    try:
        header, rows, out_csv, summary = cdr_core.process_csv(cdr_core.decode(uploaded_file.getvalue()))
    except ValueError as e:
        st.error(str(e))
    else:
        st.success(summary)
        st.write("Preview CDR Global")
        st.dataframe(pd.DataFrame(rows, columns=header), hide_index=True)
        name = os.path.splitext(uploaded_file.name)[0]
        st.download_button(
            label="Download data as CSV",
            data=out_csv.encode("utf-8-sig"),
            file_name=f"{name}_CDR_global.csv",
            mime="text/csv")

# Global CDR Calculator

### Simple app to calculate CDR Global

* [CDR Scoring Rules](https://knightadrc.wustl.edu/professionals-clinicians/cdr-dementia-staging-instrument/cdr-scoring-rules/)
**Morris, J.C. (1993). The clinical dementia rating (CDR): Current version and scoring rules. Neurology, 43(11), 2412-2414.**

[Click here to run it on streamlit](https://globalcdrcalculator.streamlit.app/)

### Rules:
1. If M = 0, CDR = 0 unless there is impairment (0.5 or greater) in two or more secondary categories, in which case CDR = 0.5.
2. When M = 0.5, CDR = 1 if at least three of the other categories are scored one or greater. Else CDR = 0.5
3. CDR = M if at least three secondary categories are given the same score as memory.
4. When three secondary categories are scored on one side of M and two secondary categories are scored on the other side of M, CDR=M.
5. Whenever three or more secondary categories are given a score greater or less than the memory score, CDR = score of majority of secondary categories on whichever side of M has the greater number of secondary categories.
6. When M = 1 or greater, CDR cannot be 0; in this circumstance, CDR = 0.5 when the majority of secondary categories are 0.

###### Unusual circumstances occur occasionally in Alzheimer’s disease and may be expected in non-Alzheimer dementia as well are scored as follows:

7. With ties in the secondary categories on one side of M, choose the tied scores closest to M for CDR (e.g., M and another secondary category = 3, two secondary categories = 2, and two secondary categories = 1; CDR = 2).
8. When only two secondary categories are given the same score as M, CDR = M as long as no more than two secondary categories are on either side of M.  

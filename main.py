import numpy as np
import pandas as pd
import warnings
from io import StringIO
import streamlit as st

warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None

# Function that calculates CDR global from CDR boxes

def calculate_cdr_inline(memory, secondary_categories):
    rules={
        1: "Rule 1: if M = 0, CDR = 0 unless there is impairment (0.5 or greater) in two or more secondary categories, in which case CDR = 0.5.",
        2: "Rule 2: When M = 0.5, CDR = 1 if at least three of the other categories are scored one or greater. Else CDR = 0.5",
        3: "Rule 3: CDR = M if at least three secondary categories are given the same score as memory.",
        4: "Rule 4: When three secondary categories are scored on one side of M and two secondary categories are scored on the other side of M, CDR=M.",
        5: "Rule 5: Whenever three or more secondary categories are given a score greater or less than the memory score, CDR = score of majority of secondary categories on whichever side of M has the greater number of secondary categories.",
        6: "Rule 6: When M = 1 or greater, CDR cannot be 0; in this circumstance, CDR = 0.5 when the majority of secondary categories are 0.",
        7: "Rule 7: With ties in the secondary categories on one side of M, choose the tied scores closest to M for CDR (e.g., M and another secondary category = 3, two secondary categories = 2, and two secondary categories = 1; CDR = 2).",
        8: "Rule 8: When only two secondary categories are given the same score as M, CDR = M as long as no more than two secondary categories are on either side of M."
    }
# Ultima versión 29/12/23
    from collections import Counter
    # Count the number of secondary categories on each side of memory score
    lower_side_count = sum(score < memory for score in secondary_categories)
    higher_side_count = sum(score > memory for score in secondary_categories)
    equal_count = sum(score == memory for score in secondary_categories)
    n0= secondary_categories.count(0)
    n05= secondary_categories.count(0.5)
    n1= secondary_categories.count(1)
    n2= secondary_categories.count(2)
    n3= secondary_categories.count(3)

    # Check for ties
    # Use Counter to count occurrences
    counted_values = Counter(secondary_categories)
    # Find values with the maximum count
    max_count = max(counted_values.values())
    ties = [value for value, count in counted_values.items() if count == max_count]

    
    # Rule 7: With ties in the secondary categories on one side of M, choose the tied scores closest to M
    # for CDR (e.g., M and another secondary category = 3, two secondary categories = 2, and two secondary
    # categories = 1; CDR = 2).
    #m 1, box 0.5, 1, 1, 0, 0
    # Check if there are ties
    if (len(ties) == 2) & (memory >= 1):
        if ((ties[0] > memory) & (ties[1] > memory)) | ((ties[0] < memory) & (ties[1] < memory)):
            rule = rules[7]
            serie = pd.Series(secondary_categories).value_counts(ascending=False)
            categories = list(serie.index)
            counts = list(serie.values)
            distance_idx_0 = memory - categories[0]
            distance_idx_1 = memory - categories[1]
            
            if (categories[0]<1) & (categories[1]<1) & (memory == 1):
                return 0.5, rule
            elif (categories[0]<memory) & (categories[1]<memory) & (distance_idx_0 < distance_idx_1):
                return categories[0], rule
            elif (categories[0]<memory) & (categories[1]<memory) & (distance_idx_0 > distance_idx_1):
                return categories[1], rule
            elif (categories[0]>memory) & (categories[1]>memory) & (distance_idx_0 < distance_idx_1):
                return categories[0], rule
            elif (categories[0]>memory) & (categories[1]>memory) & (distance_idx_0 > distance_idx_1):
                return categories[1], rule
            elif (distance_idx_0 == distance_idx_1):
                return min(categories[0], categories[1]), rule
            
    # Rule 8: When only one or two secondary categories are given the same score as M, CDR = M as long as
    # no more than two secondary categories are on either side of M.
    if ((equal_count == 1) | (equal_count==2)) & (lower_side_count <= 2) & (higher_side_count <=2):
        rule=rules[8]
        return memory, rule


    # Rule 1: If M = 0, CDR = 0 unless there is impairment (0.5 or greater) in two or more secondary categories,
    # in which case CDR = 0.5.
    if memory == 0:
        rule=rules[1]
        if secondary_categories.count(0.5) + secondary_categories.count(1) + secondary_categories.count(2) + secondary_categories.count(3) >= 2:
            return 0.5, rule
        else:
            return 0, rule

    # Rule 2: When M = 0.5, CDR = 1 if at least three of the other categories are scored one or greater.
    #         Else M = 0.5
    if memory == 0.5:
        rule=rules[2]
        if secondary_categories.count(1) + secondary_categories.count(2) + secondary_categories.count(3) >= 3:
            return 1, rule
        else:
            return 0.5, rule

    # Rule 3: CDR = M if at least three secondary categories are given the same score as memory
    ## Count the number of secondary categories equal to memory score
    equal_memory_count = secondary_categories.count(memory)
    if (equal_memory_count >= 3) & (memory>0.5):
        rule=rules[3]
        return memory, rule
    
    # Rule 6: When M = 1 or greater, CDR cannot be 0; in this circumstance, CDR = 0.5 when
    # the majority of secondary categories are 0
    
    if (memory >= 1) & (n0 >n05) & (n0 >n1) & (n0 >n2) & (n0 >n3):    
        rule=rules[6]
        return 0.5, rule
    
    # Rule 4: When three secondary categories are scored on one side of M and two secondary categories
    # are scored on the other side of M, CDR=M
    if (lower_side_count == 2) & (higher_side_count == 3):
        rule=rules[4]
        return memory, rule
    elif (lower_side_count == 3) & (higher_side_count == 2):
        rule=rules[4]
        return memory, rule

    # Rule 5: Whenever three or more secondary categories are given a score greater or less than the memory
    # CDR = score of the majority of secondary categories on whichever side of M has the
    # greater number of secondary categories
    if (memory > 0.5) & ((lower_side_count >= 3) | (higher_side_count >= 3)):
        rule=rules[5]
        print(f"Lower: {lower_side_count}, Upper: {higher_side_count}")
        print(f"Most frequent category: {pd.Series(secondary_categories).value_counts(ascending=False).index[0]}")
        print(pd.Series(secondary_categories).value_counts(ascending=False))
        
        serie = pd.Series(secondary_categories).value_counts(ascending=False)
        categories = list(serie.index)
        counts = list(serie.values)
        if len(counts) == 1:
            return categories[0], rule

        if (len(categories)== 4) & (lower_side_count==3) & (serie.index[0] == memory):
            sub_serie = serie.drop(memory, axis=0).sort_index(ascending=False).index[0]
            return sub_serie, rule
        
        elif (len(categories)== 4) & (lower_side_count==3) & (serie.index[0] != memory):
            sub_serie = serie.index[0]
            return sub_serie, rule             
        
        distance_idx_0 = memory - categories[0]
        distance_idx_1 = memory - categories[1]
        
        if(memory != categories[0]) & (categories[0]!=0):
            return categories[0], rule
        elif (memory != categories[1]) & (categories[1]!=0):
            return categories[1], rule
        else:
            return 0.5, rule


        
# Ultima versión 29/12/23
def calculate_cdr(memory, secondary_categories):
    """
    memory (int): 0, 0.5, 1, 2
    secondary_categories (list): list of box scores .i.e [1, 1, 1, 0.5, 2]
    """
    from collections import Counter
    # Count the number of secondary categories on each side of memory score
    lower_side_count = sum(score < memory for score in secondary_categories)
    higher_side_count = sum(score > memory for score in secondary_categories)
    equal_count = sum(score == memory for score in secondary_categories)
    n0= secondary_categories.count(0)
    n05= secondary_categories.count(0.5)
    n1= secondary_categories.count(1)
    n2= secondary_categories.count(2)
    n3= secondary_categories.count(3)

    # Check for ties
    tie = False
    # Use Counter to count occurrences
    counted_values = Counter(secondary_categories)
    # Find values with the maximum count
    max_count = max(counted_values.values())
    ties = [value for value, count in counted_values.items() if count == max_count]

    
    # Rule 7: With ties in the secondary categories on one side of M, choose the tied scores closest to M
    # for CDR (e.g., M and another secondary category = 3, two secondary categories = 2, and two secondary
    # categories = 1; CDR = 2).
    #m 1, box 0.5, 1, 1, 0, 0
    # Check if there are ties
    if (len(ties) == 2) & (memory >= 1):
        tie=True
        if ((ties[0] > memory) & (ties[1] > memory)) | ((ties[0] < memory) & (ties[1] < memory)):
            print("Rule 7")
            serie = pd.Series(secondary_categories).value_counts(ascending=False)
            categories = list(serie.index)
            counts = list(serie.values)
            distance_idx_0 = memory - categories[0]
            distance_idx_1 = memory - categories[1]
            
            if (categories[0]<1) & (categories[1]<1) & (memory == 1):
                return 0.5
            elif (categories[0]<memory) & (categories[1]<memory) & (distance_idx_0 < distance_idx_1):
                return categories[0]
            elif (categories[0]<memory) & (categories[1]<memory) & (distance_idx_0 > distance_idx_1):
                return categories[1]
            elif (categories[0]>memory) & (categories[1]>memory) & (distance_idx_0 < distance_idx_1):
                return categories[0]
            elif (categories[0]>memory) & (categories[1]>memory) & (distance_idx_0 > distance_idx_1):
                return categories[1]
            elif (distance_idx_0 == distance_idx_1):
                return min(categories[0], categories[1])
            
    # Rule 8: When only one or two secondary categories are given the same score as M, CDR = M as long as
    # no more than two secondary categories are on either side of M.
    if ((equal_count == 1) | (equal_count==2)) & (lower_side_count <= 2) & (higher_side_count <=2):
        print("Rule 8")
        return memory


    # Rule 1: If M = 0, CDR = 0 unless there is impairment (0.5 or greater) in two or more secondary categories,
    # in which case CDR = 0.5.
    if memory == 0:
        print("Rule 1")
        if secondary_categories.count(0.5) + secondary_categories.count(1) + secondary_categories.count(2) + secondary_categories.count(3) >= 2:
            return 0.5
        else:
            return 0

    # Rule 2: When M = 0.5, CDR = 1 if at least three of the other categories are scored one or greater.
    #         Else M = 0.5
    if memory == 0.5:
        print("Rule 2")
        if secondary_categories.count(1) + secondary_categories.count(2) + secondary_categories.count(3) >= 3:
            return 1
        else:
            return 0.5

    # Rule 3: CDR = M if at least three secondary categories are given the same score as memory
    ## Count the number of secondary categories equal to memory score
    equal_memory_count = secondary_categories.count(memory)
    if (equal_memory_count >= 3) & (memory>0.5):
        print("Rule 3")
        return memory
    
    # Rule 6: When M = 1 or greater, CDR cannot be 0; in this circumstance, CDR = 0.5 when
    # the majority of secondary categories are 0
    
    if (memory >= 1) & (n0 >n05) & (n0 >n1) & (n0 >n2) & (n0 >n3):    
        print("Rule 6")
        return 0.5
    
    # Rule 4: When three secondary categories are scored on one side of M and two secondary categories
    # are scored on the other side of M, CDR=M
    if (lower_side_count == 2) & (higher_side_count == 3):
        print("Rule 4")
        return memory
    elif (lower_side_count == 3) & (higher_side_count == 2):
        print("Rule 4")
        return memory

    # Rule 5: Whenever three or more secondary categories are given a score greater or less than the memory
    # CDR = score of the majority of secondary categories on whichever side of M has the
    # greater number of secondary categories
    if (memory > 0.5) & ((lower_side_count >= 3) | (higher_side_count >= 3)):
        print('Rule 5')
        print(f"Lower: {lower_side_count}, Upper: {higher_side_count}")
        print(f"Most frequent category: {pd.Series(secondary_categories).value_counts(ascending=False).index[0]}")
        print(pd.Series(secondary_categories).value_counts(ascending=False))
        
        serie = pd.Series(secondary_categories).value_counts(ascending=False)
        categories = list(serie.index)
        counts = list(serie.values)
        if len(counts) == 1:
            return categories[0]

        if (len(categories)== 4) & (lower_side_count==3) & (serie.index[0] == memory):
            sub_serie = serie.drop(memory, axis=0).sort_index(ascending=False).index[0]
            return sub_serie
        
        elif (len(categories)== 4) & (lower_side_count==3) & (serie.index[0] != memory):
            sub_serie = serie.index[0]
            return sub_serie                
        
        distance_idx_0 = memory - categories[0]
        distance_idx_1 = memory - categories[1]
        
        if(memory != categories[0]) & (categories[0]!=0):
            return categories[0]
        elif (memory != categories[1]) & (categories[1]!=0):
            return categories[1]
        else:
            return 0.5



st.title("CDR Global calculator.")
st.subheader("A simple app to calculate the CDR global from the CDR boxes.")
st.markdown(" ##### Please, test it, use it and write to mmaito@udesa.edu.ar if you find any scoring errors.")
st.header(""" [CDR Scoring Rules](https://knightadrc.wustl.edu/professionals-clinicians/cdr-dementia-staging-instrument/cdr-scoring-rules/)""")

st.markdown("""  
**Morris, J.C. (1993). The clinical dementia rating (CDR): Current version and scoring rules. Neurology, 43(11), 2412-2414.**

            
### Rules:
1. If M = 0, CDR = 0 unless there is impairment (0.5 or greater) in two or more secondary categories, in which case CDR = 0.5.
2. When M = 0.5, CDR = 1 if at least three of the other categories are scored one or greater. Else M = 0.5
3. CDR = M if at least three secondary categories are given the same score as memory.
4. When three secondary categories are scored on one side of M and two secondary categories are scored on the other side of M, CDR=M.
5. Whenever three or more secondary categories are given a score greater or less than the memory score, CDR = score of majority of secondary categories on whichever side of M has the greater number of secondary categories.
6. When M = 1 or greater, CDR cannot be 0; in this circumstance, CDR = 0.5 when the majority of secondary categories are 0.

###### Unusual circumstances occur occasionally in Alzheimer’s disease and may be expected in non-Alzheimer dementia as well are scored as follows:

7. With ties in the secondary categories on one side of M, choose the tied scores closest to M for CDR (e.g., M and another secondary category = 3, two secondary categories = 2, and two secondary categories = 1; CDR = 2).
8. When only two secondary categories are given the same score as M, CDR = M as long as no more than two secondary categories are on either side of M.  

        """)

st.markdown("##### Please, select the score for memory and secundary scores.")

### Selectbox
memory = st.radio(f"**Memory**", options=(0, 0.5, 1, 2, 3), index=0, horizontal=True)
orientation = st.radio(f"**Orientation**", options=(0, 0.5, 1, 2, 3), index=0, horizontal=True)
problem = st.radio(f"**Judgment and Problem Solving**", options=(0, 0.5, 1, 2, 3), index=0, horizontal=True)
community = st.radio(f"**Community Affairs**", options=(0, 0.5, 1, 2, 3), index=0, horizontal=True)
home = st.radio(f"**Home and Hobbies**", options=(0, 0.5, 1, 2, 3), index=0, horizontal=True)
care = st.radio(f"**Personal Care**", options=(0, 1, 2, 3), index=0, horizontal=True, help="Personal care cannot be scored 0.5")
secondary_categories = [orientation, problem, community, home, care]

cdr_global, rule = calculate_cdr_inline(memory=memory, secondary_categories=secondary_categories)

st.metric(label="**:blue[CDR Global Score]**", value=cdr_global, delta=None)
st.markdown(f"##### Applied rule:")
st.write(f"{rule}")

st.markdown("---")
st.markdown(""" ##### Please, uploade your csv file yo have your cdr global calculated.
 First row must be columna names in this order: Memory, box1, box2, box3, box4, box5.
 The programm returns the same csv with the CDR_global column for each row""")

uploaded_file = st.file_uploader(label="File to calculate CDR Global", accept_multiple_files=False)
if uploaded_file:

    pd_file = pd.read_csv(uploaded_file)
    rows = pd_file.shape[0]
    results =[]

    for row in range(len(pd_file)):
        m = pd_file.iloc[row,0]
        sc = list(pd_file.iloc[row, 1:].values)
        cdr = calculate_cdr(memory=m, secondary_categories=sc)
        results.append(cdr)


    pd_file['CDR_global'] = results
    st.write("Preview CDR Global")
    st.table(pd_file.head().style.format("{:.1f}"))

    data_as_csv= pd_file.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download data as CSV",
        data=data_as_csv,
        file_name="Calculated CDR_global.csv",
        mime="text/plain")
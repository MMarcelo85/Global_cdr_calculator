# Data table to sleuth file

### Simple app to convert excel and csv files to sleuth format

[Click here to run it on streamlit](https://tabletosleuth.streamlit.app/)


* The app can load excel files (xlsx and xls) and text files (csv, txt, tsv, etc)
* Set the delimiter for text files
* Set skiprows (from 0 to 9)
* Load and download multiple files.

- Columns shlould be ordered in the following way:
Coordinates - one column for each coordinate ('x', 'y', 'z')- ,'Study' and 'N'.
All other variables will be ignored. If variables have other names, correct them and come back later.  

- The space should be declared in de Space tab (MNI or TAL). Note: All studies must be in the same space. If not, you can use GINGER ALE app to convert to a different space.


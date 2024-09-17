# presto-football-xmlparser
PrestoStats Football - XML parser for use in NewTek LiveText/DataLink
- 9/17/2024: As of right now, the program only parses player passing statistics, this will be updated in the future for more statistics.
- Tested on Windows.

Written by Trae Toelle, Athletics Live Video Producer at [Kansas Wesleyan University](https://kwucoyotes.com)

This program takes a PrestoStats/StatCrew XML file and parses it to get specific player data for use in NewTek LiveText/DataLink on TriCasters.


## Prerequisites
- [Python 3.10+](https://www.python.org/downloads/)
  - Make sure you select to add Python to enviroment variables on install.
- lxml and requests Python libraries, install using PIP.
  - `pip install lxml requests`

## Instructions for use
Run the program in PowerShell or Command Prompt.
`py prestoSyncLiveText.py`

First, point the program to your Presto XML file path, this can be a local file directly from PrestoSync, or it can be pulled from the web if you have stat partners set up. 
- You **must** specify a filename at the end of the filepath, otherwise the program will fail to function.
- If using a web source, you **must** include `https://` or `http://` at the beginning of your URL, otherwise the program will fail to function.
  
Secondly, point the program to where you want your output XML file to go. As of right now there is no FTP support for this program, so only local file output is allowed.
- Default file output is "output.xml" in the program's working directory.
- Network paths in Windows, such as `\\TRICASTER-MINI\DataLink Watch\output.xml` are accepted.

If everything works correctly, the program will ask for team selection, and player selection.
- Queries stats for selected player every 5 seconds until stopped by user.
- Query time can be changed by user in Python file if desired. 


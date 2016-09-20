# JoeThesis
Phenological mismatch of paleovegetation.







#### Running the Neotoma/Climate Script
1.  Go to the Williams Lab Computer 
2.  Open a command shell py clicking the windows icon in the lower left and typing <kbd>cmd</kbd> + <kbd>Enter</kbd>.
3.  Change directories into the Github folder where the code lives. ```cd documents/github/JoeThesis```
4.  Decide what taxon you want to search for and any wild cards you want to use by looking [here](http://api.neotomadb.org/doc/use)
5.  Run the script using python. In the command prompt, type ```python neotoma_to_space_time_climate.py [[Neotoma_SearchString]] [[Name_of_the_file_you_want.csv]]```, replacing ```[[Neotoma_SearchString]]``` with the search string you came up with in step 4 and ```[[Name_of_the_file_you_want.csv]]``` with the name of the file you want to save, e.g., ```Quercus.csv```.  Files can be relative or absolute paths.
6.  Press <kbd>Enter</kbd>
7.  Wait for the script to finish running. It will alert you to its progress along the way.
8.  Open the csv file ```[[Name_of_the_file_you_want.csv]]``` in excel or R when it's finished. 

NB: ```NeotomaLocations.csv``` is an intermediate file and only has locations and times, without climate. It gets overwritten each time the script is called.

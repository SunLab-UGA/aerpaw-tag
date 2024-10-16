
Usage:
main('folder','resulttype')
where 'folder' is the folder that contains the following three files
GPS_DATA.csv
pingResultsEPC.txt
pingResultsUE.txt
Example
main('test4','UE') : Inside test4 folder generate results from UE data 
main('demo2','EPC') : : Inside test4 folder generate results from UE data

legends.m adds legends to the plots and saves them as jpg format.
KML file generation
main.m creates UE_input.csv (or EPC_input.csv) inside the 'folder'. 
kml_generator.py is modified to plot values between 0 and 1
def generate_color(val, min_val = 0, max_val = 1, colors = COLORS):
COLORS is modified to generate different colors for success and failure of the pings. 

COLORS = [BLUE, RED]    
or
COLORS = [YELLOW, GREEN]    

Usage
python3 kml_generator.py --input test4/UE_input.csv --output test4/testbed.kml

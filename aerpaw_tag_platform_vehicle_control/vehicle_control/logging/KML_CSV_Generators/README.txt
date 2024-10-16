csv_generator.py
Log file preprocessing for KML generation

Original code by Byron Qi
Modified/modernized by John Kesler

This script is fed a zip file containing two subdirectories, 'gps/' and 'lte/',
both of which contain log files generated from our datalogging programs
(gps_logger.py and cell_search.c). The log files from gps_logger are expected to
have 'GPS_DATA' somewhere in the path, and likewise the ones from cell_search
should have 'logfile' in their path.

The output of this script is a single csv file that contains a row for each data
point in the lte data fed in combined with a cooresponding data point from the
gps data fed in. The script will use the GPS point immediately before (and
closest) to the cooresponding RF data.

This can be run by using:
    python csv_generator.py --input <input> --output <output>

There is some help offered by using the --help flag.

Parameters:
    --input:    path to the zip file containing the data
    --output:   path to the produced csv file (will be created)

A given row in the output file looks like:
    index,timestamp,longitude,latitude,altitude,RSRP signal

--------------------------------------------------------------------------------

gen_fake_lte_logs.py
Tool to generate dummy LTE log files

Original code by John Kesler

Requirements:
    perlin-noise

This script is a tool that connects to a vehicle (being run in SITL, most
likely), samples its location over time, and spits out a set of output CSVs that
resemble the output from the cell_search.c script. The only column populated with
dummy data (that isn't just zeroes) is the one recording signal strength -- this
is filled with output from a perlin noise generator fed with the position of the
vehicle.

This can be run by using:
    python gen_fake_lte_logs.py --output <output dir> --conn <connection string>

There is some help offered by using the --help flag.

Parameters:
    --output:   path to the directory to dump generated csv files in
    --conn:     connection string to talk with vehicle
    --seed:     [optional, default=unix time] seed for the perlin noise generator
    --rate:     [optional, default=20] rate in Hz to collect samples

--------------------------------------------------------------------------------

kml_generator.py
Convert processed CSV file into KML

Original code by Byron Qi

This script is broken down into a few parts:
    get_image() is passed the RSRP signal dB of a given data point and
                recolorizes 'scatter.png'
    kml_gen()   is fed lines from the input csv file and transforms the input
                csv data into a kml-formatted output file, appending if the file
                already exists

This can be run by using:
    python kml_generator.py --input <input csv> --output <output kml>

There is some help offered by using the --help flag

Parameters:
    --input:    path to input CSV file created by csv_generator.py
    --output:   path to output KML file
    --images:   path to scatter image folder

To add more data to nodes:          <- NOTE: this could (should!) be refactored.
    Add new parameter to kml_gen() type signature and pass in data from read in
        csv rows (using row[] variable) to kml_gen calls
    In the kml.write calls, add a new `%s,` to the existing `%s`s under the
        <description> tag, and then pass in the new value to the format string

To change the color of icons:
    Adjust constants at the top of the file

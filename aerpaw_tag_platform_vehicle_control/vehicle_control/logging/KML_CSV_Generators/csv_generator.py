#!/usr/bin/python3

"""
Generator that parses and combines GPS and antenna log data into a single csv
file.

Usage:
    python csv_generator.py --input <zipped log files> --output <output csv file>

Expectations:
    The zipped log files should contain two subdirectories: 'gps', and 'lte',
    each of these dirs will contain the log files to be processed.

Output format:
    CSV file as given by <output>
    timestamp is of format yyyy-mm-ddThh:mm:ssZ
    index,timestamp,longitude,latitude,altitude,RSRP signal (dB)
"""

import csv
from datetime import datetime
import os
import shutil
import sys
from typing import Callable, List, Tuple
import zipfile

_DEFAULT_WORKING_PATH = 'tmp'
_GPS_DIR = 'gps'
_LTE_DIR = 'lte'

def _prepare_working_dir(zip_path: str, working_dir: str=_DEFAULT_WORKING_PATH) -> Tuple[List[str], List[str]]:
    """
    prepare working dir by extracting files

    returns gps_files[], lte_files[]
    """
    shutil.rmtree(working_dir, True)
    with zipfile.ZipFile(zip_path, 'r') as f:
        f.extractall(working_dir)
    
    # TODO the pattern of enforcing filenames is brittle. remove
    get_files = lambda path, substr: [os.path.join(path, f) for f in os.listdir(path)
            if os.path.isfile(os.path.join(path, f)) and substr in f]

    gps_path = os.path.join(working_dir, _GPS_DIR)
    lte_path = os.path.join(working_dir, _LTE_DIR)

    return get_files(gps_path, "GPS_DATA"), get_files(lte_path, "logfile")

def _load_data_files(files: List[str], expected_cols: int, header_lines: int=0) -> List[List[str]]:
    """
    concatenate all csv files in a given list of files together
    
    expected_cows <int>:      the # of cols needed in a line to use it
    header_lines  <optional>: the # of lines to skip at the beginning of a file
    """
    # NOTE: it's probably more efficient to use linux magic to treat as stream
    file_data = []
    for filename in files:
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            for _ in range(header_lines):
                next(reader)
            for row in reader:
                if len(row) != expected_cols:
                    continue
                file_data.append([i.strip() for i in row])

    return file_data

def _transform_idx(row: List, idx: int, transformation: Callable) -> List:
    return row[:idx] + [transformation(row[idx])] + row[idx+1:]

def convert_files(zip_path: str, output_file: str) -> None:
    # unzip and load file data
    gps_files, lte_files = _prepare_working_dir(zip_path)

    if len(gps_files) == 0:
        sys.exit("Error: No GPS files found.")
    elif len(lte_files) == 0:
        sys.exit("Error: No LTE files found.")

    # parse into single gps and radio log file data structs
    gps_data = _load_data_files(gps_files, 8)
    lte_data = _load_data_files(lte_files, 15, 3)

    # convert lists to use datetime timestamps and sort by them
    get_gps_time = lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f")
    get_lte_time = lambda x: datetime.strptime(x, "%a %b %d %H:%M:%S %Y")
    
    gps_data = sorted(
            map(lambda row: _transform_idx(row, 5, get_gps_time), gps_data),
            key=lambda row: row[5])
    lte_data = sorted(
            map(lambda row: _transform_idx(row, 14, get_lte_time), lte_data),
            key=lambda row: row[14])

    # combine and write to output file
    # each new point is an LTE point with the closest GPS point before it
    gps_idx = 0
    writing = False
    with open(output_file, 'a+') as f:
        initial_line = sum(1 for _ in f)
        writer = csv.writer(f)
        
        for line, lte_row in enumerate(lte_data):
            next_time = lte_row[14]
            
            found_new_idx = False
            for idx, gps_row in enumerate(gps_data[gps_idx:]):
                if not writing and gps_row[5] < next_time:
                    # only start after getting the streams in line
                    writing = True
                elif gps_row[5] > next_time and idx + gps_idx > 0:
                    gps_idx = idx + gps_idx - 1
                    found_new_idx = True
                    break
            if not found_new_idx:
                print("GPS data exhausted")
                return
            gps_row = gps_data[gps_idx]
            
            if writing:
                writer.writerow([
                    initial_line + line,                        # line num
                    lte_row[14].strftime("%Y-%m-%dT%H:%M:%SZ"), # timestamp
                    gps_row[1],                                 # lon
                    gps_row[2],                                 # lat
                    gps_row[3],                                 # alt
                    lte_row[11]                                 # RSRP signal
                    ])
        
        print("LTE data exhausted")
        return

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-i", "--input", help="zip containing log files",
            required=True)
    parser.add_argument("-o", "--output", help="path of output csv file",
            required=True)
    args = parser.parse_args()
    
    convert_files(args.input, args.output)

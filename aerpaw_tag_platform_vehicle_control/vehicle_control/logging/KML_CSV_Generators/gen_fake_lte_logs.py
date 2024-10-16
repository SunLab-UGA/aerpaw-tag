#!/usr/bin/python3

"""
Generate fake lte logs for testing without actually having access to the needed
hardware. This is just dummy data generated based off gradient noise taking the
vehicle's GPS position into account (via. a MAVLink connection). Files will be
output into the specified directory.

Usage:
    python gen_fake_lte_logs.py --output <output dir> --conn <conn string>

Output format:
    Found CELL MHz, <freq>,  EARFCN, <dl_earfcn>, PHYID, <cell id>, PRB,
        <cell nof_prb>,  ports, <cell ports>, PSS power dBm, <power in dBm>,
         PSR, <cell psr>, <c asctime timestamp>

Our datalogging only cares about the power and timestamp (<power in dBm> and
<c asctime timestamp>), so the rest will just be given constant blank values
for now.

Requirements:
    perlin-noise
"""

import csv
from math import log10
import os
from signal import SIGINT, SIGTERM, signal
import sys
import time
from typing import Callable

import dronekit
import perlin_noise

PERLIN_SCALE = 100

def _create_noise(seed: int) -> Callable:
    noise = perlin_noise.PerlinNoise(octaves=10, seed=seed)
    return lambda lat, lon, alt: \
            noise.noise([lat*PERLIN_SCALE, lon*PERLIN_SCALE, alt])

def _dump_line(vehicle: dronekit.Vehicle, writer: object, noise_function: Callable) -> None:
    position_relative = vehicle.location.global_relative_frame
    lat, lon = [float(f"{i}") for i in [position_relative.lat, position_relative.lon]]
    alt = round(float(f"{position_relative.alt}"), 3)
    raw_strength = abs(noise_function(lat, lon, alt))
    db_strength = 10*log10(raw_strength) # NOTE: yeah, this is kinda fake but whatever

    writer.writerow([
        " Found CELL MHz", " 0",
        "  EARFCN", " 0",
        " PHYID", " 0",
        " PRB", " 0",
        "  ports", " 0",
        " PSS power dBm", f" {db_strength:.1f}",
        "  PSR", " 0",
        f" {time.asctime()}"
        ])

def periodic_dump(conn_str: str, output_dir: str, sample_rate: int, \
        noise_function: Callable) -> None:
    vehicle = dronekit.connect(conn_str, wait_ready=True)
    sampling_delay = 1 / sample_rate
    next_sample_time = 0
    
    cur_sample = 0
    cur_file = cur_filename = writer = None

    def _clean_up(signum, frame):
        if cur_file != None:
            cur_file.close()
        vehicle.close()
        sys.exit(0)

    signal(SIGINT, _clean_up)
    signal(SIGTERM, _clean_up)

    while True:
        if time.time() > next_sample_time:
            next_sample_time = time.time() + sampling_delay
            if cur_sample % 1000 == 0:
                cur_filename = f"logfile{cur_sample // 1000:03}.csv"
                cur_file = open(os.path.join(output_dir, cur_filename), 'w')
                writer = csv.writer(cur_file)
            _dump_line(vehicle, writer, noise_function)
            cur_sample += 1

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("--output", help="output directory", required=True)
    parser.add_argument("--conn", help="connection string", required=True)
    parser.add_argument("--seed", help="seed for the RNG", required=False,
            default=int(time.time()))
    parser.add_argument("--rate", help="sampling rate (Hz)", required=False,
            default=20)
    args = parser.parse_args()

    periodic_dump(args.conn, args.output, args.rate, _create_noise(args.seed))


#!/bin/bash

# Script to test CPU load imposed by a simple disk read operation
#
# Copyright (c) 2016 Canonical Ltd.
#
# Authors
#   Rod Smith <rod.smith@canonical.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# The purpose of this script is to run disk stress tests using the
# stress-ng program.
#
# Usage:
#   disk_cpu_load.sh [ --max-load <load> ] [ --xfer <mebibytes> ]
#                    [ --verbose ] [ <device-filename> ]
#
# Parameters:
#  --max-load <load> -- The maximum acceptable CPU load, as a percentage.
#                       Defaults to 30.
#  --xfer <mebibytes> -- The amount of data to read from the disk, in
#                        mebibytes. Defaults to 4096 (4 GiB).
#  --verbose -- If present, produce more verbose output
#  <device-filename> -- This is the WHOLE-DISK device filename (with or
#                       without "/dev/"), e.g. "sda" or "/dev/sda". The
#                       script finds a filesystem on that device, mounts
#                       it if necessary, and runs the tests on that mounted
#                       filesystem. Defaults to /dev/sda.


# set -e


def get_params():
    disk_device = "/dev/sda"
    # disk_device = '/home/ubuntu'
    verbose = 0
    max_load = 30
    xfer = 4096
    while len(sys.argv) > 1:
        if sys.argv[1] == "--max-load":
            max_load = int(sys.argv[2])
            sys.argv = sys.argv[2:]
        elif sys.argv[1] == "--xfer":
            xfer = int(sys.argv[2])
            sys.argv = sys.argv[2:]
        elif sys.argv[1] == "--verbose":
            verbose = 1
        else:
            disk_device = "/dev/" + sys.argv[1]
            disk_device = disk_device.replace("//dev", "/dev", 1)
            if not os.path.exists(disk_device):
                print(f"Unknown block device \"{disk_device}\"")
                print("Usage: disk_cpu_load.sh [ --max-load <load> ] [ --xfer <mebibytes> ] [ device-file ]")
                sys.exit(1)
        sys.argv = sys.argv[2:]

    return disk_device, verbose, max_load, xfer


# Find the sum of all values in an array
# Input:
#   $1 - The array whose values are to be summed
# Output:
#   $total - The sum of the values
def sum_array(array):
    total = 0
    for i in array:
        total += i
    return total


# Compute's CPU load between two points in time.
# Input:
#   $1 - CPU statistics from /proc/stat from START point, in a string of numbers
#   $2 - CPU statistics from /proc/stat from END point, in a string of numbers
#   These values can be obtained via $(grep "cpu " /proc/stat | tr -s " " | cut -d " " -f 2-)
# Output:
#   $cpu_load - CPU load over the two measurements, as a percentage (0-100)
def compute_cpu_load(start_stats, end_stats, verbose):
    start_use = start_stats.split()
    end_use = end_stats.split()
    diff_idle = int(end_use[3]) - int(start_use[3])

    start_total = sum_array(start_use)
    end_total = sum_array(end_use)

    diff_total = end_total - start_total
    diff_used = diff_total - diff_idle

    if verbose == 1:
        print("Start CPU time =", start_total)
        print("End CPU time =", end_total)
        print("CPU time used =", diff_used)
        print("Total elapsed time =", diff_total)

    if diff_total != 0:
        cpu_load = (diff_used * 100) / diff_total
    else:
        cpu_load = 0

    return cpu_load


def main():
    disk_device, verbose, max_load, xfer = get_params()
    retval = 0
    print("Testing CPU load when reading", xfer, "MiB from", disk_device)
    print("Maximum acceptable CPU load is", max_load)
    start_load = subprocess.check_output(["grep", "cpu ", "/proc/stat"]).decode("utf-8").strip().split()[1:]
    start_load = " ".join(start_load)
    if verbose == 1:
        print("Beginning disk read....")
    try:
        subprocess.run(["dd", "if=" + disk_device, "of=/dev/null", "bs=1048576", "count=" + str(xfer)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print("Error executing the 'dd' command:")
        print(e.stderr.decode("utf-8"))
        sys.exit(1)
    if verbose == 1:
        print("Disk read complete!")
    end_load = subprocess.check_output(["grep", "cpu ", "/proc/stat"]).decode("utf-8").strip().split()[1:]
    end_load = " ".join(end_load)
    cpu_load = compute_cpu_load(start_load, end_load, verbose)
    print("Detected disk read CPU load is", cpu_load)
    if cpu_load > max_load:
        retval = 1
        print("*** DISK CPU LOAD TEST HAS FAILED! ***")
    sys.exit(retval)


if __name__ == "__main__":
    import subprocess
    import sys
    import os.path

    main()
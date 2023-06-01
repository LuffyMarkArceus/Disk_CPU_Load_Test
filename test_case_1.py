#!/usr/bin/env python3

import subprocess
import sys
import os.path
import paramiko
from getpass import getpass


def get_params():
    disk_device = "/dev/sda"
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


def sum_array(array):
    total = 0
    for i in array:
        total += i
    return total


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


def test_ssh_connectivity(hostname, port, username, password, private_key_path):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Test SSH Connectivity with Password Authentication
        client.connect(hostname, port=port, username=username, password=password)
        print("SSH connection established with password authentication.")
        client.close()

        # Test SSH Connectivity with Key-based Authentication
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
        client.connect(hostname, port=port, username=username, pkey=private_key)
        print("SSH connection established with key-based authentication.")
        client.close()

        return True
    except paramiko.AuthenticationException as auth_exc:
        print("Authentication failed:", str(auth_exc))
    except paramiko.SSHException as ssh_exc:
        print("SSH connection failed:", str(ssh_exc))
    except Exception as exc:
        print("An error occurred:", str(exc))

    return False


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
    # Disk CPU Load Test Parameters
    disk_device, verbose, max_load, xfer = get_params()

    # SSH Connectivity Test Parameters - Provide the details here for your connection
    hostname = "remote-server.example.com"
    port = 22
    username = "your-username"  
    # private_key_path = "/path/to/private_key"

    # Test SSH Connectivity
    password = getpass("Enter your password: ")
    test_ssh_connectivity(hostname, port, username, password, private_key_path)

    # Run Disk CPU Load Test
    main()
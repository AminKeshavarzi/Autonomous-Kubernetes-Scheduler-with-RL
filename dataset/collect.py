import threading
from queries import get_cpu_usage, get_mem_usage, get_disk_usage
import time
from typing import Callable, Dict
import argparse

stop_threads = False

def collect(func: Callable[[str], Dict], ip:str, results:list, index:int) -> None:
    """collects the data from the given function and stores it in the shared list

    This function queries Prometheus using the provided `func` callable,
    retrieves telemetry metrics for the given `ip`, and stores the results
    in the specified index of the shared `results` list. We can define function 
    for different metrics and pass it to this function to collect the data.

    Args:
        func (Callable[[str], Dict]): the name of the function to query prometheus
        ip (str): ip of workernode of a cluster
        results (list): the name of shared list to store the telemetry metrics
        index (int): the index of the shared list to store the telemetry metrics

    Returns:
        None: This function does not return anything.

    Raises:
        KeyError: If expected keys ('data', 'result', 'value') are missing from the `response` dictionary.
        IndexError: If the `result` or `value` lists are shorter than expected.
        TypeError: If the `response` is not structured as a dictionary or its nested elements are of incorrect types.
        Exception: For any other generic exceptions that occur during execution.

    """    
    global stop_threads
    try:
        response = func(ip)  # Call the function
        if 'data' in response and 'result' in response['data']:
            if len(response['data']['result']) > 0:
                result = response['data']['result'][0]
                if 'value' in result and len(result['value']) > 1:
                    value = result['value'][1]
                    results[index] = value  # Store the result in the shared list
                else:
                    print(f"Thread {index} encountered an error: value list is too short")
            else:
                print(f"Thread {index} encountered an error: result list is empty")
        else:
            print(f"Thread {index} encountered an error: invalid response structure, response: {response}")
    except Exception as e:
        print(f"Thread {index} encountered an error: {e}, {index}")

def generate_data(ips:list) -> list:
    """call the collect function for each metric and store the results in a list

    Args:
        ips (list): the ips of the workernodes of a cluster

    Returns:
        list: the list of telemetry metrics for each workernode. The length of the list is 3 (CPU, memry, disk) times the number of workernodes.
    """    
    global stop_threads
    # Create a list to store the results
    results = [None] * (len(ips) * 3)

    # Create a thread for each function
    threads = []
    for i, func in enumerate([get_cpu_usage, get_mem_usage, get_disk_usage]):
        for j, ip in enumerate(ips):
            thread = threading.Thread(target=collect, args=(func, ip, results, i*len(ips) + j))
            threads.append(thread)

    # Start threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check if any result is None
    if any(result is None for result in results):
        print("One or more functions did not return a valid result.")

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect telemetry metrics from Prometheus.")
    parser.add_argument('--ips', nargs='+', required=True, help="List of IP addresses")
    parser.add_argument('--duration', type=int, required=True, help="Duration to run the script in seconds")
    args = parser.parse_args()

    ips = args.ips
    end_time = time.time() + args.duration
    try:
        while time.time() < end_time:
            combined_results = generate_data(ips)
            
            # Append results to a text file
            with open("results.txt", "a") as file:
                file.write(f"{combined_results}\n")

            # Sleep for 60 seconds before the next call
            time.sleep(60)
    except KeyboardInterrupt:
        print("Process interrupted by user.")
    finally:
        stop_threads = True
        print("All threads have been signaled to stop.")
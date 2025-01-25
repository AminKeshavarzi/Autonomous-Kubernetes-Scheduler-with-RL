import requests

###################### CPU USAGE ######################
def get_cpu_usage(internal_ip: str) -> dict:
    """Fetch CPU usage from Prometheus for a given internal IP.

    Args:
        internal_ip (str): The internal IP address of the workernode to query.

    Returns:
        metrics_data (dict): The response from the Prometheus server.
    """   
    prometheus_url = "http://localhost:9090/api/v1/query"
    prometheus_query = f'100 - (avg(irate(node_cpu_seconds_total{{mode="idle", instance="{internal_ip}:9100"}}[1m])) * 100)' #Results are in the shape [metadata, cpu_percentage_value]

    try:
        response = requests.get(prometheus_url, params={'query': prometheus_query})
        if response.status_code == 200:
            metrics_data = response.json()
            return metrics_data
        else:
            print(f"Error on HTTP request: status code {response.status_code}")
    except Exception as e:
        print(f"Error on HTTP request: {str(e)}")
    return {}

###################### MEMORY USAGE ######################
def get_mem_usage(internal_ip: str) -> dict:
    """Fetch Memory usage from Prometheus for a given internal IP.

    Args:
        internal_ip (str): The internal IP address of the workernode to query.

    Returns:
        metrics_data (dict): The response from the Prometheus server.
    """    
    prometheus_url = "http://localhost:9090/api/v1/query"
    prometheus_query = f'node_memory_MemAvailable_bytes{{instance="{internal_ip}:9100"}}/10^9' #Results are in the shape [metadata, cpu_percentage_value]

    try:
        response = requests.get(prometheus_url, params={'query': prometheus_query})
        if response.status_code == 200:
            metrics_data = response.json()
            return metrics_data
        else:
            print(f"Error on HTTP request: status code {response.status_code}")
    except Exception as e:
        print(f"Error on HTTP request: {str(e)}")
    return {}
###################### MEMORY USAGE ######################

def get_disk_usage(internal_ip: str) -> dict:
    """Fetch disk usage from Prometheus for a given internal IP.

    Args:
        internal_ip (str): The internal IP address of the workernode to query.

    Returns:
        metrics_data (dict): The response from the Prometheus server.
    """    
    prometheus_url = "http://localhost:9090/api/v1/query"
    prometheus_query = f'100 - (node_filesystem_free_bytes{{mountpoint="/run",instance="{internal_ip}:9100"}} / node_filesystem_size_bytes{{mountpoint="/run",instance="{internal_ip}:9100"}} * 100)' #Results are in the shape [metadata, disk_percentage_value]

    try:
        response = requests.get(prometheus_url, params={'query': prometheus_query})
        if response.status_code == 200:
            metrics_data = response.json()
            return metrics_data
        else:
            print(f"Error on HTTP request: status code {response.status_code}")
    except Exception as e:
        print(f"Error on HTTP request: {str(e)}")
    return {}


    
    
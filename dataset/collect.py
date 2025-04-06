import random
import time
import threading
import argparse
from typing import Callable, Dict, List
from kubernetes import client, config
import string

# Prometheus query imports (you need to have these implemented)
from queries import get_cpu_usage, get_mem_usage  # your custom functions

stop_threads = False

def random_suffix(length=4):
    """Generate a random suffix to append to pod names"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

### === POD DEPLOYMENT AND DELETION === ###
def delete_existing_pods(namespace: str):
    """Delete pods with names starting with 'auto-pod-' in the specified namespace."""
    config.load_kube_config()
    v1 = client.CoreV1Api()

    try:
        pods = v1.list_namespaced_pod(namespace=namespace)
        for pod in pods.items:
            if pod.metadata.name.startswith("auto-pod-"):
                print(f"🗑️ Deleting existing pod: {pod.metadata.name}")
                v1.delete_namespaced_pod(pod.metadata.name, namespace)
    except Exception as e:
        print(f"❌ Error deleting pods: {e}")

def deploy_pods(num_pods: int = 100, namespace: str = "default"):
    """Deploy a set of pods with random CPU and memory demands."""
    config.load_kube_config()
    v1 = client.CoreV1Api()

    cpu_options = ["100m", "200m", "500m", "1"]
    memory_options = ["128Mi", "256Mi", "512Mi", "1Gi"]
    image = "busybox"
    command = ["sh", "-c", "sleep 3600"]

    # Delete previously deployed pods
    delete_existing_pods(namespace)

    for i in range(1, num_pods + 1):
        cpu = random.choice(cpu_options)
        mem = random.choice(memory_options)
        suffix = random_suffix()
        pod_name = f"auto-pod-{i}-{suffix}"  # Ensure uniqueness

        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name, labels={"app": "auto-demo"}),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="main",
                        image=image,
                        command=command,
                        resources=client.V1ResourceRequirements(
                            requests={"cpu": cpu, "memory": mem},
                            limits={"cpu": cpu, "memory": mem},
                        )
                    )
                ],
                restart_policy="Never"
            )
        )

        try:
            v1.create_namespaced_pod(namespace=namespace, body=pod)
            print(f"✅ Created pod {pod_name} with CPU={cpu}, Memory={mem}")
        except Exception as e:
            print(f"❌ Failed to create pod {pod_name}: {e}")

### === TELEMETRY COLLECTION === ###
def collect(func: Callable[[str], Dict], ip: str, results: list, index: int) -> None:
    global stop_threads
    try:
        response = func(ip)
        if 'data' in response and 'result' in response['data']:
            if len(response['data']['result']) > 0:
                result = response['data']['result'][0]
                if 'value' in result and len(result['value']) > 1:
                    value = result['value'][1]
                    results[index] = value
                else:
                    print(f"Thread {index} error: value list too short")
            else:
                print(f"Thread {index} error: result list empty")
        else:
            print(f"Thread {index} error: invalid response: {response}")
    except Exception as e:
        print(f"Thread {index} error: {e}")

def generate_data(ips: List[str]) -> List:
    global stop_threads
    resources = ['cpu', 'memory']
    results = [None] * (len(ips) * len(resources))
    threads = []

    for i, ip in enumerate(ips):
        for j, func in enumerate([get_cpu_usage, get_mem_usage]):
            thread = threading.Thread(target=collect, args=(func, ip, results, i * len(resources) + j))
            threads.append(thread)

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    if any(result is None for result in results):
        print("⚠️ Some telemetry metrics were not collected successfully.")

    return results

### === MAIN === ###
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy pods and collect telemetry metrics.")
    parser.add_argument('--ips', nargs='+', required=True, help="List of node IPs")
    parser.add_argument('--duration', type=int, required=True, help="Duration to run telemetry in seconds")
    parser.add_argument('--namespace', default="default", help="Namespace to deploy pods")
    parser.add_argument('--num_pods', type=int, default=100, help="Number of pods to deploy")
    args = parser.parse_args()

    print("🚀 Deploying pods...")
    deploy_pods(num_pods=args.num_pods, namespace=args.namespace)

    print(f"📡 Starting telemetry collection from nodes: {args.ips}")
    end_time = time.time() + args.duration

    try:
        while time.time() < end_time:
            results = generate_data(args.ips)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            with open("results.txt", "a") as f:
                f.write(f"{timestamp}: {results}\n")
            print(f"📁 Logged telemetry at {timestamp}")
            time.sleep(60)
    except KeyboardInterrupt:
        print("❌ Interrupted by user.")
    finally:
        stop_threads = True
        print("🛑 Stopping telemetry collection.")

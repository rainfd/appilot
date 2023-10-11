import subprocess
import time
import tempfile
import socket
import yaml
import json


def setup_kind(cluster: str):
    """Setup kind cluster and return kubeconfig file."""
    # cluster = "test-appilot-cluster"
    container = f"{cluster}-control-plane"

    # check if kind is installed
    # don't use path to check if kind is installed
    # because it may be installed in a different path
    if "kind" not in subprocess.check_output("which kind", shell=True).decode():
        raise Exception("Kind is not installed.")

    # create kind configuration
    # kind get clusters
    # kind create cluster --name test-appilot
    # check if kind cluster exists
    if cluster in subprocess.check_output("kind get clusters", shell=True).decode():
        print("Kind cluster already exists.")
    else:
        # create kind configuration file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"""
apiVersion: kind.x-k8s.io/v1alpha4
kind: Cluster
networking:
    apiServerAddress: "0.0.0.0"
            """)
            f.seek(0)

            # create kind cluster
            print("Creating kind cluster...")
            subprocess.check_output(f"kind create cluster --name {cluster} --config {f.name}", shell=True)

        print("Waiting for kind cluster to start...")
        times = 3
        while True:
            if times == 0:
                raise Exception("Failed to create kind cluster.")
            if cluster in subprocess.check_output("kind get clusters", shell=True).decode():
                break
            time.sleep(5)
            times -= 1

        print(f"Kind cluster {cluster} created.")

    # get kubeconfig
    # kind get kubeconfig --name test-appilot
    kubeconfig = subprocess.check_output(f"kind get kubeconfig --name {cluster}", shell=True).decode()

    ip = get_cluster_ip(cluster)

    config = yaml.safe_load(kubeconfig)
    config["clusters"][0]["cluster"]["server"] = f"https://{ip}:6443"
    kubeconfig = yaml.dump(config)

    return kubeconfig


def get_cluster_ip(cluster: str):
    """Get cluster container ip. Using docker inspect"""
    container = get_cluster_container(cluster)
    inspect = subprocess.check_output(f"docker inspect {container}", shell=True).decode().strip()
    message = json.loads(inspect)
    ip = message[0]["NetworkSettings"]["Networks"]["kind"]["IPAddress"]
    return ip


def get_cluster_container(cluster: str):
    return f"{cluster}-control-plane"


def delete_kind_cluster(cluster: str):
    """Delete kind cluster."""
    subprocess.check_output(f"kind delete cluster --name {cluster}", shell=True)

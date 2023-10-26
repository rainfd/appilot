import subprocess
import time
import tempfile
import socket
import yaml
import json

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import List

from urllib3.exceptions import HTTPError


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
            time.sleep(3)
            times -= 1

        print(f"Kind cluster {cluster} created.")

    times = 3
    while not check_cluster_ready(cluster) and times >= 0:
        if times == 0:
            raise Exception("Kind cluster is not ready.")
        time.sleep(5)
        times -= 1


def get_cluster_kubeconfig(cluster: str):
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


def check_cluster_ready(cluster: str) -> bool:
    kubeconfig = get_cluster_kubeconfig(cluster)
    config_dict = yaml.safe_load(kubeconfig)
    # kubernetes load config from string
    config.load_kube_config_from_dict(config_dict)

    v1 = client.CoreV1Api()
    try:
        nodes = v1.list_node()
        node = nodes.items[0]
        node_name = node.metadata.name
        node_conditions = node.status.conditions
        for condition in node_conditions:
            if condition.type == "Ready":
                if condition.status == "True":
                    print(f"Node {node_name} is Ready")
                    return True
                else:
                    print(f"Node {node_name} is Not Ready")
                    return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def create_namespaces(cluster: str, namespaces: List[str]):
    kubeconfig = get_cluster_kubeconfig(cluster)
    config_dict = yaml.safe_load(kubeconfig)
    # kubernetes load config from string
    config.load_kube_config_from_dict(config_dict)

    v1 = client.CoreV1Api()

    for ns in namespaces:
        body = client.V1Namespace(metadata=client.V1ObjectMeta(name=ns))
        try:
            v1.create_namespace(body)
        except ApiException as e:
            if e.status == 404:
                continue
        except Exception as e:
            raise e


def delete_namespaces(cluster: str, namespace: List[str]):
    kubeconfig = get_cluster_kubeconfig(cluster)
    config_dict = yaml.safe_load(kubeconfig)
    # kubernetes load config from string
    config.load_kube_config_from_dict(config_dict)

    for ns in namespace:
        v1 = client.CoreV1Api()
        try:
            v1.delete_namespace(ns)
        except ApiException as e:
            if e.status == 404:
                continue
        except Exception as e:
            raise e



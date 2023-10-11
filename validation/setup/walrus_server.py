#!/usr/bin/env python
import os
import socket
import subprocess
import time
import requests
import json


import urllib3
urllib3.disable_warnings()


IMAGE = "sealio/walrus"
CONTAINER = "test-walrus"
KIND_CLUSTER = "test-walrus-cluster"
PASSWORD = "123456Aa"


class WalrusTestClient:

    def __init__(self, api_url: str = "https://localhost", api_key: str = "", kubeconfig=""):
        self.api_url = api_url
        self.api_key = api_key

        self.user = "admin"
        self.password = ""
        self.kubeconfig = kubeconfig
        self.connector_id = ""

    def setup(self):
        self.install()
        self.login()
        self.set_server_address()
        self.create_api_key()
        # self.environment_setup()

    def install(self):
        """Setup walrus container."""

        # check if docker is installed
        # don't use path to check if docker is installed
        # because it may be installed in a different path
        if "docker" not in subprocess.check_output("which docker", shell=True).decode():
            raise Exception("Docker is not installed.")

        # check if walrus container is running
        if CONTAINER in subprocess.check_output("docker ps", shell=True).decode():
            print("Walrus container is already running.")
        else:
            # check if walrus image is downloaded
            if IMAGE not in subprocess.check_output("docker images", shell=True).decode():
                print("Downloading walrus image...")
                subprocess.check_output(f"docker pull {IMAGE}", shell=True)

            print("Starting walrus container...")
            if self.kubeconfig != "":
                # TODO: not working
                # external kubernetes cluster
                subprocess.check_output(f"docker run -d --restart=unless-stopped -p 80:80 -p 443:443 "
                                        f"--net kind "
                                        f"-v {self.kubeconfig}:/root/.kube/config "
                                        f"--name {CONTAINER} {IMAGE}", shell=True)
            else:
                subprocess.check_output("sudo docker run -d --privileged --restart=unless-stopped -p 80:80 -p 443:443 "
                                        f"--net kind "
                                        f"--name {CONTAINER} {IMAGE}", shell=True)

            # wait for walrus container to start
            print("Waiting for walrus container to start...")
            time.sleep(5)

        # get walrus password
        password = ""
        times = 3
        while password == "":
            if times == 0:
                raise Exception("Failed to get walrus password.")
            password = subprocess.check_output(
                f"docker logs {CONTAINER} 2>&1 | grep 'Bootstrap Admin Password' | awk -F '!!! "
                "Bootstrap Admin Password: ' '{print $2}' | awk '{print $1}'",
                shell=True).decode().strip()
            time.sleep(5)
            times -= 1
        self.password = password

        # get walrus container ip
        inspect = subprocess.check_output(f"docker inspect {CONTAINER}", shell=True).decode().strip()
        message = json.loads(inspect)
        ip = message[0]["NetworkSettings"]["Networks"]["kind"]["IPAddress"]
        self.ip = ip
        self.api_url = f"https://{ip}"

    def login(self):
        """Login walrus server to get session."""

        for password in [self.password, PASSWORD]:
            url = self.api_url + "/account/login"
            headers = {
                "Content-Type": "application/json",
            }
            data = {
                "password": password,
                "username": self.user
            }
            response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
            # default bootstrap password
            if response.status_code == 401:
                continue
            if response.status_code >= 300:
                raise Exception("Failed to login to walrus container.")

            cookie = response.headers.get('Set-Cookie', None)
            if cookie is None:
                raise Exception("Failed to get walrus cookie.")
            self.cookie = cookie

            if password == self.password:
                self.change_password()

        if getattr(self, "cookie", None) is None:
            raise Exception("Failed to login to walrus container.")

    def change_password(self):
        """Change password for test."""
        url = self.api_url + "/account/info"
        data = {
            "oldPassword": self.password,
            "password": PASSWORD,
            "name": self.user
        }
        response = requests.put(url, headers=self.headers(), data=json.dumps(data), verify=False)
        if response.status_code >= 300:
            raise Exception("Failed to change walrus password.")

    def headers(self):
        return {
            # "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Cookie": self.cookie,
        }

    def set_server_address(self):
        """Set walrus server address."""
        url = self.api_url + "/v1/settings"
        data = {
            "items": [
                {
                    "name": "ServeUrl",
                    "value": self.api_url
                },
            ]
        }
        response = requests.put(url, headers=self.headers(), data=json.dumps(data), verify=False)
        if response.status_code >= 300:
            raise Exception("Failed to set walrus server address.")


    def create_api_key(self, name="appilot"):
        """Create walrus api key."""
        url = self.api_url + "/account/tokens"
        data = {
            "name": name,
            "expirationSeconds": None,
        }
        response = requests.post(url, headers=self.headers(), data=json.dumps(data), verify=False)
        if response.status_code >= 300:
            raise Exception("Failed to create walrus token.")
        self.api_key = response.json()['accessToken']

    def create_default_env(self, project="default", environment="dev"):
        """Set walrus default environment."""
        url = self.api_url + "/account/defaults"
        data = {
            "defaultProject": project,
            "defaultEnvironment": environment
        }
        response = requests.put(url, headers=self.headers(), data=json.dumps(data), verify=False)
        if response.status_code >= 300:
            raise Exception("Failed to set walrus default environment.")
        return response.json()

    def create_connector(self, kubeconfig: str):
        """Create walrus default kubernetes connector. Return connector id."""
        url = self.api_url + "/v1/connectors"

        # check connector exists
        response = requests.get(url, headers=self.headers(), verify=False)
        if response.status_code >= 300:
            raise Exception("Failed to get walrus connectors.")
        connectors = response.json()["items"]
        if connectors:
            for connector in connectors:
                if connector["name"] == KIND_CLUSTER:
                    self.connector_id = connector["id"]
                    return self.connector_id

        data = {
            "name": KIND_CLUSTER,
            "configData": {
                "kubeconfig": {
                    "visible": False,
                    "value": kubeconfig,
                    "type": "string"
                }
            },
            "configVersion": "v1",
            "type": "Kubernetes",
            "category": "Kubernetes",
            "enableFinOps": False
        }
        response = requests.post(url, headers=self.headers(), data=json.dumps(data), verify=False)
        if response.status_code >= 300:
            raise Exception("Failed to set walrus default connector.")
        self.connector_id = response.json()["id"]


    # def environment_setup(self):
    #     """Appilot walrus toolkit environment setup."""
    #     os.environ["WALRUS_API_URL"] = self.api_url
    #     os.environ["WALRUS_API_KEY"] = self.api_key
    #     os.environ["WALRUS_SKIP_TLS_VERIFY"] = "1"
    #     os.environ["WALRUS_DEFAULT_PROJECT"] = "default"
    #     os.environ["WALRUS_DEFAULT_ENVIRONMENT"] = "dev"

    def create_environment(self, project="default", environment="dev"):
        """Create walrus environment."""

        # get project id first
        url = self.api_url + "/v1/projects"
        response = requests.get(url, headers=self.headers(), verify=False)
        if response.status_code >= 300:
            raise Exception("Failed to get walrus projects.")
        projects = response.json()["items"]
        project_id = ""
        if projects:
            for p in projects:
                if p["name"] == project:
                    project_id = p["id"]
                    break
        if project_id == "":
            raise Exception("Failed to get walrus project id.")

        # check environment exists
        url = self.api_url + f"/v1/projects/{project_id}/environments"
        response = requests.get(url, headers=self.headers(), verify=False)
        if response.status_code >= 300:
            raise Exception("Failed to get walrus environments.")
        environments = response.json()["items"]
        if environments:
            for e in environments:
                if e["name"] == environment:
                    if environment == "dev":
                        self.dev_env_id = e["id"]
                    elif environment == "test":
                        self.test_env_id = e["id"]
                    return e["id"]

        url = self.api_url + f"/v1/projects/{project_id}/environments"
        data = {
            "projectID": project_id,
            "name": environment,
            "description": "",
            "connectorIDs": [self.connector_id],
            "connectors": [
                {
                    "connector": {
                        "id": self.connector_id
                    }
                }
            ],
            "labels": {},
            "services": []
        }
        response = requests.post(url, headers=self.headers(), data=json.dumps(data), verify=False)
        if response.status_code >= 300:
            raise Exception("Failed to create walrus environment.")


    def destory(self):
        """Clean walrus container."""
        subprocess.check_output(f"docker rm -f {CONTAINER}", shell=True)


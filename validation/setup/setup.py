import os
import yaml
import sys
from typing import Any, Optional
import colorama

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from autochain.chain.langchain_wrapper_chain import LangChainWrapperChain

import utils.utils
from callbacks import handlers
from config import config
from i18n import text
from agent.agent import create_agent
from walrus.toolkit import WalrusToolKit
from k8s.toolkit import KubernetesToolKit

from validation.setup.walrus_server import WalrusTestClient
from validation.setup.kind import (
    setup_kind,
    delete_kind_cluster,
    get_cluster_kubeconfig,
    delete_namespaces,
    create_namespaces
)

WalrusClient: Optional[WalrusTestClient] = None

WALRUS_KIND_CLUSTER = "walrus-kind-cluster"
K8S_KIND_CLUSTER = "k8s-kind-cluster"


def save_kubeconfig(kubeconfig):
    with open("test-kubeconfig", "w") as f:
        f.write(kubeconfig)
    pwd = os.getcwd()
    path = os.path.join(pwd, "test-kubeconfig")
    return path


def appilot_enviroment(toolkit):
    """Set default environment variables."""
    # os.environ["TOOLKIT"] = ["walrus", "kubernetes"]
    os.environ['TOOLKITS'] = toolkit
    os.environ["NATURAL_LANGUAGE"] = "English"
    os.environ["SHOW_REASONS"] = "1"
    os.environ["VERBOSE"] = "1"


def walrus_enviroment(api_url, api_key):

    """Appilot walrus toolkit environment setup."""
    os.environ["WALRUS_URL"] = api_url
    os.environ["WALRUS_API_KEY"] = api_key
    os.environ["WALRUS_SKIP_TLS_VERIFY"] = "1"
    os.environ["WALRUS_DEFAULT_PROJECT"] = "default"
    os.environ["WALRUS_DEFAULT_ENVIRONMENT"] = "dev"


def kubernetes_enviroment(path):
    os.environ["KUBECONFIG"] = path


def setup_walrus_sandbox():
    # kind
    clear_walrus_sandbox(["default-" + x for x in ["dev", "test", "qa", "prod"]])
    setup_kind(WALRUS_KIND_CLUSTER)
    kubeconfig = get_cluster_kubeconfig(WALRUS_KIND_CLUSTER)
    # walrus
    client = WalrusTestClient()
    client.setup()
    client.create_connector(kubeconfig)
    for env in ("test", "dev", "qa"):
        client.create_environment(environment=env)
    # env
    walrus_enviroment(client.api_url, client.api_key)

    global WalrusClient
    WalrusClient = client


def destroy_walrus_sandbox():
    global WalrusClient
    if WalrusClient:
        WalrusClient.destory()

    delete_kind_cluster(WALRUS_KIND_CLUSTER)


def clear_walrus_sandbox(namespaces):
    global WalrusClient
    if WalrusClient:
        WalrusClient.destory()
    else:
        WalrusTestClient().destory()

    try:
        delete_namespaces(WALRUS_KIND_CLUSTER, namespaces)
    except Exception as e:
        print(e)
        return


def setup_k8s_sandbox():
    setup_kind(K8S_KIND_CLUSTER)
    kubeconfig = get_cluster_kubeconfig(K8S_KIND_CLUSTER)
    path = save_kubeconfig(kubeconfig)
    kubernetes_enviroment(path)


def clear_k8s_sandbox():
    namespaces = ["default", "dev", "test", "qa", "prod"]
    try:
        delete_namespaces(K8S_KIND_CLUSTER, namespaces)
    except Exception as e:
        print(e)
        return
    create_namespaces(K8S_KIND_CLUSTER, namespaces)


def destroy_k8s_sandbox():
    delete_kind_cluster(K8S_KIND_CLUSTER)


def setup_test_agent(model="gpt-4"):
    config.init()
    colorama.init()

    memory = ConversationBufferMemory(memory_key="chat_history")

    llm = ChatOpenAI(
        model_name=model,
        temperature=0,
        callbacks=[handlers.PrintReasoningCallbackHandler()],
    )

    text.init_system_messages(llm)

    enabled_toolkits = [
        toolkit.lower() for toolkit in config.APPILOT_CONFIG.toolkits
    ]

    tools = []
    if "kubernetes" in enabled_toolkits:
        kubernetes_toolkit = KubernetesToolKit(llm=llm)
        tools.extend(kubernetes_toolkit.get_tools())
    elif "walrus" in enabled_toolkits:
        walrus_toolkit = WalrusToolKit(llm=llm)
        tools.extend(walrus_toolkit.get_tools())
    else:
        print(text.get("enable_no_toolkit"))
        sys.exit(1)

    # Remove all callbacks from tools
    for tool in tools:
        tool.callbacks = []

    agent = create_agent(
        llm,
        shared_memory=memory,
        tools=tools,
        verbose=config.APPILOT_CONFIG.verbose,
        interact=False,
    )

    return LangChainWrapperChain(langchain=agent)

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

from validation.setup.walrus_server import WalrusTestClient
from validation.setup.kind import setup_kind, delete_kind_cluster

WalrusClient: Optional[WalrusTestClient] = None

WALRUS_KIND_CLUSTER = "walrus-kind-cluster"


def save_kubeconfig(kubeconfig):
    with open("test-kubeconfig", "w") as f:
        f.write(kubeconfig)
    pwd = os.getcwd()
    path = os.path.join(pwd, "test-kubeconfig")
    return path


def appilot_enviroment(api_url, api_key):
    """Set default environment variables."""
    os.environ["TOOLKIT"] = "walrus"
    os.environ["NATURAL_LANGUAGE"] = "English"
    os.environ["SHOW_REASONS"] = "1"
    os.environ["VERBOSE"] = "0"

    """Appilot walrus toolkit environment setup."""
    os.environ["WALRUS_URL"] = api_url
    os.environ["WALRUS_API_KEY"] = api_key
    os.environ["WALRUS_SKIP_TLS_VERIFY"] = "1"
    os.environ["WALRUS_DEFAULT_PROJECT"] = "default"
    os.environ["WALRUS_DEFAULT_ENVIRONMENT"] = "dev"


def setup_walrus_sandbox():
    # kind
    kubeconfig = setup_kind(WALRUS_KIND_CLUSTER)
    # walrus
    client = WalrusTestClient()
    client.setup()
    client.create_connector(kubeconfig)
    for env in ("test", "dev", "qa"):
        client.create_environment(environment=env)
    # env
    appilot_enviroment(client.api_url, client.api_key)

    global WalrusClient
    WalrusClient = client


def destory_walrus_sandbox():
    global WalrusClient
    if WalrusClient:
        WalrusClient.destory()

    delete_kind_cluster(WALRUS_KIND_CLUSTER)


def setup_test_agent(model="gpt-4"):
    setup_walrus_sandbox()

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
        # kubernetes_toolkit = KubernetesToolKit(llm=llm)
        # tools.extend(kubernetes_toolkit.get_tools())
        pass
    elif "walrus" in enabled_toolkits:
        # walrus_toolkit = MockWalrusToolkit(llm=llm)
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
    )

    return LangChainWrapperChain(langchain=agent)

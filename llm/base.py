from langchain.chat_models import ChatOpenAI, ChatGooglePalm, ErnieBotChat
from langchain.llms import Tongyi

from config import config
from llm.sagemaker import get_sagemaker
from llm.baidu import get_erniebot


def get_llm(*args, **kwargs):
    model = config.APPILOT_CONFIG.model
    llm = None
    if model.startswith("gpt"):
        llm = ChatOpenAI(
            model_name="gpt-4",
            **kwargs,
        )
    elif model.startswith("ERNIE-Bot"):
        llm = get_erniebot(**kwargs)
    elif model.startswith("palm"):
        llm = ChatGooglePalm(**kwargs)
    elif model.startswith("aws"):
        llm = get_sagemaker(**kwargs)
    elif model.startswith("qwen"):
        llm = Tongyi(
            model_name="qwen-14b-chat",
            **kwargs
        )
    else:
        raise ValueError(f"model {model} is not supported")
    return llm

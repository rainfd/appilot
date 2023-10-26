from langchain.chat_models import ChatOpenAI, ChatGooglePalm, ErnieBotChat
from langchain.llms import Bedrock

from config import config
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
    return llm

def test():
    # client = boto3.client(
    #     's3',
    #     aws_access_key_id=ACCESS_KEY,
    #     aws_secret_access_key=SECRET_KEY,
    #     aws_session_token=SESSION_TOKEN
    # )
    import boto3
    boto3.client
    llm = Bedrock(
        region_name="us-east-1",
    )
    return llm
import requests
from langchain.chat_models import ErnieBotChat


def _chat(self, payload: object) -> dict:
    base_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat"
    if self.model_name == "ERNIE-Bot-turbo":
        url = f"{base_url}/eb-instant"
    elif self.model_name == "ERNIE-Bot":
        url = f"{base_url}/completions"
    elif self.model_name == "ERNIE-Bot-4":
        # url = f"{base_url}/completions_pro"
        url = f"{base_url}/completions"
    else:
        raise ValueError(f"Got unknown model_name {self.model_name}")
    # TODO: limit payload to 4800 characters
    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
        },
        params={"access_token": self.access_token},
        json=payload,
    )
    return resp.json()


ErnieBotChat._chat = _chat


def get_erniebot(model="ERNIE-Bot-4", **kwargs):
    return ErnieBotChat(
        model_name="ERNIE-Bot-4",
        **kwargs,
    )

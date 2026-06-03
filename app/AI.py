import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import websocket

class Ws_Param(object):
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        url = self.Spark_url + '?' + urlencode(v)
        return url


def gen_params(appid, domain, question):
    data = {
        "header": {
            "app_id": appid,
            "uid": "1234",
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "temperature": 1.2,
                "max_tokens": 32768
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }
    return data


def getText(role, content, text_list=None):
    if text_list is None:
        text_list = []
    jsoncon = {"role": role, "content": content}
    text_list.append(jsoncon)
    return text_list


def getlength(text):
    length = 0
    for content in text:
        length += len(content["content"])
    return length


def checklen(text):
    while getlength(text) > 8000:
        del text[0]
    return text


def main(appid, api_key, api_secret, Spark_url, domain, question):
    wsParam = Ws_Param(appid, api_key, api_secret, Spark_url)
    wsUrl = wsParam.create_url()
    answer = ""
    isFirstcontent = False

    def on_message(ws, message):
        nonlocal answer, isFirstcontent
        data = json.loads(message)
        code = data['header']['code']
        content = ''
        if code != 0:
            print(f'请求错误: {code}, {data}')
            ws.close()
        else:
            choices = data["payload"]["choices"]
            status = choices["status"]
            text = choices['text'][0]
            if 'reasoning_content' in text and text['reasoning_content']:
                reasoning_content = text["reasoning_content"]
                print(reasoning_content, end="")
                isFirstcontent = True

            if 'content' in text and text['content']:
                content = text["content"]
                if isFirstcontent:
                    print("\n*******************以上为思维链内容，模型回复内容如下********************\n")
                print(content, end="")
                isFirstcontent = False
            answer += content
            if status == 2:
                ws.close()

    def on_error(ws, error):
        print("### error:", error)

    def on_close(ws, one, two):
        print("连接关闭")

    def on_open(ws):
        def run(*args):
            data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question))
            ws.send(data)
        thread.start_new_thread(run, (ws,))

    ws = websocket.WebSocketApp(
        wsUrl,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.appid = appid
    ws.question = question
    ws.domain = domain
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    return answer


if __name__ == '__main__':
    appid = "bb2fc088"
    api_secret = "NzM2MTdiNmJjNDhjNTUyYTc0MTQwNTQw"
    api_key = "1fecfee0b9482cac4d476f955d22089d"
    domain = "spark-x"
    Spark_url = "wss://spark-api.xf-yun.com/v1/x1"

    while True:
        user_input = input("\n我:")
        text_list = []
        question = checklen(getText("user", user_input, text_list))
        print("星火:", end="")
        result = main(appid, api_key, api_secret, Spark_url, domain, question)
        getText("assistant", result, text_list)
        print(f"\n助手:{result}")
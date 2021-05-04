from aws_cdk import (
    core,
    aws_lambda as _lambda
)
import os

FUNC = """
import re
import requests
from bs4 import BeautifulSoup
import json
import codecs

def handler(event, context):
    config_path = '../configs/PS5_configs.json'
    config = config_load(config_path)

    line_notify_token = config['line_notify_token']

    result_message = scraping(config['rakuten'])

    if result_message != None:
        send_line_notify(result_message, line_notify_token)

def send_line_notify(notification_message, line_notify_token):
    line_notify_api = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {line_notify_token}'}
    data = {'message': f'message: {notification_message}'}
    requests.post(line_notify_api, headers = headers, data = data)

def scraping(config):
    result_message = config['shop']
    data = requests.get(config['url'], params=config['payload'])
    data.encoding = data.apparent_encoding
    data = data.text
    soup = BeautifulSoup(data, "html.parser")
    try:
        detail = soup.find(config['find_tag']).text
        if (config['key'] in detail) == False: # 商品ページにキーワードがない場合は販売していると判定
            result_message += "在庫あり"
            result_message += config['item_url']
            return result_message
        else:
            return None
    except AttributeError:
            return "Error"

def config_load(path):
    with codecs.open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return json.load(f)
"""


class SaleNotification(core.Stack):

    def __init__(self, scope: core.App, name: str, **kwargs) -> None:
        super().__init__(scope, name, **kwargs)

        
        handler = _lambda.Function(
            self, 'LambdaHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_inline(FUNC),
            handler="index.handler",
            memory_size=128,
            timeout=core.Duration.seconds(20),
            dead_letter_queue_enabled=True,
        )

        core.CfnOutput(self, "FunctionName", value=handler.function_name)

app = core.App()
SaleNotification(
    app, "SaleNotification",
    env={
        "region": os.environ["CDK_DEFAULT_REGION"],
        "account": os.environ["CDK_DEFAULT_ACCOUNT"],
    }
)
app.synth()
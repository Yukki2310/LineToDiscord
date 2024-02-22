import logging
import os
import azure.functions as func
import json
import requests

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

# Azure FunctionsのApplication Settingに設定した値から取得する
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# discordの振り分け処理
keyword_to_channels = {
    "keyword": ["webhookUrl"]
}
def process_message(message):
    # キーワードを探す
    matched_channels = set()

    for keyword, channels in keyword_to_channels.items():
        if keyword in message:
            matched_channels.update(channels)
    # どのキーワードにもマッチしない場合は、デフォルトのチャンネルを返す
    if not matched_channels:
        matched_channels.add("https://discord.com/api/webhooks/1131790244006596749/lTvWfGkIcQyhlcPUqou7amJpyFa4X5c9sd5YaAzWcGKEGLHm0dUqNkL0knI6LuKVtDG-")

    return matched_channels

# Discordへの投稿
def post_discord(message: str, webhook_url: str):
    embeds = [
        {
            'color': 0x06C755,
            'fields': [
                {
                    'name': 'LINEから転送',
                    'value': message
                }
            ]
        }
    ]
    content =   {
        'embeds': embeds
    }
    headers =   {
        'Content-Type': 'application/json'
    }

    requests.post(
        webhook_url,
        json.dumps(content),
        headers=headers
    )

# LINEのWebhook認証
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # get x-line-signature header value
    signature = req.headers['x-line-signature']

    # get request body as text
    body = req.get_body().decode("utf-8")
    logging.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        func.HttpResponse(status_code=400)

    return func.HttpResponse('OK')

# LINEメッセージに反応
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.reply_token == "00000000000000000000000000000000":
        return

    matched_channels = process_message(event.message.text)

    for channel_url in matched_channels:
        post_discord(event.message.text, channel_url)
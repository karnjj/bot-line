from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage,)

app = Flask(__name__)

line_bot_api = LineBotApi('o14KQyuIIqKfmAdR9b+oat4z8A7nKRtWjMdIaGSjGl6vuxc8Ot85rGSEAFWVVOeS+OWiQGTjFH7IAf7hBiRU+2txbde+ZNaJHEXIv6B59aZRXotzbvXiXhk4Py9rpfyg6/LJlMQFvkPBrF+s8SUKLAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('375be5ebbd4428a657ecd629c07e2beb')

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/webhook", methods=['POST'])
def webhook():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"
    
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	text=event.message.text
	if text == 'karn' :		
		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage('Hello karn!!'))

if __name__ == "__main__":
	app.run()

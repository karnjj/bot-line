from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage,)
import paho.mqtt.client as mqtt , os

# Define event callbacks
def on_connect(client, userdata, flags, rc):
    print("rc: " + str(rc))

def on_message(client, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

def on_publish(client, obj, mid):
    print("mid: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(client, obj, level, string):
    print(string)

mqttc = mqtt.Client()
# Assign event callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe


mqttc.username_pw_set("brsiutlc", "Rw4rcSFm_gCL")
mqttc.connect('m15.cloudmqtt.com',  17711 )
mqttc.subscribe("/test", 0)


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
	mqttc.username_pw_set("brsiutlc", "Rw4rcSFm_gCL")
	mqttc.connect('m15.cloudmqtt.com',  17711 )
	mqttc.subscribe("/test1", 0)
	mqttc.subscribe("/test2", 0)
	text=event.message.text
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(text))
	mqttc.publish("/test", text)

if __name__ == "__main__":
	app.run()

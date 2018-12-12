from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage,)
import paho.mqtt.client as mqtt
import json

_APP_VERSION_ = "beta 1.08"

# Define event callbacks
def on_connect(client, userdata, flags, rc):
	print("rc: " + str(rc))

def on_message(client, obj, msg):
	global temp
	m_in=json.loads(msg.payload)
	print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
	#txt = str(m_in["temp"]) + " " + str(m_in["humi"]) + " " + str(bool(m_in["mois"]))
	line_bot_api.reply_message(
		temp.reply_token,
		TextSendMessage("Temp\t: {0:2d} C\nHumi\t\t: {1:2d} %\nMois\t\t: {2}\nLigh\t\t: {3:2d}" .format(int(m_in["temp"]),int(m_in["humi"]),str(bool(m_in["mois"])),int(m_in["lumi"]))))
	mqttc.disconnect()

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
mqttc.subscribe("/test2", 0)


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

_await_temp = 0
_await_humi = 0
_await_lumi = 0
_await_mois = 0

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	global temp, _await_temp, _await_humi, _await_lumi, _await_mois
	temp = event
	mqttc.username_pw_set("brsiutlc", "Rw4rcSFm_gCL")
	mqttc.connect('m15.cloudmqtt.com',  17711 )
	mqttc.subscribe("/test2", 0)
	text = event.message.text
	text = text.splitlines()
        cmd = text[0].lower()
        print ("Got: " + text[0] + " --> " + cmd)
        if   cmd == "stat":
		mqttc.publish("/test1", text[0])
		mqttc.loop_forever()
	elif cmd  == "help":
		line_bot_api.reply_message(
			temp.reply_token,
                        TextSendMessage("There are : \nstat -- Check the environment in side the box.\nhelp -- Well, that's how you get here.\nedit -- Edit values of the setting.\nassign -- Assign new values to the system\nver -- Check the version of Line Interactive"))
	elif cmd == "edit":
                _await_temp = text[1]
                _await_humi = text[2]
                _await_lumi = text[3]
                _await_mois = text[4]
                line_bot_api.reply_message(
                        temp.reply_token,
                        TextSendMessage("These values will be assigned\nTemp : {0}\nHumi : {1}\nMois : {2}\nLigh : {3}\n\nTo confirm type : assign".format(_await_temp, _await_humi, _await_lumi, _await_mois))
                )
        elif cmd == "assign"
                broker_out = {
                        "humi":_await_humi,
                        "temp":_await_temp,
                        "mois":_await_mois,
                        "lumi":_await_mois
                }
		data_out = json.dumps(broker_out)
		mqttc.publish("/test1", data_out)
		line_bot_api.reply_message(
			temp.reply_token,
			TextSendMessage("Values assigned")
		)
        elif cmd == "ver":
            line_bot_api.reply_message(
                        temp.reply_token,
                        TextSendMessage(_APP_VERSION_)
                    )
        else:
		txt = event.message.text + " is not a valid function name."
		line_bot_api.reply_message(
			temp.reply_token,[
				TextSendMessage(txt),
				TextSendMessage("Please try again.")
			]
		)

if __name__ == "__main__":
	app.run()

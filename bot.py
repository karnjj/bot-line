from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *
import paho.mqtt.client as mqtt
import json
from configparser import ConfigParser
import time
_APP_VERSION_ = "beta 1.10"
cfg = ConfigParser()
cfg.read('config.ini')
loop_flag = 1


# Define event callbacks
def on_connect(client, userdata, flags, rc):
    print("rc: " + str(rc))


def on_message(client, obj, msg):
    global temp, loop_flag
    m_in = json.loads(msg.payload)
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    line_bot_api.reply_message(
        temp.reply_token,
        TextSendMessage("Temp\t: {0:2d} C\nHumi\t\t: {1:2d} %\nMois\t\t: {2}\nLigh\t\t: {3:2d}" .format(int(m_in["temp"]), int(m_in["humi"]), str(bool(m_in["mois"])), int(m_in["lumi"]))))
    loop_flag = 0


def on_publish(client, obj, mid):
    print("mid: " + str(mid))


def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(client, obj, level, string):
    print(string)


def savedata(data):
    with open('config.ini', 'w') as configfile:
        data.write(configfile)


mqttc = mqtt.Client()
# Assign event callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe

mqttc.username_pw_set("brsiutlc", "Rw4rcSFm_gCL")
mqttc.connect('m15.cloudmqtt.com',  17711)
mqttc.subscribe("/test2", 0)

app = Flask(__name__)

line_bot_api = LineBotApi(cfg.get('LineServer', 'Channel_token'))
handler = WebhookHandler(cfg.get('LineServer', 'Channel_secret'))


@app.route("/")
def hello():
    return "Welcome to my line bot"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)
    return 'OK'


_await_temp = 0
_await_humi = 0
_await_lumi = 0
_await_mois = 0


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global temp, _await_temp, _await_humi, _await_lumi, _await_mois, loop_flag
    count = 0
    print(event)
    cfg.read('config.ini')
    # print(cfg.sections())
    temp = event
    mqttc.username_pw_set("brsiutlc", "Rw4rcSFm_gCL")
    mqttc.connect('m15.cloudmqtt.com',  17711)
    mqttc.subscribe("/test2", 0)
    text = event.message.text
    text = text.split()
    cmd = text[0].lower()
    print("Got: " + text[0] + " --> " + cmd)
    if cmd == "stat":
        mqttc.publish("/test1", text[0])
        mqttc.loop_start()
        while loop_flag == 1 and count < 5:
            time.sleep(1)
            count += 1
            print(count)
        loop_flag = 1
    elif cmd == "help":
        """
        line_bot_api.reply_message(
            temp.reply_token,
            TextSendMessage("There are : \nstat -- Check the environment in side the box.\nhelp -- Well, that's how you get here.\n"
                            "edit -- Edit values of the setting.\nassign -- Assign new values to the system\nver -- Check the version of Line Interactive"))
        """
        txtmsg = "There are : \nstat -- Check the environment in side the box.\nhelp -- Well, that's how you get here.\n"
        + "edit -- Edit values of the setting.\nassign -- Assign new values to the system\nver -- Check the version of Line Interactive"
        line_bot_api.reply_message(
            temp.reply_token,
            TextSendMessage(
                text = 'Quick reply',
                quick_reply = QuickReply(
                    items = [
                        QuickReplyButton(
                            action = MessageAction(label = "stat", text = "stat")
                        ),
                    ])))
    elif cmd == "edit":
        _await_temp = text[1]
        _await_humi = text[2]
        _await_lumi = text[3]
        _await_mois = text[4]
        textmsg = "These values will be assigned\nTemp : {0}\nHumi : {1}\nMois : {2}\nLigh : {3}\n\nTo confirm type : Yes".format(
            _await_temp, _await_humi, _await_lumi, _await_mois)
        confirm_template = ConfirmTemplate(textmsg, actions=[
            MessageAction(label='Yes', text='Yes!'),
            MessageAction(label='No', text='No!'),
        ])
        template_message = TemplateSendMessage(
            alt_text='Confirm alt text', template=confirm_template)
        line_bot_api.reply_message(temp.reply_token, template_message)
        cfg['configData']['flag_update'] = 'True'
        savedata(cfg)
    elif cmd == "yes!":
        if cfg.getboolean('configData', 'flag_update'):
            broker_out = {
                "humi": _await_humi,
                "temp": _await_temp,
                "mois": _await_mois,
                "lumi": _await_lumi
            }
            data_out = json.dumps(broker_out)
            mqttc.publish("/test1", data_out)
            line_bot_api.reply_message(
                temp.reply_token,
                TextSendMessage("Values assigned")
            )
            cfg['configData']['flag_update'] = 'False'
            savedata(cfg)
        else:
            line_bot_api.reply_message(
                temp.reply_token,
                TextSendMessage("No value change")
            )
    elif cmd == "ver":
        line_bot_api.reply_message(
            temp.reply_token,
            TextSendMessage(_APP_VERSION_)
        )
    else:
        txt = event.message.text + " is not a valid function name."
        line_bot_api.reply_message(
            temp.reply_token, [
                TextSendMessage(txt),
                TextSendMessage("Please try again.")
            ]
        )
    mqttc.disconnect()
    mqttc.loop_stop()


if __name__ == "__main__":
    app.run()

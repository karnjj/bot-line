from flask import Flask, request, abort
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *
import paho.mqtt.client as mqtt
import json
from configparser import ConfigParser
import time
import datetime
import threading
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
        TextSendMessage("Temp\t: {0:2d} C\nHumi\t\t: {1:2d} %\nMois\t\t: {2}\nLigh\t\t: {3}" .format(int(m_in["in_temp"]), int(m_in["in_humi"]), (m_in["mois"]), str(bool(m_in["lumi"])))))
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

cred = credentials.Certificate("pocket-farm-b1970-firebase-adminsdk-sfo2w-db33ced3fd.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

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
    return 200


def remind():
    while True:
        #print(1)
        line_bot_api.push_message(
            'U68a3a83f15c519f660754c9c0959dd50',
            TextSendMessage(str(datetime.datetime.now()))
        )
        time.sleep(5)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global temp, loop_flag
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
        mqttc.publish("/test1", cmd)
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
        line_bot_api.reply_message(
            temp.reply_token,
            TextSendMessage(
                text="There are : \nstat -- Check the environment in side the box.\nhelp -- Well, that's how you get here.\n"
                     "edit -- Edit values of the setting.\nver -- Check the version of Line Interactive",
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=MessageAction(label="Stat", text="stat")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="Edit", text="edit")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="Ver", text="ver")
                        ),
                    ])))
    elif cmd == "load":
        doc_ref = db.collection(u'Profiles').document(text[1])
        doc = doc_ref.get().to_dict()
        '''
        cfg['configData']['temp'] = int(doc['temp'])
        cfg['configData']['humi'] = int(doc['humi'])
        cfg['configData']['mois'] = int(doc['mois'])
        cfg['configData']['lumi'] = int(doc['lumi'])
        '''
        textmsg = "These values will be assigned\nTemp : {0:2d}\nHumi : {1:2d}\nMois : {2}\nLigh : {3}\n\nTo confirm type : Yes".format(
            int(doc['temp']), int(doc['humi']), int(doc['mois']), str(bool(doc['lumi'])))
        confirm_template = ConfirmTemplate(textmsg, actions=[
            MessageAction(label='Yes', text='Yes!'),
            MessageAction(label='No', text='No!'),
        ])
        template_message = TemplateSendMessage(
            alt_text='Confirm alt text', template=confirm_template)
        line_bot_api.reply_message(temp.reply_token, template_message)
        cfg['configData']['flag_update'] = 'True'
        savedata(cfg)
    elif cmd == "new" :
        data = {
            u'temp': text[2],
            u'humi': text[3],
            u'mois': text[4],
            u'lumi' : text[5]
        }

        # Add a new doc in collection 'cities' with ID 'LA'
        db.collection(u'Profiles').document(text[1]).set(data)
        line_bot_api.reply_message(
            temp.reply_token,
            TextSendMessage("value save.")
        )
    elif cmd == "edit":
        cfg['configData']['temp'] = text[1]
        cfg['configData']['humi'] = text[2]
        cfg['configData']['mois'] = text[3]
        cfg['configData']['lumi'] = text[4]
        textmsg = "These values will be assigned\nTemp : {0}\nHumi : {1}\nMois : {2}\nLigh : {3}\n\nTo confirm type : Yes".format(
            text[1], text[2], text[3], str(bool(text[4])))
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
                "humi": cfg['configData']['humi'],
                "temp": cfg['configData']['temp'],
                "mois": cfg['configData']['mois'],
                "lumi": cfg['configData']['lumi']
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
    elif cmd == "flex":
        bubble = BubbleContainer(
            direction='ltr',
            header=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text='Device Status', align='center', weight='bold', size='lg')
                ]
            ),
            hero=ImageComponent(
                url='https://image.flaticon.com/icons/svg/1470/1470946.svg',
                size='4xl',
                aspect_ratio='1.51:1',
                aspect_mode='fit',
            ),
            body=BoxComponent(
                layout='vertical',
                contents=[
                    BoxComponent(
                        layout='horizontal',
                        contents=[
                            TextComponent(text='Inside Temp',align='start',weight='regular'),
                            TextComponent(text='0 C',align='end',weight='regular'),
                        ]
                    ),
                    BoxComponent(
                        layout='horizontal',
                        contents=[
                            TextComponent(text='Outside Temp',align='start',weight='regular'),
                            TextComponent(text='0 C',align='end',weight='regular'),
                        ]
                    ),
                    BoxComponent(
                        layout='horizontal',
                        contents=[
                            TextComponent(text='Inside Humi',align='start',weight='regular'),
                            TextComponent(text='0 %',align='end',weight='regular'),
                        ]
                    ),
                    BoxComponent(
                        layout='horizontal',
                        contents=[
                            TextComponent(text='Outside Humi',align='start',weight='regular'),
                            TextComponent(text='0 %',align='end',weight='regular'),
                        ]
                    ),
                    BoxComponent(
                        layout='horizontal',
                        contents=[
                            TextComponent(text='Mois',align='start',weight='regular'),
                            TextComponent(text='0 %',align='end',weight='regular'),
                        ]
                    ),
                    BoxComponent(
                        layout='horizontal',
                        contents=[
                            TextComponent(text='Lumi',align='start',weight='regular'),
                            TextComponent(text='True',align='end',weight='regular'),
                        ]
                    ),
                ]
            )
        )
        message = FlexSendMessage(alt_text="Status", contents=bubble)
        line_bot_api.reply_message(
            event.reply_token,
            message
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

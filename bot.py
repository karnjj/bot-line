from flask import Flask

app = Flask(__name__)

@app.route("/")
@app.route("/webhook", methods=['GET', 'POST'])

def hello():

	return "Hello World!"

def webhook():
	if request.method == 'POST':
		return "OK"

if __name__ == "__main__":

	app.run()

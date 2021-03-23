import os
from flask import Flask, jsonify, request
from flask_restful import Api
from resources.chatbot import Chatbot
from flask_cors import CORS, cross_origin


app = Flask(__name__)

api = Api(app)

cors = CORS(app)


# @app.route("/chatbot/question")
# def chatbot():
#     return Chatbot.get()

@app.route("/")
def index():
    return "<h1><strong>Flask - REST Api<strong></h1><br/><br/> <h2><a href='/hoteis'>Listar Hoteis</a></h2>"

api.add_resource(Chatbot, '/chatbot/question')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

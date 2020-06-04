from flask import Flask
from bson.objectid import ObjectId
from flask_pymongo import PyMongo
import os, json, datetime
from py2neo import Graph, Node, Relationship, cypher


class JSONEncoder(json.JSONEncoder):                           
    ''' extend json-encoder class'''
    def default(self, o):                               
        if isinstance(o, ObjectId):
            return str(o)                               
        if isinstance(o, datetime.datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)


#  intialize our app
app = Flask(__name__)


#  add mongo url to flask config, so that flask_pymongo can use it to make connection
# app.config['MONGO_URI'] = os.environ.get('nebflix')
app.config['MONGO_URI'] = "mongodb://localhost:27017/nebflix"
mongo = PyMongo(app)

# # use the modified encoder class to handle ObjectId & datetime object while jsonifying the response.
app.json_encoder = JSONEncoder

# neo4j
graph = Graph(password='nebflix')

# DO NOT COMMENT OUT THE BELOW LINE
from nebflix import routes



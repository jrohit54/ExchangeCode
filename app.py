from flask import Flask
from flask import request
import json
import sys
from mysql import *
from redisDB import * 

import logging, sys

class LogFile(object):
    """File-like object to log text using the `logging` module."""

    def __init__(self, name=None):
        self.logger = logging.getLogger(name)

    def write(self, msg, level=logging.INFO):
        self.logger.log(level, msg)

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()

logging.basicConfig(level=logging.DEBUG, filename='/opt/flaskAppForDB.log')

# Redirect stdout and stderr
sys.stdout = LogFile('stdout')
sys.stderr = LogFile('stderr')


#class Logger(object):
#    def __init__(self):
#        self.terminal = sys.stdout
#        self.log = open("/opt/flaskAppForDB.log", "a") #logs all print statements to file
#    def write(self, message):
#        self.terminal.write(message)
#        self.log.write(message)

#    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
#        for handler in self.logger.handlers:
#            handler.flush()
#        pass

#sys.stdout = Logger() # Start logger


app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/getExternalJS/<filename>", methods=["GET"])
def getcommonjs(filename):
	return readFromFile('./static/' + filename)

@app.route("/test", methods=["POST"])
def test():
	input_json = request.get_json(force=True)
	# force=True, above, is necessary if another developer
	# forgot to set the MIME type to 'application/json'
	print 'data from client:', input_json
	return _test(input_json["test"])

@app.route("/setdb", methods=["POST"])
def setdb():
	print("In setdb method")
	db_config = request.get_json(force=True)
	print 'DB data from client:', db_config
	#print("a----------"+str(json.dumps(db_config)))
	success = connect_mysql(db_config)
	#success = connect_mysql(json.dumps(db_config))
	print("*********")
	if success == True:
		 return "Success: DB connected", 200
	else:
		 return "FAIL: Could not connect to DB", 500

@app.route("/query", methods=["POST"])
def query_db():
	queries = request.get_json(force=True)
	# print 'Query data from client:', queries
	res = {}
	keys = queries.keys()
	try:
		keys.sort(key=int)
	except ValueError as e:
		return "All keys are not integer", 400
	# print keys

	for key in keys:
		res[key] = run_query(queries[key])

	response = app.response_class(
		response=json.dumps(res),
		status=200,
		mimetype='application/json'
		)
	return response

@app.route("/index")
def index():
    return _test("My Test Data")

@app.route("/redis/connect", methods=["POST"])
def connect_redis():
	redis_config = request.get_json(force=True)
	success = connect(redis_config);
	if success == True:
		return "Success : Redis connected", 200
	else:
		return "FAIL: Could not connect to Redis", 500

@app.route("/redis/get/<keys>", methods=["GET"])
def redis_get(keys):
	keys = [x.strip() for x in keys.split(',')]
	res = {}
	for key in keys:
		res[key] = get(key)
	return json.dumps(res)

@app.route("/redis/hget/<key>/<field>", methods=["GET"])
def redis_hget(key, field):
	key = key
	field = field
	res = {}
	res = hget(key, field)
	return json.dumps(res)

@app.route("/redis/set", methods=["POST"])
def redis_set():
	keyValuePairs = request.get_json(force=True)
	keys = keyValuePairs.keys()
	keys.sort()
	res = {}
	for key in keys:
		res[key] = set(key, keyValuePairs[key])
	return json.dumps(res)

@app.route("/redis/removeAll", methods=["GET"])
def redis_remove_keys():
	success = remove_all_keys()
	if  success == True:
		return "Success, all keys are removed", 200
	else:
		return "Failure, unable to remove keys", 500

def readFromFile(file):
	try:
		f = open(file, 'r')
		content = f.read()
		print content
		return content
	except Exception as e:
		print e
	return ""

if __name__ == "__main__":
    app.run(host="0.0.0.0" , debug=True)




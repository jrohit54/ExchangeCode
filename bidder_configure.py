from flask import Flask
from flask import request
import json
import os
import glob
import time
from gevent.wsgi import WSGIServer

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

logging.basicConfig(level=logging.DEBUG, filename='/opt/flaskAppForBidder.log')

# Redirect stdout and stderr
sys.stdout = LogFile('stdout')
sys.stderr = LogFile('stderr')

app = Flask(__name__)
log_dir = "/var/log/rtb_video_server_logs"
path = "/opt"
response_folder = "responses"
request_folder = "requests"
request_header_folder = "requestHeaders"
bidder_request_position = {}
global D
D = {}

@app.before_first_request
def startup():
	createDirectory(path + '/' + request_folder)
	createDirectory(path + '/' + response_folder)
	createDirectory(path + '/' + request_header_folder)

def createDirectory(path):
	print 'Creating directory at location: ', path
	if not os.path.exists(path):
		os.makedirs(path)

@app.route("/", methods=["POST"])
def hello():
	return "Hello World!"

@app.route("/configureResponse/<bidder>", methods=["POST"])
def configureResponse(bidder):
	global D
	bidder_response = request.data
	print 'Bidder: ', bidder
	if 'delay' in request.args:
		delayTime = request.args.get('delay')
		delayTime = float(delayTime)
		if type(delayTime) == int or type(delayTime) == float:
			D[bidder] = delayTime
			print 'map is ', D
			print 'Bidder Delay time in milli sec is: ',delayTime
	else:
		if bidder in D:
			del D[bidder]
	print 'Bidder response: ', bidder_response
	response_file = getFilePath(bidder, response_folder)
	print 'Saving response in file: ', response_file
	try:
		writeInFile(response_file, 'w', bidder_response)
	except Exception as e:
		print e
		return "Error in saving bidder response"
	return "Success: Bidder response saved", 200

@app.route("/<bidder>", methods=["POST"])
def getResponseForPOSTRequest(bidder):
	return getResponse(bidder, request.data, request.headers)

@app.route("/<bidder>", methods=["GET"])
def getResponseForGETRequest(bidder):
	return getResponse(bidder, request.url, request.headers)

@app.route("/<bidder>/<macro>", methods=["GET"])
def getResponseForGETRequestWithMacro(bidder,macro):
	return getResponse(bidder, request.url, request.headers)

def getStringFromHeaders(headers):
	dic = {}
	headers = headers.to_list()
	for header in headers:
		dic[header[0]] = header[1]
	return json.dumps(dic)

def getResponse(bidder, request, headers):
	if bidder in D.keys():
		delayTime = D[bidder]
		print 'map is', D
		print 'Bidder Delay time in milli sec is: ', delayTime
		if (int(delayTime) <=0):
			time.sleep(0)
		else:
			#delay is in milli seconds
			time.sleep(float(delayTime) / 1000.0)
	request_file = getFilePath(bidder, request_folder)
	request_header_file = getFilePath(bidder, request_header_folder)
	print 'Bidder: ', bidder
	print 'Bidder request: ', request
	print 'Bidder request headers: ', getStringFromHeaders(headers)
	try:
		writeInFile(request_file, 'a', request + "\n")
		writeInFile(request_header_file, 'a', getStringFromHeaders(headers) + "\n")
	except Exception as e:
		print 'Error in writing file'
		print e
	print 'Bidder request saved'
	response_file = getFilePath(bidder, response_folder)
	print 'Reading response from file: ', response_file
	return readFromFile(response_file)

@app.route("/getRequest/<bidder>", methods=["GET"])
def getRequest(bidder):
	request_file = getFilePath(bidder, request_folder)
	requests = readFromFile(request_file)
	print requests
	return requests

@app.route("/getRequest/<encoding>/<bidder>", methods=["GET"])
def getDecompressedRequest(bidder, encoding):
	request_file = getFilePath(bidder, request_folder)
	requests = readFromFile(request_file)
	header = {
		"Content-Encoding" : encoding
	}
	print requests
	return requests, 200, header

@app.route("/clearRequest/<bidder>", methods=["GET"])
def clearRequest(bidder):
	request_file = getFilePath(bidder, request_folder)
	try:
		deleteFile(request_file)
	except Exception as e:
		return "There is no request saved for this bidder"
	return "Requests cleared"

@app.route("/getHeader/<bidder>", methods=["GET"])
def getHeader(bidder):
	request_header_file = getFilePath(bidder, request_header_folder)
	headers = readFromFile(request_header_file)
	print headers
	return headers

@app.route("/clearHeader/<bidder>", methods=["GET"])
def clearHeader(bidder):
	request_header_file = getFilePath(bidder, request_header_folder)
	try:
		deleteFile(request_header_file)
	except Exception as e:
		return "There is no request headers saved for this bidder"
	return "Headers cleared"

@app.route("/clearResponse/<bidder>", methods=["GET"])
def clearResponse(bidder):
	response_file = getFilePath(bidder, response_folder)
	try:
		deleteFile(response_file)
	except Exception as e:
		return "There is no response saved for this bidder"
	return "Response cleared"

@app.route("/readLog/<fileName>", methods=["GET"])
def readLog(fileName):
	print "inside read logs"
	fileName = log_dir + "/" + fileName + ".log"
	print "reading from " + fileName
	content = ""
	if bool(bidder_request_position) == False :
		print "Markers not set!"
		return "Markers not set!"
	if fileName not in bidder_request_position:
		print "File " + fileName + " not found!"
		return "File " + fileName + " not found!"
	else:
		content = readNewContentFromFile(fileName)
		print content
	return content

@app.route("/setMarker", methods=["GET"])
def setMarker():
	extension = "log"
	dirPath = log_dir + "/*.{}"
	files = [i for i in glob.glob(dirPath.format(extension))]
	print "the log files are " , files
	for file in files:
		f = open(file, 'r')
		f.seek(0,2)
		bidder_request_position[file] = f.tell()
		f.close()
	print "the log files positions are ", bidder_request_position
	return "Reading log files Now"

def readFromFile(file):
	try:
		f = open(file, 'r')
		content = f.read()
		print content
		return content
	except Exception as e:
		print e
	return ""

def writeInFile(file, mode, content):
	f = open(file, mode)
	f.write(content)

def deleteFile(file):
	if os.path.isfile(file):
		os.remove(file)
		print("File: %s is removed" % file)
	else:
		print("Error: %s file not found" % file)
		raise e

def getFilePath(bidder, folder_name):
	return path + "/" + folder_name + "/" + bidder

def readNewContentFromFile(filePath):
	try:
		content = ""
		f = open(filePath, 'r')
		f.seek(bidder_request_position[filePath])
		print "reading in " + filePath + " from location " + str(bidder_request_position[filePath])
		content = f.read()
		bidder_request_position[filePath] = f.tell()
		print "new reading location for " + filePath + " set to " + str(bidder_request_position[filePath])
	except Exception as e:
		print e
	return content


if __name__ == "__main__":
    #app.run(host="0.0.0.0", port=5001, debug=True)
    http_server = WSGIServer(('0.0.0.0', 5001), app)
    http_server.serve_forever()
import MySQLdb
import json
import sys


cur = None
def connect_mysql(db_config):
        try:
		print("Inside connect_mysql")
                host=db_config["host"]
                user=db_config["user"]
                passwd=db_config["password"]
                db=db_config["database"]
                print("host="+str(host)+", user="+str(user)+",passwd="+str(passwd)+",db="+str(db))

		print("loading data"+str(type(db_config)))
		try:
                	db_config=json.loads(db_config)
		except:
			print("culprit!!")

		print("Trying to Connect with details ")
                conn = MySQLdb.connect(host=db_config["host"],user=db_config["user"],passwd=db_config["password"],db=db_config["database"],connect_timeout=500,autocommit=True,use_unicode=True,charset="utf8")
                #conn = MySQLdb.connect(host,user,passwd,db,connect_timeout=500,autocommit=True)
		print("Conneted to DB Successfully!")

		# Escape MySql
		# conn.escape_string()
		# cursor to execute all the queries you need
		global cur
		cur = conn.cursor()
		restore_DB(conn)
		print 'Dump loaded'
		delete_sensitive_data(conn)
		return True
	except Exception, e:
		print e
		return False

def run_query(query):
	global cur
	print query
	try:
		# cur.execute(MySQLdb.escape_string(query))
		cur.execute(query)
		return True
	except Exception, e:
		print e
		return False

def restore_DB(conn):
	print("Restoring DB")
	f = open('/home/rohit/rohit/Automation_Postman_scripts/automation_apps/Automation_apps/prodDbDumpWithDeltas.sql')
   	full_sql = f.read()
   	sql_commands = full_sql.split(';\n')
   	#print sql_commands
	noOfQueries=0
	queryLineNumber=0
   	for sql_command in sql_commands:
		queryLineNumber=queryLineNumber+1
   		if sql_command.startswith('INSERT INTO `traffic_share`') or sql_command.startswith('INSERT INTO `bidder_entity_preference`') or sql_command.startswith('UPDATE `traffic_share`') or sql_command.startswith('UPDATE `bidder_entity_preference`')  or sql_command.startswith('INSERT INTO `publisher_entity_preference`') or sql_command.startswith('UPDATE `publisher_entity_preference`'):
   			continue
   		#print sql_command
		noOfQueries=noOfQueries+1
		try:
			cur = conn.cursor()
			cur.execute(sql_command)
			cur.close()
		except:
			print("[Exception] : in this query "+str(sql_command)+" , at Line number "+str(queryLineNumber))
			if not sql_command.strip():
				print("BLANK LINE!!")
	print("No of Queries executed = "+str(noOfQueries))

def delete_sensitive_data(conn):
	try:
                #cur.execute("update bidder_urls set url='http://172.19.99.130/bidder1';")
                #print("update bidder_urls set url='http://172.19.99.130/bidder1';")
		cur = conn.cursor()
		cur.execute("LOCK TABLES `bidder_urls` WRITE;")
                cur.execute("update bidder_urls set url='http://10.6.33.102/bidder5.json';")
		cur.execute("UNLOCK TABLES;")
		cur.close()
                print("update bidder_urls set url='http://10.6.33.102/bidder5.json';")
	except Exception, e:
		print e

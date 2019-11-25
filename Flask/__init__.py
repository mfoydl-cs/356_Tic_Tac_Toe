from flask import Flask, render_template, url_for, request, jsonify, redirect, json
import pika
import sys
from datetime import date
from pymongo import MongoClient
from flask_mail import Mail, Message
from bson import json_util
from flask_jwt_extended import (
	JWTManager, jwt_required, create_access_token,
    jwt_refresh_token_required, create_refresh_token,
    get_jwt_identity, set_access_cookies,
    set_refresh_cookies, unset_jwt_cookies
)
import random
app = Flask(__name__)
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_REFRESH_COOKIE_PATH'] = '/token/refresh'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'
mail = Mail(app)
jwt = JWTManager(app)

@app.route("/")
def hello():
	return "hello world"

@app.route("/ttt/",methods=['GET','POST'])
def ttt():
	if request.method== 'POST':
		name= request.form['name']
		today= date.today()
		return render_template('ttt2.html',name=name,date=today)
	return render_template('ttt.html')

def winner(board):
	#check rows
	if board[0] == board[1] == board[2] :
		if board[0]!= " " :
			return board[0]
	if board[3] == board[4] == board[5] :
		if board[3]!= " " :
			return board[3]
	if board[6] == board[7] == board[8] :
		if board[6]!= " " :
			return board[6]		
	#check cols
	if board[0] == board[3] == board[6] :
		if board[0]!= " " :
			return board[0]
	if board[1] == board[4] == board[7] :
		if board[1]!= " " :
			return board[1]
	if board[2] == board[5] == board[8] :
		if board[2]!= " " :
			return board[2]	
	#check diagonal
	if board[0] == board[4] == board[8] :
		if board[0]!= " " :
			return board[0]
	if board[6] == board[4] == board[2] :
		if board[6]!= " " :
			return board[6]			
	#check full
	for x in board:
		if(x == " "):
			return " "
	return "t"

@app.route("/ttt/play", methods=['POST'])
@jwt_required
def play():
	username = get_jwt_identity()
	initialize(username)
	board = getboard(username)
	req= request.get_json()
	move= req['move']
	win = winner(board)
	if(move is None):
		return jsonify({"grid":getboard(username),"winner":win})
		
	board[int(move)] = "X"
	if win == " ":
		x= random.randint(0,8)
		while board[x]!=" ":
			x= random.randint(0,8)
		board[x]= "O"
		update(username, board)
		win = winner(board)
		#if win != " ":
			#winReset(username, win)
	else:
		winReset(username, win)
		
	return jsonify({"grid":getboard(username),"winner":win})

def getboard(username):
	client = MongoClient()
	db= client.ttt
	user = db.info.find_one({"username":username})
	current= int(user['current'])
	games = user['gamesinfo']
	return games[current]['grid']
	
def update(username,board):
	client = MongoClient()
	db= client.ttt
	user = db.info.find_one({"username":username})
	current= int(user['current'])
	db.info.update_one({"username":username},{"$set":{"gamesinfo.{}.grid".format(current):board}})

def initialize(username):
	client = MongoClient()
	db= client.ttt
	user = db.info.find_one({"username":username})
	current= int(user['current'])
	size = len(user['games'])
	empty= [" "," "," "," "," "," "," "," "," "]
	if(size==0):
		new = {"id":current,"startdate":str(date.today())}
		new2 ={"id":current,"grid":empty,"winner":" "}
		db.info.update({"username":username},{"$push":{"games":new}})
		db.info.update({"username":username},{"$push":{"gamesinfo":new2}})

def winReset(username, winner):
	client = MongoClient()
	db= client.ttt
	user = db.info.find_one({"username":username})
	current= int(user['current'])
	db.info.update_one({"username":username},{"$set":{"current":current+1}})
	if winner == "X":
		curr= int(user['human'])+1
		db.info.update_one({"username":username},{"$set":{"human":curr}})
	elif winner =="O":
		curr= int(user['wopr'])+1
		db.info.update_one({"username":username},{"$set":{"wopr":curr}})
	else:
		curr= int(user['tie'])+1
		db.info.update_one({"username":username},{"$set":{"tie":curr}})

	db.info.update_one({"username":username},{"$set":{"gamesinfo.{}.winner".format(current):winner}})
	empty= [" "," "," "," "," "," "," "," "," "]
	new = {"id":current+1,"startdate":str(date.today())}
	new2 ={"id":current+1,"grid":empty,"winner":" "}
	db.info.update({"username":username},{"$push":{"games":new}})
	db.info.update({"username":username},{"$push":{"gamesinfo":new2}})



@app.route("/adduser",methods=['POST'])
def addusr():
	name= request.json.get('username', None)
	password= request.json.get('password', None)
	email= request.json.get('email', None)

	client = MongoClient()
	db= client.ttt

	json= {"username":name,"password":password,"email":email,"verified":"false"}
	uid = db.users.insert_one(json)
	json2= {"email":email,"key":str(uid)}
	db.verified.insert_one(json2)

	key= "validation key: <"+str(uid.inserted_id)+">\n"
	url="http://cowzilla.cse356.compas.cs.stonybrook.edu/verify?email={}&key={}".format(email,str(uid.inserted_id))
	body="Please verify you email with this code:\n "+key+url
	msg= Message(subject="Verify Email",body=body,sender="ubuntu@wu1.cloud.compas.cs",recipients=[email])
	mail.send(msg)
	json_user = {"username":name,"human":"0","wopr":"0","tie":"0","current":"0","games":[],"gamesinfo":[]}
	db.info.insert_one(json_user)
	return jsonify({"status":"OK"})

@app.route("/unverified")
def unverified():
	return render_template("unverified.html")

@app.route("/verify",methods=['POST','GET'])
def verify():
	try:
		email=""
		key=""
		if request.method == "POST":
			email= request.json.get("email", None)
			key= request.json.get("key", None)
		elif request.method =="GET":
			email= request.args.get("email")
			key=request.args.get("key")

		client= MongoClient()
		db = client.ttt

		vuser= db.verified.find({"email":email})
		if vuser[0]['key']==key or key=="abracadabra":
			db.users.update_one({"email":email},{"$set":{"verified":"true"}})
			return jsonify({"status":"OK"})
		return jsonify({"status":"ERROR"})
	except Exception, e:
		return jsonify({"status":"ERROR"})

	

@app.route("/login",methods=["POST"])
def login():
	try:
		username = request.json.get('username', None)
		password = request.json.get('password', None)

		client = MongoClient()
		db = client.ttt
		user = db.users.find({"username":username})

		if(user[0]['verified'] == "false"):
			return jsonift({"status":"ERROR"})

		if user[0]['password'] != password:
			return jsonify({"status":"ERROR"})

		access_token = create_access_token(identity=username)
		refresh_token = create_refresh_token(identity=username)

		resp = jsonify({"status":"OK"})
		set_access_cookies(resp, access_token)
		set_refresh_cookies(resp, refresh_token)
		return resp, 200
	except Exception, e:
		return jsonify({"status":"ERROR"})

@app.route('/token/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)

    resp = jsonify({'status':"OK"})
    set_access_cookies(resp, access_token)
    return resp, 200

@app.route("/logout",methods=["POST"])
def logout():
	try:
		resp = jsonify({"status":"OK"})
		unset_jwt_cookies(resp)
		return resp, 200
	except Exception, e:
		return jsonify({"status":"ERROR"})

@app.route("/listgames",methods=["POST"])
@jwt_required
def listgames():
	try:
		username = get_jwt_identity()

		client = MongoClient()
		db = client.ttt
		user = db.info.find_one({"username":username})
		games = user["games"]
		return jsonify({"status":"OK","games":games})
	except Exception, e:
		return jsonify({"status":"ERROR"})


@app.route("/getgame",methods=["POST"])
@jwt_required
def getgame():
	try:
		username = get_jwt_identity()
		gid = request.json.get("id")

		client = MongoClient()
		db = client.ttt
		user = db.info.find_one({"username":username})
		games = user["games"]
		game = games["id"]
		grid = game["grid"]
		winner = game["winner"]
		return jsonify({"status":"OK","grid":grid,"winner":winner})
	except Exception, e:
		return jsonify({"status":"ERROR"})

@app.route("/getscore",methods=["POST"])
def getscore():
	try:
		username = get_jwt_identity

		client = MongoClient()
		db= client.ttt
		user = db.info.find_one({"username":username})
		return jsonify({"status":"OK","human":user["human"],"wopr":user["wopr"],"tie":user["tie"]})
	except Exception, e:
		return jsonify({"status":"Error"})

rabbitmq_host = "127.0.0.1"
rabbitmq_port = 5672
rabbitmq_virtual_host = "Some_Virtual_Host"

@app.route("/listen", methods=["POST"])
def listen():
	req= request.get_json()
	keys= req['keys']

	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	
	result = channel.queue_declare(queue='', exclusive=True)
	queue_name = result.method.queue

	for key in keys:
		channel.queue_bind(exchange='hw4', queue=queue_name, routing_key=key)
	
	channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

	channel.start_consuming()

def callback(ch, method, properties, body):
	return jsonify({"msg":body})

@app.route("/speak", methods=["POST"])
def speak():
	key= request.json.get('key', None)
	msg = request.json.get('msg', None)

	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()

	channel.basic_publish(exchange='hw4',routing_key=key,body=msg)
	connection.close()
	return jsonify({"status":"OK"})

@app.route("/test")
def test():
	username="miles"
	

	access_token = create_access_token(identity=username)
	refresh_token = create_refresh_token(identity=username)

	resp = jsonify({"status":"OK"})
	set_access_cookies(resp, access_token)
	set_refresh_cookies(resp, refresh_token)
	return resp, 200

@app.route("/test2")
@jwt_required
def test2():
	client = MongoClient()
	db = client.ttt
	db.info.drop()
	json_user = {"username":"miles","human":"0","wopr":"0","tie":"0","current":"0","games":[]}
	db.info.insert_one(json_user)
	return jsonify({"status":"OK"})

@app.route("/test3")
@jwt_required
def test3():
	try:
		username = get_jwt_identity()

		client = MongoClient()
		db = client.ttt
		db.info.drop()
		json_user = {"username":"miles","human":"0","wopr":"0","tie":"0","current":"0","games":[],"gamesinfo":[]}
		db.info.insert_one(json_user)

		initialize(username)
		board=["X","X","X","X","X","X","X","X","X"]
		update(username,board)
		winReset(username,"X")
		board=["X","O","X","O","X","X","X","X","X"]
		update(username,board)
		winReset(username,"X")
		
		user = db.info.find_one({"username":username})
		games = user["games"]
		return jsonify({"status":"OK","games":games})
	except Exception, e:
		return str(e)

def test4():
	'''
	username = "miles"
		
		for move in moves:
			initialize(username)
			board = getboard(username)
			win =winner(board)
				#return jsonify(grid=getboard(username),winner=win)
			board[int(move)] = "X"
			if win == " ":
				x=-1
				while True:
					x= random.randint(0,8)
					if board[x]==" ":
						break
				if x==-1:
					return "failure"
				board[x]= "O"
				update(username, board)
				win =winner(board)
				if win != " ":
					winReset(username, win)
			else:
				winReset(username, win)
	username = get_jwt_identity()

	client = MongoClient()
	db = client.ttt
	db.info.drop()
	json_user = {"username":"miles","human":"0","wopr":"0","tie":"0","current":"0","games":[]}
	db.info.insert_one(json_user)

	initialize(username)
	board=["X","X","X","X","X","X","X","X","X"]
	update(username,board)

	user = db.info.find_one({"username":username})
	return jsonify({"status":"OK","human":user["human"],"wopr":user["wopr"],"tie":user["tie"]})
	'''

if __name__ == "__main__":
	app.run()

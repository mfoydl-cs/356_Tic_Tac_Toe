from flask import Flask, render_template, url_for, request, jsonify
from datetime import date
import random
app = Flask(__name__)

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
def play():
	board= request.get_json()['grid']
	win = winner(board)
	if win == " ":
		x= random.randint(0,8)
		while board[x]!=" ":
			x= random.randint(0,8)
		board[x]= "O"
		win = winner(board)
	return jsonify(grid=board,winner=win)



if __name__ == "__main__":
	app.run()

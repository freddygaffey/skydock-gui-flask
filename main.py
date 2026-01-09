from flask import Flask, render_template, request, jsonify
from drone import drone

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/command", methods=["POST"])
def handle_command():
    data = request.json
    command = data.get("command")
    print(f"Received command: {command}")
    return jsonify(status="Command received")

@app.route("/incoming_question")
def incoming_q_check():
    question = drone.get_unanswerd_question()
    return question if question else "None"

@app.route("/question_answer", methods=["POST"])
def question_answer():
#    {'command': 'Accepted', 'question': ' takoff'} 
    data = request.json
    print(data)
    drone.answer_question(question=data["question"],answer=data["command"])
    return "all good"

@app.route("/send/float", methods=["POST"])
def send_float_pymavlink():
    data = request.json
    drone.send_float(data["command"],data["parameter"])
    print(data)
    return "all good"

    
@app.route("/map")
def desplay_map():
    return render_template("mapping.html")

if __name__ == "__main__":
    drone.connect("/dev/rfcomm90")
    app.run(debug=False)


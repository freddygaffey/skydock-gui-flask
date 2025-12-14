from flask import Flask, render_template, request, jsonify
from drone import check_drone_question

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
    question = check_drone_question()
    return question if question else "None"

@app.route("/question_answer", methods=["POST"])
def question_answer():
    data = request.json
    print(data)
    return "hi go away"
    # question = data.get("question")  # <- the question text
    # answer = data.get("command")     # <- the user answer ("Accepted" / "Rejected")

    # # Now you have both
    # print(f"Question: {question}")
    # print(f"User answered: {answer}")

    # # Optionally, do something with it (e.g., feed it to your simulator)
    # return jsonify(status="Response received")


if __name__ == "__main__":
    app.run(debug=True)


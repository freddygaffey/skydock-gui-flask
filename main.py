from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/command", methods=["POST"])
def handle_command():
    data = request.json
    command = data.get("command")
    # Here, you can handle the command logic or pass it to the Raspberry Pi
    print(f"Received command: {command}")
    return jsonify(status="Command received")

if __name__ == "__main__":
    app.run(debug=True)

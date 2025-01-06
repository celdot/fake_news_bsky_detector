from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
app = CORS(app)
@app.route('/receive', methods=['POST'])
def receive_input():
    data = request.get_json()
    user_input = data.get('input', '')
    print(f"Received input: {user_input}")
    return jsonify({"status": "success", "received": user_input}), 200
if __name__ == '__main__':
    app.run(debug=True)
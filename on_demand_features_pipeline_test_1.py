import os

import hopsworks
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

import features_processing_utils as fpu
from inference_pipeline import inference

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://celdot.github.io"}})

# CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/receive', methods=['POST'])
def receive_input():
    print("POST request received!")
    
    data = request.get_json()
    user_input = data.get('input', '')
    print(f"Received input: {user_input}")
    
    # Retrieve the API key from the environment variable
    api_key = os.environ.get("HOPSWORKS_API_KEY")
    print("api key is", api_key[:10])
    
    if not api_key:
        print("API Key not found!")
        return jsonify({"status": "error", "message": "API Key not found"}), 500

    # Log in to Hopsworks using the API key
    project = hopsworks.login(api_key_value=api_key)
    print("Connected to Hopsworks, yay !")
    
    result = inference(user_input)
    print(f"Result: {result}")
    
    response = jsonify({"status": "success", "results": result})
    response.headers.add("Access-Control-Allow-Origin", "https://celdot.github.io")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")

    return response, 200 # Send result back as JSON

if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=8080)
    app.run(host='0.0.0.0', port=8080, debug=True)
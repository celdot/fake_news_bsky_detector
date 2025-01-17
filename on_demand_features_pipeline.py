import os

import hopsworks
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

import features_processing_utils as fpu
from inference_pipeline import inference

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/receive', methods=['POST'])
def receive_input():
    data = request.get_json()
    user_input = data.get('input', '')
    
    # Retrieve the API key from the environment variable
    api_key = os.environ.get("HOPSWORKS_API_KEY")
    
    if not api_key:
        return jsonify({"status": "error", "message": "API Key not found"}), 500

    # Log in to Hopsworks using the API key
    project = hopsworks.login(api_key_value=api_key)

    fs = project.get_feature_store()
    query_fg = fs.get_or_create_feature_group(
        name='user_query',
        description='Name of news article from user input',
        version=1,
        primary_key=['news_id'],
        online_enabled=True,
    )
    
    try :
        queries_df = query_fg.read()
    except:
        queries_df = pd.DataFrame()
    
    query_features = fpu.process_query(user_input)
    if isinstance(query_features, str):  # Check if error message was returned
        response = jsonify({"status": "success", "results": query_features})
        
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        
        return response, 200
    
    query_features.columns = query_features.columns.str.replace(' ', '_')
    
    queries_df = pd.concat([queries_df, query_features], ignore_index=True)

    query_fg.insert(queries_df, write_options={"wait_for_job": True})
    
    result = inference(user_input, project, fs)
    
    response = jsonify({"status": "success", "results": result})
    
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")

    return response, 200 # Send result back as JSON

if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=8080)
    app.run(host='0.0.0.0', port=8080, debug=True)
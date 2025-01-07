import hopsworks
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

import features_processing_utils as fpu
from inference_pipeline import inference

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://celdot.github.io"}})

@app.route('/receive', methods=['POST'])
def receive_input():
    print(HOPSWORKS_API_KEY[:5] )
    data = request.get_json()
    user_input = data.get('input', '')
    print(f"Received input: {user_input}")
    
    project = hopsworks.login()
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
    query_features.columns = query_features.columns.str.replace(' ', '_')
    
    queries_df = pd.concat([queries_df, query_features], ignore_index=True)

    query_fg.insert(queries_df, write_options={"wait_for_job": True})
    
    print("finished writing to feature store")
    
    result = inference(user_input)
    print(f"Result: {result}")

    return jsonify({"status": "success", "results": result}), 200 # Send result back as JSON

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
import feature_processing_utils as fpu
import hopsworks
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

project = hopsworks.login()
fs = project.get_feature_store()
query_fg = fs.get_or_create_feature_group(
    name='user_query',
    description='Name of news article from user input',
    version=1,
    primary_key=['news_id'],
    online_enabled=True,
)
queries_df = query_fg.read()

@app.route('/receive', methods=['POST'])
def receive_input():
    data = request.get_json()
    user_input = data.get('input', '')
    print(f"Received input: {user_input}")
    
    query_features = fpu.process_query(user_input)
    query_features.columns = query_features.columns.str.replace(' ', '_')
    
    queries_df = pd.concat([queries_df, query_features], ignore_index=True)

    query_fg.insert(queries_df, write_options={"wait_for_job": True})

    return jsonify({"status": "success", "received": user_input}), 200

if __name__ == '__main__':
    app.run(debug=True)
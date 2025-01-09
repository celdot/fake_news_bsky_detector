import os

import hopsworks
import joblib
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier


def inference(input, project, fs):
    # Get the model registry
    mr = project.get_model_registry()
    
    # Retrieve the model from the model registry
    retrieved_model = mr.get_model(
        name="news_propagation_model",
        version=15,
    )

    # Download the saved model files to a local directory
    saved_model_dir = retrieved_model.download()
    
    # Load the model from a saved JSON file
    model = joblib.load(os.path.join(saved_model_dir, "model.joblib"))
    
    user_query_fg = fs.get_feature_group(
                    name="user_query",
                    version=1)
    
    features_to_predict = user_query_fg.select_except(["news_id"]).read()
        
    prediction = model.predict(features_to_predict.tail(1))
    
    if prediction == 0:
        return(f"The news {input} is real")
    else:
        return(f"The news {input} is fake")
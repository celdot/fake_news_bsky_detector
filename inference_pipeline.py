import os

import hopsworks
import joblib
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier


def inference(input):
    project = hopsworks.login()

    # Get the model registry
    mr = project.get_model_registry()
    
    # Retrieve the model from the model registry
    retrieved_model = mr.get_model(
        name="news_propagation_model",
        version=15,
    )

    # Download the saved model files to a local directory
    saved_model_dir = retrieved_model.download()
    
    # Initialize the model
    model = RandomForestClassifier()
    
    # Load the model from a saved JSON file
    model = joblib.load(os.path.join(saved_model_dir, "model.joblib"))
    
    # Get features to predict
    fs = project.get_feature_store()
    
    user_query_fg = fs.get_feature_group(
                    name="user_query",
                    version=1)
    
    user_query = user_query_fg.select_all().read()
    features_to_predict = user_query_fg.select_except(["news_id"]).read()
    
    predictions_fg = fs.get_or_create_feature_group(
    name="news_propagation_predictions",
    version=1,
    description="News propagation prediction results",
    primary_key=["user_query"],
    )
    
    try :
        predictions_df = predictions_fg.read()
    except:
        predictions = model.predict(features_to_predict)
        predictions_df = user_query["news_id"].to_frame().rename(columns={"news_id": "user_query"})
        predictions_df["prediction"] = predictions
        
    prediction = model.predict(features_to_predict.tail(1))
    new_prediction = pd.DataFrame({"user_query": user_query.tail(1)["news_id"].values[0], "prediction": prediction})
    predictions_df = predictions_df._append(new_prediction, ignore_index=True)
    
    predictions_df["prediction"] = predictions_df["prediction"].astype(int)
    print("added predictions, now inserting")
    
    predictions_fg.insert(predictions_df, write_options={"wait_for_job": True})
    
    if prediction == 0:
        print("The news is real")
        return(f"The news {input} is real")
    else:
        print("The news is fake")
        return(f"The news {input} is fake")
    
def inference_test(user_input):
    print("well received")
    return f"The news {user_input} was well received"
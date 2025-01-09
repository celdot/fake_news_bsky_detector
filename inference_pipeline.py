import os

import joblib


def inference(input, project, fs):
    mr = project.get_model_registry()
    
    # Retrieve the model from the model registry
    retrieved_model = mr.get_model(
        name="news_propagation_model",
        version=16,
    )

    # Download the saved model files to a local directory
    saved_model_dir = retrieved_model.download()
    
    # Load the model from a saved JSON file
    model = joblib.load(os.path.join(saved_model_dir, "model.joblib"))
    
    user_query_fg = fs.get_or_create_feature_group(
        name='user_query',
        description='Name of news article from user input',
        version=1,
        primary_key=['news_id'],
        online_enabled=True,
    )
    
    print("got feature group")
    
    features_to_predict = user_query_fg.select_except(["news_id"]).read()
        
    prediction = model.predict(features_to_predict.tail(1))
    
    if prediction == 0:
        return(f"The news: {input} is real.")
    else:
        return(f"The news: {input} is fake.")
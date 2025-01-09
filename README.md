# Blue Sky Fake News Detector

<img src="./img/new_logo.png" alt="Hopsworks Logo" width="200" height="200"> <img src="./img/google_cloud.webp" alt="Google Cloud Logo" width="200" height="200"> <img src="./img/bluesky-logo.jpg" alt="Blue Sky Logo" width="200">

### Project description

This project implements a pipeline for fake news detection, using the propagation behaviour of the real and fake news in social medias like Twitter. The project leverages Hopsworks for feature management and model storage, GitHub Actions for automation, and GitHub Pages for visualizationa and user interface. The social media Blue Sky is used to retrieve posts about a specific news, with its API.

 The project implements the paper [Fake News Detection on Twitter Using Propagation
 Structures](https://link.springer.com/chapter/10.1007/978-3-030-61841-4_10) from Marion Meyers(B), Gerhard Weiss, and Gerasimos Spanakis, with the social media Blue Sky as the source of the posts, instead of Twitter.

---

## Project Structure

The project is divided into the following components:

![Project structure](/img/fake_news_project_structure.png)

### 1. **Feature Engineering and Data Management**
- **`features_processing_utils.py`**: Contains utility functions for scraping posts with the Bsky API and processing features about the propagation graph of the posts and their reposts in Bsky.
- **`historical_features_pipeline.ipynb`**: Scrapes posts about news in the FakeNewsNet dataset, compute their features, and backfills those features into a feature group in Hopsworks. Handles data unbalance by oversampling the fake news.
- **`on_demand_feature_pipeline.py`**:  Includes a Flask server that processes requests and generates features from user input, about a piece of news, on demand. Scrapes posts related to it in Blue Sky, before computing the features and storing them in Hopsworks in a feature group. The Flask server is deployed on Google Cloud to ensure scalability and reliability.

### 2. **Model Training**
- **`model_training_pipeline.ipynb`**: Trains a Random Forest classification model (from sklearn) locally and stores it in Hopsworks. Hyperparameters tuning is also done locally and the best model is selected for inference. Feature importance and the confusion matrix are extracted during this process.

### 3. **Batch Inference**
- **`inference_pipeline.py`**: Runs on-demand to make the prediction whether a piece of news is fake or not, before comparing it to the data in Politifacts and Gossicop.

---

## User Interface and Visualization Dashboard

A user interface hosted on GitHub Pages allows the user to put in the name of a news article and see the predictions of the model about the veracity of that article.
This UI consists of:
- **a static page** : Displays general information about the project.
- **a dynamic page**: Interacts with the Flask server deployed on Google Cloud to retrieve real-time predictions and updates.

The user can monitor the model's performance on the static page:
1. A graph of feature importance from the trained model.
2. A confusion matrix showing the model's performance.

The assets for these visualizations are stored in the respective directories:
- **Feature Importance**: `figures/feature_importance.png`
- **Confusion Matrix**: `figures/confusion_matrix.png`

---

## How to Use

1. **Run Pipelines**:
   - Backfill historical data (`historical_features_pipeline.ipynb`).
   - Train the model (`model_training_pipeline.ipynb`).

2. **Deploy Flask Server on Google Cloud**:
   - Build the Docker Image:
      ```bash 
      gcloud builds submit --config ./cloudbuild.yaml .```
   - Deploy the Container:
      ```bash 
      gcloud run deploy fake-news-flask-server-image --image gcr.io/fake-news-bsky-detection/fake-news-flask-server-image --platform managed --region europe-west2 --allow-unauthenticated --update-env-vars HOPSWORKS_API_KEY=[HOPSWORKS_API_KEY]```
  
3. **View Results**:
   - Visit the [Github Pages](https://celdot.github.io/fake_news_bsky_detector/) site to input a news article, view the predictions, and monitor the model.

---

## Data

The FakeNewsNet dataset is taken from [Politifacts](https://www.politifact.com/) and [Gossicop]( www.snopes.com.). The posts about the news are scraped from the social media [Blue Sky](https://bsky.app/).

---

## Improvements

- The inference process takes about 5 min from the moment the request is received to the server to the moment the prediction is made. This time could be reduced by optimizing the feature engineering process. Indeed, the more popular a news is, the more posts about it are scraped, and the longer the process takes. This could be improved by limiting the number of posts scraped. The features computed are also pushed to a Hopsworks feature store, which takes about 3 min.
- The model could be improved, as only an accuracy of 70% is achieved here, while the paper achieves 87%.
  It could be improved with a model-centric method : spending more time on the model selection (like XGBoost instead of a Random Forest for example), features selection for the training, and hyperparameters tuning.
  It can also be achieved with a data-centric method. A lot of posts that are scraped are actually irrelevant to the news, and could be filtered out. We didn't find any way to filter them out, but it could be done by using an NLP model to filter the irrelevant posts out beforehand, or by using a more advanced API to scrape the posts.
  A lot of news that were in the FakeNewsNet dataset were not found by the Blue Sky API and search engine, which significantly reduces the size of the dataset and the model's performance.
  Thus, the performance of the model could have been higher if the social media used was Twitter, as in the paper, instead of Blue Sky.



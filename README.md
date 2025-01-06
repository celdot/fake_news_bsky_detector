# fake_news_bsky_detector

Write a report about you have done, the dataset, your method, your results, and how to run the code.

### Project description

This project implements a pipeline for fake news detection, using the propagation behaviour of the real and fake news in social medias like Twitter. The project leverages Hopsworks for feature management and model storage, GitHub Actions for automation, and GitHub Pages for visualizationa and user interface. The social media Blue Sky is used to retrieve posts about a specific news, with its API.

 The project implements the paper [Fake News Detection on Twitter Using Propagation
 Structures](https://link.springer.com/chapter/10.1007/978-3-030-61841-4_10) from Marion Meyers(B), Gerhard Weiss, and Gerasimos Spanakis, with the social media Blue Sky as the source of the posts, instead of Twitter.

---

## Project Structure

The project is divided into the following components:

![Hopsworks Logo](./img/project_structure.png)

### 1. **Feature Engineering and Data Management**
- **`features_processing_utils.py`**: Contains utility functions for scraping posts with the Bsky API and processing features about the propagation graph of the posts and their reposts in Bsky.
- **`historical_features_pipeline.ipynb`**: Scrapes posts about news in the FakeNewsNet dataset, compute their features, and backfills those features into a feature group in Hopsworks. Handles data unbalance by oversampling the fake news.
- **`on_demand_feature_pipeline.py`**: Runs on demand to take in user input about a news article and scrape posts related to it in Blue Sky, before computing the features and storing them in Hopsworks in a feature group.

### 2. **Model Training**
- **`model_training_pipeline.ipynb`**: Trains an XGBoost classification model locally and stores it in Hopsworks. Hyperparameters tuning is also done locally and the best model is selected for inference. Feature importance and the confusion matrix are extracted during this process.

### 3. **Batch Inference**
- **`inference_pipeline.py`**: Runs on-demand to make the prediction whether a piece of news is fake or not, before comparing it to the data in Politifacts and Gossicop.

---

## Automation with GitHub Actions

The pipelines `on_demand_feature_pipeline.py` and `inference_pipeline.py` are executed on-demand through a GitHub Actions workflow defined in `.github/workflows/fake_news_detection.yml`.

---

## Visualization Dashboard

A user interface hosted on GitHub Pages allows the user to put in the name of a news article and view the predictions of the model about the veracity of that article.

The user can also monitor the model's performance.:
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
   - Set up GitHub Actions to execute `on_demand_feature_pipeline.py` and `inference_pipeline.py` on-demand.
  
2. **View Results**:
   - Visit the [Github Pages](https://celdot.github.io/fake_news_bsky_detector/) site to input a news article, view the predictions, and monitor the model.

---

## Data

The FakeNewsNet dataset is taken from [Politifacts](https://www.politifact.com/) and [Gossicop]( www.snopes.com.). The posts about the news are scraped from the social media [Blue Sky](https://bsky.app/).

---

## Improvements



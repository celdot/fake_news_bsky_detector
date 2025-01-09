import json

import pandas as pd
import requests
from tqdm import tqdm


def get_profile(username):
    response = requests.get("https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=" + username)
    data = response.json()
    return data

def get_post(uri):
    response = requests.get("https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?uris=" + uri)
    data = response.json()
    return data

def get_reposts(uri, limit=100):
    response = requests.get(f"https://public.api.bsky.app/xrpc/app.bsky.feed.getRepostedBy?uri={uri}&limit={limit}")
    data = response.json()
    return data

def get_feed(username, limit=100):
    response = requests.get(f"https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor={username}&limit={limit}")
    data = response.json()
    return data

def search_posts(query, limit=100):
    response = requests.get(f"https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q={query}&limit={limit}")
    data = response.json()
    return data

def get_post_info(dataset, post, news, query, IsQuery=False):
    profile = get_profile(post["author"]["handle"])
    dataset["post_uri"].append(post["uri"])
    dataset["post_cid"].append(post["cid"])
    dataset["date"].append(post["record"]["createdAt"])
    dataset["like_count"].append(post["likeCount"])
    dataset["repost_count"].append(post["repostCount"])
    dataset["user_name"].append(post["author"]["handle"])
    dataset["follower_count"].append(profile["followersCount"])
    dataset["follows_count"].append(profile["followsCount"])
    if not IsQuery:
        dataset["news_id"].append(news[news["title"] == query]["id"].values[0])
    else:
        dataset["news_id"].append(query)
    
    return dataset

def add_posts(news, limit=100, IsQuery=False):
    dataset = {
        "post_uri": [],
        "post_cid": [],
        "type": "post",
        "date": [],
        "news_id": [],
        "like_count": [],
        "repost_count": [],
        "user_name": [],
        "follower_count": [],
        "follows_count": [],
    }

    no_posts_found = True  # Flag to track if any posts are found

    for query in tqdm(news["title"]):
        try:
            posts = search_posts(query, limit)
        except json.JSONDecodeError:
            continue

        try:
            posts_list = posts["posts"]
        except KeyError:
            posts_list = []

        if posts_list:
            no_posts_found = False

        for post in posts_list:
            try:
                dataset = get_post_info(dataset, post, news, query, IsQuery)
            except KeyError:
                pass

    if no_posts_found and IsQuery:
        return "Sorry, no posts concerning your news were found."

    dataframe = pd.DataFrame(
        dataset,
        columns=[
            "post_uri",
            "post_cid",
            "type",
            "date",
            "news_id",
            "like_count",
            "repost_count",
            "user_name",
            "follower_count",
            "follows_count",
        ],
    )

    return dataframe

def get_repost_info(dataset, user, query, posts_dataset):   
    profile = get_profile(user["handle"])
    dataset["follower_count"].append(profile["followersCount"])
    dataset["follows_count"].append(profile["followsCount"])
    dataset["user_name"].append(user["handle"])
    dataset["post_uri"].append(posts_dataset[posts_dataset["post_uri"] == query]["post_uri"].values[0])
    dataset["post_cid"].append(posts_dataset[posts_dataset["post_uri"] == query]["post_cid"].values[0])
    dataset["retweet_date"].append(posts_dataset[posts_dataset["post_uri"] == query]["date"].values[0])
    dataset["news_id"].append(posts_dataset[posts_dataset["post_uri"] == query]["news_id"].values[0])
    dataset["like_count"].append(posts_dataset[posts_dataset["post_uri"] == query]["like_count"].values[0])
    dataset["repost_count"].append(posts_dataset[posts_dataset["post_uri"] == query]["repost_count"].values[0])
    
    return dataset

def add_reposts(posts_dataset, limit=100):
    
    dataset = {"post_uri": [],
                "post_cid": [],
                "type": "repost",
                "retweet_date": [],
                "news_id": [],
                "like_count": [],
                "repost_count": [],
                "user_name": [],
                "follower_count": [],
                "follows_count": [],
                }
    
    for query in tqdm(posts_dataset["post_uri"]):
        try:
            reposts = get_reposts(query, limit)
        except json.JSONDecodeError:
            pass
        try:
            reposts_list = reposts["repostedBy"]
        except KeyError:
            reposts_list = []
        for user in reposts_list:
            try:
                dataset = get_repost_info(dataset, user, query, posts_dataset)
            except KeyError: 
                pass
            
    dataframe = pd.DataFrame(dataset, columns=["post_uri", "post_cid", "type", "retweet_date", "news_id", "like_count", "repost_count", "user_name", "follower_count", "follows_count"])
            
    return dataframe

def create_dataset(news, limit=100, IsQuery=False):
    posts_dataset = add_posts(news, limit, IsQuery)
    if isinstance(posts_dataset, str):  # Check if error message was returned
        return posts_dataset

    reposts_dataset = add_reposts(posts_dataset, limit)
    return pd.concat([posts_dataset, reposts_dataset])

def count_users_within_10_hours(group):
    # Filter users within 10 hours of the minimum date for each group
    min_date = group["date"].min()
    filtered_users = group[group["date"] <= min_date + pd.Timedelta(hours=10)]["user_name"]
    return filtered_users.nunique()

def calculate_repost_post_counts(group):
    # Step 1: Filter rows where date is within 1 hour of the minimum date in the group
    min_date = group["date"].min()
    filtered_group = group[group["date"] < min_date + pd.Timedelta(hours=1)]
    
    # Step 2: Count "type" occurrences within the filtered group
    type_counts = filtered_group["type"].value_counts()
    repost_count = type_counts.get("repost", 0)  # Safely get the "repost" count
    post_count = type_counts.get("post", 0)      # Safely get the "post" count
    
    # Return a Series with the counts and the group key
    return pd.Series({"repost_count_1hour": repost_count, "post_count_1hour": post_count})

import pandas as pd


def convert_to_datetime(dataframe):
    dataframe["date"] = pd.to_datetime(dataframe["date"], format='ISO8601', utc=True)
    dataframe["retweet_date"] = pd.to_datetime(dataframe["retweet_date"], format='ISO8601', utc=True)
    dataframe["time_difference"] = (dataframe["date"] - dataframe["retweet_date"]).dt.total_seconds()
    return dataframe

def calculate_average_followers(news_df):
    return news_df["follower_count"].mean().reset_index().rename(columns={"follower_count": "average followers"})

def calculate_average_follows(news_df):
    return news_df["follows_count"].mean().reset_index().rename(columns={"follows_count": "average follows"})

def calculate_repost_total(dataframe):
    return dataframe[["repost_count", "news_id"]].groupby("news_id").sum().fillna(0).reset_index().rename(columns={"repost_count": "repost total"})

def calculate_post_total(news_df):
    return news_df["post_cid"].nunique().fillna(0).reset_index().rename(columns={"post_cid": "post total"})

def calculate_repost_percentage(features_df):
    features_df["repost percentage"] = features_df["repost total"] / (features_df["repost total"] + features_df["post total"])
    return features_df

def calculate_average_repost(dataframe, features_df):
    reposts = dataframe[dataframe["type"] == "repost"]
    repost_counts = reposts.groupby("post_cid")["repost_count"].sum().reset_index().rename(columns={"repost_count": "reposts_per_posts"})
    repost_counts = dataframe.merge(repost_counts, on="post_cid", how="left")
    total_reposts_per_news = repost_counts.groupby("news_id")["reposts_per_posts"].sum()
    average_repost = (total_reposts_per_news / (features_df.set_index("news_id")["repost total"] + features_df.set_index("news_id")["post total"])
                      ).fillna(0).reset_index().rename(columns={0: "average repost"})
    return features_df.merge(average_repost, on="news_id", how="left")

def calculate_average_favorite(news_df):
    return news_df["like_count"].mean().reset_index().rename(columns={"like_count": "average favorite"})

def calculate_news_lifetime(news_df):
    news_lifetime = (news_df["date"].max() - news_df["date"].min()).dt.total_seconds().reset_index().rename(columns={"date": "news lifetime"})
    return news_lifetime

def count_users_within_10_hours(news_df):
    return news_df.apply(lambda x: x["retweet_date"].between(x["date"], x["date"] + pd.Timedelta(hours=10)).sum()).reset_index().rename(columns={0: "nb users 10 hours"})

def calculate_average_time_difference(news_df):
    return news_df["time_difference"].mean().reset_index().rename(columns={"time_difference": "average time difference"})

def calculate_repost_post_counts(news_df):
    repost_post_counts = news_df.apply(lambda group: {
        "repost_count_1hour": group["retweet_date"].between(group["date"], group["date"] + pd.Timedelta(hours=1)).sum(),
        "post_count_1hour": group["date"].between(group["date"], group["date"] + pd.Timedelta(hours=1)).sum()
    })
    return pd.DataFrame(repost_post_counts.tolist())

def get_features(dataframe, label, query=False):
    dataframe = convert_to_datetime(dataframe)
    news_df = dataframe.groupby("news_id")
    
    features_df = pd.DataFrame({"news_id": news_df.groups.keys()})
    
    features_df = features_df.merge(calculate_average_followers(news_df), on="news_id", how="left")
    features_df = features_df.merge(calculate_average_follows(news_df), on="news_id", how="left")
    features_df = features_df.merge(calculate_repost_total(dataframe), on="news_id", how="left")
    features_df = features_df.merge(calculate_post_total(news_df), on="news_id", how="left")
    
    features_df = calculate_repost_percentage(features_df)
    features_df = calculate_average_repost(dataframe, features_df)
    features_df = features_df.merge(calculate_average_favorite(news_df), on="news_id", how="left")
    features_df = features_df.merge(calculate_news_lifetime(news_df), on="news_id", how="left")
    features_df = features_df.merge(count_users_within_10_hours(news_df), on="news_id", how="left")
    features_df = features_df.merge(calculate_average_time_difference(news_df), on="news_id", how="left")
    
    counts_df = calculate_repost_post_counts(news_df)
    features_df = pd.concat([features_df, counts_df[["repost_count_1hour", "post_count_1hour"]]], axis=1)
    features_df["retweet percentage 1 hour"] = (
        (features_df["repost_count_1hour"] + features_df["post_count_1hour"]) /
        (features_df["repost total"] + features_df["post total"]
        )
    ).fillna(0)
    features_df = features_df.drop(columns=["repost_count_1hour", "post_count_1hour"])
    
    if not query:
        features_df["label"] = label
    
    return features_df

def complete_processing(source, label, posts_name, feature_name, start=None, end=None):
    posts = create_dataset(source[start:end])
    posts.to_csv("data/" + posts_name, index=False)
    features = get_features(posts, label)
    features.to_csv("data/" + feature_name, index=False)
    
    return features

def process_query(query):
    posts = create_dataset(pd.DataFrame({"title": [query]}), 100, True)
    if isinstance(posts, str):  # Check if error message was returned
        return posts

    print("finished scraping posts")
    features = get_features(posts, None, True)
    print("finished getting features")

    return features

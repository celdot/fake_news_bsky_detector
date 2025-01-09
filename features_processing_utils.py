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
    
    dataset = {"post_uri": [],
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
    
    for query in tqdm(news["title"]):
        try:
            posts = search_posts(query, limit)
        except json.JSONDecodeError:
            pass
        try:
            posts_list = posts["posts"]
        except KeyError:
            posts_list = []
        for post in posts_list:
            try:
                dataset = get_post_info(dataset, post, news, query, IsQuery)
            except KeyError: 
                pass
                    
    dataframe = pd.DataFrame(dataset, columns=["post_uri", "post_cid", "type", "date", "news_id", "like_count", "repost_count", "user_name", "follower_count", "follows_count"])

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

def get_features(dataframe, label, query=False):
    dataframe["repost_count_1hour"] = 0
    dataframe["post_count_1hour"] = 0
    dataframe["average_repost"] = 0
    
    ### Group the dataframe by "news_id"
    news_df = dataframe.groupby("news_id")

    ### Create an empty DataFrame for features
    features_df = pd.DataFrame()
    features_df["news_id"] = news_df.groups.keys()

    ### Convert date columns to datetime
    dataframe["date"] = pd.to_datetime(dataframe["date"], format='ISO8601', utc=True)
    dataframe["retweet_date"] = pd.to_datetime(dataframe["retweet_date"], format='ISO8601', utc=True)
    
    ### Calculate time difference between a post and its reposts in seconds
    dataframe["time_difference"] = (dataframe["date"] - dataframe["retweet_date"]).dt.total_seconds()

    ### Calculate the average number of followers for usres in each group of news and merge with features_df
    average_followers = news_df["follower_count"].mean().reset_index()
    features_df = features_df.merge(average_followers, on="news_id", how="left")

    ### Calculate the average number of follows for users in in each group and merge with feature_df
    average_follows = news_df["follows_count"].mean().reset_index()
    features_df = features_df.merge(average_follows, on="news_id", how="left")
    
    ### Get the total number of reposts
    repost_total = dataframe[["repost_count", "news_id"]].groupby("news_id").sum().fillna(0).reset_index()
    features_df = features_df.merge(repost_total, on="news_id", how="left")
    
    # Rename columns for clarity
    features_df = features_df.rename(columns={"follower_count": "average followers",
                                "follows_count": "average follows",
                                "repost_count": "repost total"})
    features_df["repost total"] = features_df["repost total"].astype('int64')

    ### Get the total number of unique posts
    post_total = news_df["post_cid"].nunique().fillna(0).astype('int64')
    features_df = features_df.merge(post_total, on="news_id", how="left")
    features_df = features_df.rename(columns={"post_cid": "post total"})
    
    ### Calculate repost percentage
    features_df["repost percentage"] = features_df["repost total"] / (features_df["repost total"] + features_df["post total"])
    
    ### Handle labeling if `query` is not provided
    if not query:
        features_df["label"] = label  # 1 for fake news, 0 for real news

    ### Calculate average repost per news
    # Filter for reposts and calculate repost counts per post
    reposts = dataframe[dataframe["type"] == "repost"]
    repost_counts = reposts.groupby("post_cid")["repost_count"].sum().reset_index()
    repost_counts.rename(columns={"repost_count": "reposts_per_posts"}, inplace=True)

    # Merge repost counts back into the original dataframe
    repost_counts = dataframe.merge(repost_counts, on="post_cid", how="left")
    total_reposts_per_news = repost_counts.groupby("news_id")["reposts_per_posts"].sum()

    # Calculate the average repost per news
    average_repost = (total_reposts_per_news / (features_df.set_index("news_id")["repost total"] + features_df.set_index("news_id")["post total"])
                        ).fillna(0).reset_index()
    
    # Add name to the series
    average_repost.name = "average_repost"
    
    features_df = features_df.merge(average_repost, on="news_id", how="left")
    features_df = features_df.rename(columns={0: "average repost"})
    
    ### Calculate average favorites
    average_favorite = news_df["like_count"].mean()
    features_df = features_df.merge(average_favorite, on="news_id", how="left")
    
    ### Calculate news lifetime in seconds, which is the difference between the time of the first post and the last post
    news_lifetime = (news_df["date"].max() - news_df["date"].min()).dt.total_seconds()
    features_df = features_df.merge(news_lifetime, on="news_id", how="left")  
    
    # Rename columns for clarity
    features_df = features_df.rename(columns={"like_count": "average favorite",
                                              "date": "news lifetime"})
    
    ### Count number of users that posted or reposts within the first 10 hours
    nb_users_10_hours = news_df.apply(count_users_within_10_hours).fillna(1).astype('int64')
    nb_users_10_hours.name = "nb_users_10_hours"
    features_df = features_df.merge(nb_users_10_hours, on="news_id", how="left")
    features_df = features_df.rename(columns={"nb_users_10_hours": "nb users 10 hours"})
    
     ### Calculate average time difference
    average_time_difference = news_df["time_difference"].mean().fillna(0)
    features_df = features_df.merge(average_time_difference, on="news_id", how="left")
    features_df = features_df.rename(columns={"time_difference": "average time difference"})
    
    ### Calculate repost percentage within 1 hour
    # Apply the function to each group and reset the index
    counts_df = news_df.apply(calculate_repost_post_counts).reset_index(drop=True)

    # Merge repost and post counts into features_df
    features_df = pd.concat([features_df, counts_df[["repost_count_1hour", "post_count_1hour"]]], axis=1)

    features_df["retweet percentage 1 hour"] = (
        (features_df["repost_count_1hour"] + features_df["post_count_1hour"]) /
        (features_df["repost total"] + features_df["post total"])
    ).fillna(0)

    ### Drop unnecessary columns
    features_df = features_df.drop(columns=["repost_count_1hour", "post_count_1hour"])
                                                
    return features_df

def complete_processing(source, label, posts_name, feature_name, start=None, end=None):
    posts = create_dataset(source[start:end])
    posts.to_csv("data/" + posts_name, index=False)
    features = get_features(posts, label)
    features.to_csv("data/" + feature_name, index=False)
    
    return features

def process_query(query):
    posts = create_dataset(pd.DataFrame({"title": [query]}), 100, True)
    print("finished scraping posts")
    features = get_features(posts, None, True)
    print("finished getting features")
    
    return features

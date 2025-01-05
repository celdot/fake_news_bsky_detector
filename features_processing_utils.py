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
    response = requests.get(f"https://public.api.bsky.app/xrpc/app.bsky.feed.getReposts?uri={uri}&limit={limit}")
    data = response.json()
    return data

def get_feed(username, limit=100):
    response = requests.get(f"https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor={username}&limit={limit}")
    data = response.json()
    return data

def search_posts(query, limit=100):
    response = requests.get(f"https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?query={query}&limit={limit}")
    data = response.json()
    return data

def get_post_info(dataset, post, news, query):
    profile = get_profile(post["author"]["handle"])
    dataset["post_uri"].append(post["uri"])
    dataset["post_cid"].append(post["cid"])
    dataset["date"].append(post["record"]["createdAt"])
    dataset["news_id"].append(news[news["title"] == query]["id"].values[0])
    dataset["like_count"].append(post["likeCount"])
    dataset["repost_count"].append(post["repostCount"])
    dataset["user_name"].append(post["author"]["handle"])
    dataset["follower_count"].append(profile["followersCount"])
    dataset["follows_count"].append(profile["followsCount"])

def add_posts(news, limit=100):
    
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
        posts = search_posts(query, limit)
        try:
            posts_list = posts["posts"]
        except KeyError:
            posts_list = []
        for post in posts_list:
            try:
                get_post_info(dataset, post, news, query)
            except KeyError: 
                pass
                    
    dataframe = pd.DataFrame(dataset, columns=["post_uri", "post_cid", "type", "date", "news_id", "like_count", "repost_count", "user_name", "follower_count", "follows_count"])
            
    return dataframe

def get_repost_info(dataset, user, query, posts_dataset):
    profile = get_profile(user["handle"])
    
    dataset["post_uri"].append(posts_dataset[posts_dataset["post_uri"] == query]["post_uri"].values[0])
    dataset["post_cid"].append(posts_dataset[posts_dataset["post_uri"] == query]["post_cid"].values[0])
    dataset["retweet_date"].append(posts_dataset[posts_dataset["post_uri"] == query]["date"].values[0])
    dataset["news_id"].append(posts_dataset[posts_dataset["post_uri"] == query]["news_id"].values[0])
    dataset["like_count"].append(posts_dataset[posts_dataset["post_uri"] == query]["like_count"].values[0])
    dataset["repost_count"].append(posts_dataset[posts_dataset["post_uri"] == query]["repost_count"].values[0])
    dataset["user_name"].append(user["handle"])
    dataset["follower_count"].append(profile["followersCount"])
    dataset["follows_count"].append(profile["followsCount"])

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
        reposts = get_reposts(query, limit)
        try:
            reposts_list = reposts["repostedBy"]
        except KeyError:
            reposts_list = []
        for user in reposts_list:
            try:
                get_repost_info(dataset, user, query, posts_dataset)
            except KeyError: 
                pass
            
    dataframe = pd.DataFrame(dataset, columns=["post_uri", "post_cid", "type", "retweet_date", "news_id", "like_count", "repost_count", "user_name", "follower_count", "follows_count"])
            
    return dataframe

def create_dataset(news, limit=100):
    posts_dataset = add_posts(news, limit)
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
    
    return pd.Series({"repost_count": repost_count, "post_count": post_count})

def get_features(dataframe, label, query=False):
    news_df = dataframe.groupby("news_id")
    
    features_df = pd.DataFrame()
    
    dataframe["date"] = pd.to_datetime(dataframe["date"], format='ISO8601', utc=True)
    dataframe["retweet_date"] = pd.to_datetime(dataframe["retweet_date"], format='ISO8601', utc=True)
    
    dataframe["time_difference"] = (dataframe["date"] - dataframe["retweet_date"]).dt.seconds
    
    features_df["average followers"] = news_df["follower_count"].mean()
    features_df["average follows"] = news_df["follows_count"].mean()

    features_df["repost total"] = news_df["repost_count"].sum().fillna(0).astype(int)
    
    features_df["post total"] = news_df["type"].value_counts().unstack()["post"].fillna(0).astype(int)
    features_df["repost percentage"] = features_df["repost total"] / (features_df["repost total"] + features_df["post total"])

    reposts = dataframe[dataframe["type"] == "repost"]

    repost_counts = reposts.groupby("post_cid")["repost_count"].sum().reset_index()
    repost_counts.rename(columns={"repost_count": "reposts_per_posts"}, inplace=True)

    repost_counts = dataframe.merge(repost_counts, on="post_cid", how="left")

    features_df["average repost"] = (repost_counts.groupby("news_id")["reposts_per_posts"].sum() / \
                                (features_df["repost total"] + features_df["post total"])).fillna(0)
                                                
    features_df["average favorite"] = news_df["like_count"].mean()
    if not query:
        features_df["label"] = label # 0 for fake news, 1 for real news
        
    features_df["news lifetime"] = (news_df["date"].max() \
                                    - news_df["date"].min()).dt.seconds
    
    features_df["nb users 10 hours"] = news_df.apply(count_users_within_10_hours).fillna(1).astype(int)

    features_df["average time difference"] = news_df["time_difference"].mean().fillna(0)
    
    # Step 3: Apply the function to each group
    counts_df = news_df.apply(calculate_repost_post_counts).reset_index()

    # Step 4: Merge repost and post counts into features_df
    features_df = features_df.merge(counts_df, on="news_id", how="left").fillna(0)

    # Step 5: Calculate retweet percentage for 1 hour
    features_df["retweet percentage 1 hour"] = (
        (features_df["repost_count"] + features_df["post_count"]) /
        (features_df["repost total"] + features_df["post total"])
        ).fillna(0)
    
    features_df = features_df.drop(columns=["repost_count", "post_count"])
                                                
    return features_df

def complete_processing(source, label, posts_name, feature_name, start=None, end=None):
    posts = create_dataset(source[start:end])
    posts.to_csv("data/" + posts_name, index=False)
    features = get_features(posts, label)
    features.to_csv("data/" + feature_name, index=False)
    
    return features

def process_query(query):
    posts = create_dataset(pd.DataFrame({"title": [query]}))
    features = get_features(posts, None, True)
    
    return features

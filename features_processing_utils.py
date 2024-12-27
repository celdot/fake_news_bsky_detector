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
    response = requests.get("https://public.api.bsky.app/xrpc/app.bsky.feed.getRepostedBy?uri=" + uri + "&limit=" + str(limit))
    data = response.json()
    return data

def get_feed(username, limit=100):
    response = requests.get("https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=" + username + "&limit=" + str(limit))
    data = response.json()
    return data

def search_posts(query, limit=100):
    response = requests.get("https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=" + query + "&limit=" + str(limit))
    data = response.json()
    return data

def create_dataset(news, limit=100):
    
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
        for post in posts["posts"]:
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
            
    dataframe = pd.DataFrame(dataset, columns=["post_uri", "post_cid", "type", "date", "news_id", "like_count", "repost_count", "user_name", "follower_count", "follows_count"])
            
    return dataframe

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
        for user in reposts["repostedBy"]:
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
            
    dataframe = pd.DataFrame(dataset, columns=["post_uri", "post_cid", "type", "retweet_date", "news_id", "like_count", "repost_count", "user_name", "follower_count", "follows_count"])
            
    return dataframe


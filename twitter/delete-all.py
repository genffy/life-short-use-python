import os
import time
import tweepy
from dotenv import load_dotenv

load_dotenv()

# Authenticate with your Twitter Developer API credentials
consumer_key = os.getenv("X_CONSUMER_KEY")
consumer_secret = os.getenv("X_CONSUMER_SECRET")
access_token = os.getenv("X_ACCESS_TOKEN")
access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
bearer_token = os.getenv("X_BEARER_TOKEN")

# Create client for v2 API with proper OAuth 1.0a authentication
client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
    bearer_token=bearer_token,
    wait_on_rate_limit=True
)

# Also create OAuth 1.0a auth handler for v1.1 API (for some operations)
auth = tweepy.OAuth1UserHandler(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)
api = tweepy.API(auth)

# Get user ID (needed for v2 endpoints)
me = client.get_me()
user_id = me.data.id
print(f"User ID: {user_id}")

# Function to delete tweets
def delete_tweets(max_count=1000):
    deleted_count = 0
    print(f"Deleting up to {max_count} tweets...")
    
    try:
        # Use v1.1 API for getting timeline
        for status in tweepy.Cursor(api.user_timeline, count=200, tweet_mode="extended").items(max_count):
            try:
                # Use v2 API for deleting
                client.delete_tweet(id=status.id)
                print(f"Deleted tweet: {status.id}")
                deleted_count += 1
                # Add slight delay to avoid rate limits
                time.sleep(0.5)
            except Exception as e:
                print(f"Error deleting tweet {status.id}: {e}")
    except Exception as e:
        print(f"Error fetching tweets: {e}")
    
    print(f"Deleted {deleted_count} tweets.")

# Function to unlike tweets
def unlike_tweets(max_count=1000):
    unliked_count = 0
    print(f"Unliking up to {max_count} liked tweets...")
    
    try:
        # Use v1.1 API for getting favorites
        for status in tweepy.Cursor(api.get_favorites, count=200, tweet_mode="extended").items(max_count):
            try:
                # Use v1.1 API for unliking
                api.destroy_favorite(status.id)
                print(f"Unliked tweet: {status.id}")
                unliked_count += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"Error unliking tweet {status.id}: {e}")
    except Exception as e:
        print(f"Error fetching likes: {e}")
    
    print(f"Unliked {unliked_count} tweets.")

# Main execution
if __name__ == "__main__":
    # Ask for confirmation
    confirm = input("This will delete all your tweets, likes, retweets, and comments. Continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        exit()
    
    # Delete tweets (which includes retweets)
    delete_tweets()
    
    # Unlike liked tweets
    unlike_tweets()
    
    print("Operation completed.")
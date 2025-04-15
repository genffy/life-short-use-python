# twitter
## twspace_dl

```shell
python3 -m pip install twspace-dl
twspace_dl -i https://x.com/i/spaces/1mnGeAXAmYbGX/peek -c ./cookie.txt
```

## Delete All X (Twitter) Content

The `delete-all.py` script allows you to delete all your tweets, likes, retweets, and comments using the Twitter API v2 with Tweepy 4.15.0.

### Setup

1. Make sure you have the required packages:
   ```shell
   pip install tweepy==4.15.0 python-dotenv
   ```

2. Set up a Twitter developer account and create an app at [developer.twitter.com](https://developer.twitter.com)

3. Copy the `.env.example` file to `.env` and fill in your API credentials:
   ```shell
   cp .env.example .env
   ```

4. Edit the `.env` file with your API credentials:
   ```
   X_CONSUMER_KEY=your_consumer_key_here
   X_CONSUMER_SECRET=your_consumer_secret_here
   X_ACCESS_TOKEN=your_access_token_here
   X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
   ```

### Usage

Run the script:
```shell
python delete-all.py
```

The script will:
1. Ask for confirmation before proceeding
2. Delete all your tweets (including retweets)
3. Unlike all tweets you have liked

Note: Due to Twitter API rate limits, the process may take time for accounts with many tweets/likes.

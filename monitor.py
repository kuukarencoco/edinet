import requests
import datetime
import tweepy
import os

# 認証情報
X_CLIENT = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)
EDINET_API_KEY = os.environ["EDINET_API_KEY"]
LOG_FILE = "posted_ids.txt"

def get_all_listings():
    today = datetime.date.today().strftime("%Y-%m-%d")
    url = "https://api.edinet-fsa.go.jp/api/v2/documents.json"
    params = {
        "date": today,
        "type": 2,
        "Subscription-Key": EDINET_API_KEY
    }
    
    try:
        res = requests.get(url, params=params, timeout=30)
        if res.status_code != 200:
            return []
        data = res.json()
    except:
        return []

    targets = []
    posted_ids = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            posted_ids = f.read().splitlines()

    if "results" in data:
        for doc in data["results"]:
            doc_id = doc.get("docID")
            if doc_id and doc_id not in posted_ids:
                targets.append(doc)
    return targets

def main():
    targets = get_all_listings()
    if not targets:
        print("新規書類なし")
        return

    for doc in targets:
        doc_id = doc['docID']
        filer_name = doc.get('filerName', '名称不明')
        doc_description = doc.get('docDescription', '書類')
        
        # 【重要】タイトルを最大80文字で構成
        # 「発行体名」＋「：」＋「書類内容」の順で繋げます
        display_text = f"{filer_name}：{doc_description}"
        
        # 80文字を超える場合はカットして「..」を付与
        if len(display_text) > 80:
            clean_title = display_text[:77] + ".."
        else:
            clean_title = display_text
        
        view_url = f"https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx?SBN=H&ID={doc_id}"
        
        # ツイート本文（タイトル80文字 + URL）
        message = f"{clean_title}\n{view_url}"
        
        try:
            X_CLIENT.create_tweet(text=message)
            with open(LOG_FILE, "a") as f:
                f.write(doc_id + "\n")
            print(f"投稿成功: {doc_id}")
        except Exception as e:
            print(f"投稿エラー: {e}")

if __name__ == "__main__":
    main()

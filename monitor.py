import requests
import datetime
import tweepy
import os

X_CLIENT = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)
EDINET_API_KEY = os.environ["EDINET_API_KEY"]
LOG_FILE = "posted_ids.txt"

def get_st_listings():
    today = datetime.date.today().strftime("%Y-%m-%d")
    url = "https://disclosure.edinet-fsa.go.jp/api/v1/documents.json"
    params = {"date": today, "type": 2, "Subscription-Key": EDINET_API_KEY}
    
    res = requests.get(url, params=params)
    
    # --- エラー原因を特定するためのログ機能 ---
    if res.status_code != 200:
        print(f"EDINETエラー: ステータスコード {res.status_code}")
        return []
    
    try:
        data = res.json()
    except Exception as e:
        print("【原因】EDINETからデータではない応答が返りました。")
        print(f"レスポンスの先頭: {res.text[:100]}") # 最初の100文字を表示
        return []
    # ------------------------------------

    targets = []
    posted_ids = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            posted_ids = f.read().splitlines()

    if "results" in data:
        for doc in data["results"]:
            if doc.get("docTypeCode") == "030000" and "訂正" not in doc.get("docDescription", ""):
                doc_id = doc.get("docID")
                if doc_id not in posted_ids:
                    desc = doc.get("docDescription", "")
                    if "トークン" in desc or "内国信託受益証券" in desc:
                        targets.append(doc)
    return targets

def main():
    targets = get_st_listings()
    if not targets:
        print(f"{datetime.datetime.now()}: 有効な銘柄なし")
        return

    for doc in targets:
        doc_id = doc['docID']
        url = f"https://disclosure.edinet-fsa.go.jp/api/v1/documents/{doc_id}"
        message = (
            f"【新規公開】セキュリティトークンの有価証券届出書が提出されました。\n\n"
            f"発行体：{doc['filerName']}\n"
            f"書類名：{doc['docDescription']}\n\n"
            f"詳細(EDINET)：{url}\n"
            f"#ST #デジタル証券 #セキュリティトークン"
        )
        try:
            X_CLIENT.create_tweet(text=message)
            with open(LOG_FILE, "a") as f:
                f.write(doc_id + "\n")
            print(f"投稿成功: {doc_id}")
        except Exception as e:
            print(f"投稿エラー: {e}")

if __name__ == "__main__":
    main()

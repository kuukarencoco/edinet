import requests
import datetime
import tweepy
import os

# 認証情報（GitHub Secretsから取得）
X_CLIENT = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"]
)
EDINET_API_KEY = os.environ["EDINET_API_KEY"]
LOG_FILE = "posted_ids.txt"

def get_st_listings():
    # 仕様書に従い、今日の日付を取得
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # 【重要】エンドポイントを v2 に修正
    url = "https://api.edinet-fsa.go.jp/api/v2/documents.json"
    
    # 【重要】仕様書の規定通り、type=2 と Subscription-Key をセット
    params = {
        "date": today,
        "type": 2,
        "Subscription-Key": EDINET_API_KEY
    }
    
    try:
        # タイムアウトを設定し、エラーハンドリングを強化
        res = requests.get(url, params=params, timeout=30)
        
        if res.status_code != 200:
            print(f"EDINETエラー: ステータスコード {res.status_code}")
            # 403が出る場合、ここでレスポンス内容を表示して原因を特定
            print(f"詳細: {res.text}")
            return []
            
        data = res.json()
    except Exception as e:
        print(f"接続または解析エラー: {e}")
        return []

    targets = []
    posted_ids = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            posted_ids = f.read().splitlines()

    # 書類一覧からST関連を抽出
    if "results" in data:
        for doc in data["results"]:
            # docTypeCode "030000" = 有価証券届出書
            if doc.get("docTypeCode") == "030000" and "訂正" not in (doc.get("docDescription") or ""):
                doc_id = doc.get("docID")
                if doc_id not in posted_ids:
                    desc = doc.get("docDescription") or ""
                    # キーワード判定
                    if "トークン" in desc or "内国信託受益証券" in desc:
                        targets.append(doc)
    return targets

def main():
    targets = get_st_listings()
    if not targets:
        print(f"{datetime.datetime.now()}: 新規の対象銘柄はありませんでした")
        return

    for doc in targets:
        doc_id = doc['docID']
        # 書類閲覧URLの構築
        view_url = f"https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx?SBN=H&ID={doc_id}"
        
        message = (
            f"【新規公開】セキュリティトークンの有価証券届出書が提出されました。\n\n"
            f"発行体：{doc['filerName']}\n"
            f"書類名：{doc['docDescription']}\n\n"
            f"詳細(EDINET)：{view_url}\n"
            f"#ST #デジタル証券 #セキュリティトークン"
        )
        try:
            X_CLIENT.create_tweet(text=message)
            with open(LOG_FILE, "a") as f:
                f.write(doc_id + "\n")
            print(f"投稿成功: {doc_id}")
        except Exception as e:
            print(f"X投稿エラー: {e}")

if __name__ == "__main__":
    main()

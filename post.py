"""
AI人生ステータス診断 — X投稿スクリプト
名前を入力するとステータスを生成してXに投稿する
"""

import tweepy
from datetime import datetime

# ============================================================
# X API 認証情報（@AILifeStatus アカウントのキーを設定）
# ============================================================
X_API_KEY             = "YOUR_API_KEY"
X_API_SECRET          = "YOUR_API_SECRET"
X_ACCESS_TOKEN        = "YOUR_ACCESS_TOKEN"
X_ACCESS_TOKEN_SECRET = "YOUR_ACCESS_TOKEN_SECRET"

SITE = "https://ai-life-status.vercel.app"

# ============================================================
# データ（index.html と完全同期）
# ============================================================
JOBS = ["伝説の社畜","深夜のコンビニ賢者","布団の守護神","カフェイン魔術師","散財の錬金術師","孤高のソロキャンパー","妄想の建築家","通知の奴隷","AI魔法剣士","深夜ラーメン背徳者","ドライブの哲学者","推し活の聖女","副業沼の冒険者","永遠の計画マン","カフェ巡りの魔女","ストーリーズの女神","コスメ錬金術師","積ん読の大賢者","昼寝の大魔王","サブスク放置の貴族","推しの騎士","深夜アニメの求道者","Google検索の勇者","タピオカの巫女","Zoom疲れの勇者","TikTok沼の住人","推し活破産者","深夜Xの亡者","週末シェフ見習い","寝落ち配信の伴走者","ガジェット沼の住人","名言コレクターの賢者"]
MOVES = ["無限先延ばし","深夜のひらめき","課金カタルシス","布団バリア","焚き火ヒーリング","ググり連撃","推しパワー全開","SNS読心術","サブスク忘却","積ん読の知恵","カフェイン三連","二度寝の覇道","ドライブ瞑想","Amazonワンクリック","エナドリ三連星","映えショット"]
WKS  = ["月曜朝: 全ステ-50%（解呪不可）","「あと5分」→30分バグ","セールで課金暴走","深夜SNSでやる気リーク","布団引力への耐性ゼロ","他人の成功でHP微減","「明日やろう」自動発動","推し供給途切れでやる気消滅"]
QTS  = ["散財力、もはや才能。","孤独耐性の高さは最強の証。","やる気の使い所を選んでるだけ。","布団が強すぎる。お前は悪くない。","お前はお前のRPGを生きろ。","運は行動の蓄積。"]
ST   = [
    {"n": "💪体力",    "k": "hp"},
    {"n": "🧠知力",    "k": "int"},
    {"n": "💰金運",    "k": "pay"},
    {"n": "😎孤独耐性", "k": "solo"},
    {"n": "🔥やる気",  "k": "mot"},
    {"n": "🍀運",      "k": "luk"},
]

# ============================================================
# JS互換のハッシュ関数・乱数生成器
# ============================================================
def to_int32(n):
    n = n & 0xFFFFFFFF
    if n >= 0x80000000:
        n -= 0x100000000
    return n

def js_hash(s):
    h = 0
    for c in s:
        h = to_int32(to_int32(h << 5) - h + ord(c))
    return abs(h)

def make_rng(seed):
    s = [seed]
    def rng():
        s[0] = (s[0] * 16807) % 2147483647
        return (s[0] - 1) / 2147483646
    return rng

# ============================================================
# ステータス生成（JS の gen() と同じロジック）
# ============================================================
def gen(name):
    date_str = datetime.now().strftime("%a %b %d %Y")  # JS: new Date().toDateString()
    seed = js_hash(name + date_str)
    r = make_rng(seed)

    job   = JOBS[int(r() * len(JOBS))]
    _     = r()  # trait
    move  = MOVES[int(r() * len(MOVES))]
    wk    = WKS[int(r() * len(WKS))]
    _     = r()  # qt

    sv = {}
    total = 0
    for s in ST:
        v = int(r() * 800) + 100
        if r() > 0.55: v = int(r() * 400) + 800
        if r() > 0.82: v = int(r() * 30) + 1
        if r() > 0.97: v = -1
        if r() > 0.993: v = int(r() * 9000) + 1000
        sv[s["k"]] = v
        total += v if v > 0 else 500

    lv = min(99, max(1, int(total / 80)))

    return {"name": name, "job": job, "move": move, "wk": wk, "lv": lv, "sv": sv}

# ============================================================
# ツイートテキスト生成
# ============================================================
def build_tweet(d):
    mx_name, mx_val = "", 0
    for s in ST:
        v = d["sv"][s["k"]]
        if v > mx_val:
            mx_name, mx_val = s["n"], v
    mx_disp = "???" if mx_val < 0 else f"{mx_val:,}"

    return (
        f"⚔️ギルド登録結果\n\n"
        f"{d['name']}\n\n"
        f"ジョブ：{d['job']}（Lv.{d['lv']}）\n"
        f"必殺技：「{d['move']}」\n"
        f"弱点：「{d['wk']}」\n"
        f"最強ステ：{mx_name}{mx_disp}\n\n"
        f"あなたのジョブは？⚔️\n"
        f"{SITE}\n"
        f"#AI人生ステータス #診断 #やってみて"
    )

# ============================================================
# X投稿
# ============================================================
def post_to_x(text):
    client = tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET,
    )
    response = client.create_tweet(text=text)
    return response.data["id"]

# ============================================================
# メイン
# ============================================================
def main():
    name = input("冒険者の名前を入力: ").strip()
    if not name:
        print("名前が空です")
        return

    d = gen(name)
    tweet = build_tweet(d)

    print("\n--- 投稿内容 ---")
    print(tweet)
    print(f"---------------\n文字数: {len(tweet)}")

    confirm = input("\nこの内容でXに投稿しますか？ (y/n): ")
    if confirm.lower() != "y":
        print("キャンセルしました")
        return

    tweet_id = post_to_x(tweet)
    print(f"✅ 投稿完了: https://x.com/i/web/status/{tweet_id}")

if __name__ == "__main__":
    main()

"""
@AILifeStatus トレンド投稿ネタ自動収集＆生成ツール
実行: python tools/trend_post_generator.py  (プロジェクトルートから)
"""
import re, sys, math, random, urllib.request, ctypes
import html as html_module
from datetime import datetime
import xml.etree.ElementTree as ET
from pathlib import Path

# tools/ ディレクトリ自身をパスに追加（config.py 読み込み用）
sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")

try:
    from config import ANTHROPIC_API_KEY
except ImportError:
    ANTHROPIC_API_KEY = ""

SITE_URL  = "ai-life-status.vercel.app"
HASHTAGS  = "#AI人生ステータス"
_today = datetime.now().strftime("%Y-%m-%d")
OUTPUT_HTML = str(Path(__file__).parent.parent / "posts" / f"{_today}.html")
OPUS_MODEL  = "claude-opus-4-6"

# ============================================================
# 決定論的RNG — index.html の hash()/sr()/gen() を完全再現
# 同じ名前＋同じ日付 → アプリと同じ診断結果を返す
# ============================================================
_DIAG_JOBS = ["伝説の社畜","深夜のコンビニ賢者","布団の守護神","カフェイン魔術師","散財の錬金術師","孤高のソロキャンパー","妄想の建築家","通知の奴隷","AI魔法剣士","深夜ラーメン背徳者","ドライブの哲学者","推し活の聖女","副業沼の冒険者","永遠の計画マン","カフェ巡りの魔女","ストーリーズの女神","コスメ錬金術師","積ん読の大賢者","昼寝の大魔王","サブスク放置の貴族","推しの騎士","深夜アニメの求道者","Google検索の勇者","タピオカの巫女","Zoom疲れの勇者","TikTok沼の住人","推し活破産者","深夜Xの亡者","週末シェフ見習い","寝落ち配信の伴走者","ガジェット沼の住人","名言コレクターの賢者"]
_DIAG_TRAITS = ["朝弱い","考えすぎ","衝動的","マイペース","完璧主義","楽観的","夜型","行動派","感覚派","直感型"]
_DIAG_MOVES  = ["無限先延ばし","深夜のひらめき","課金カタルシス","布団バリア","焚き火ヒーリング","ググり連撃","推しパワー全開","SNS読心術","サブスク忘却","積ん読の知恵","カフェイン三連","二度寝の覇道","ドライブ瞑想","Amazonワンクリック","エナドリ三連星","映えショット"]
_DIAG_WKS    = ["月曜朝: 全ステ-50%（解呪不可）","「あと5分」→30分バグ","セールで課金暴走","深夜SNSでやる気リーク","布団引力への耐性ゼロ","他人の成功でHP微減","「明日やろう」自動発動","推し供給途切れでやる気消滅"]
_DIAG_QTS    = ["散財力、もはや才能。","孤独耐性の高さは最強の証。","やる気の使い所を選んでるだけ。","布団が強すぎる。お前は悪くない。","お前はお前のRPGを生きろ。","運は行動の蓄積。"]
_DIAG_ST     = [("💪体力","hp"),("🧠知力","int"),("💰金運","pay"),("😎孤独耐性","solo"),("🔥やる気","mot"),("🍀運","luk")]
_DIAG_TITLES = ['見習い','一般','熟練','精鋭','達人','伝説','神話']

def _js_hash(s: str) -> int:
    """djb2 variant: matches index.html hash()"""
    h = 0
    for ch in s:
        h = ((h << 5) - h) + ord(ch)
        h = ctypes.c_int32(h).value  # h|=0
    return abs(h)

def _js_rng(seed: int):
    """Park-Miller PRNG: matches index.html sr()"""
    s = [seed]
    def _next():
        s[0] = (s[0] * 16807) % 2147483647
        return (s[0] - 1) / 2147483646
    return _next

def _js_date_str(dt=None) -> str:
    """JS Date.toDateString() format: 'Wed Mar 18 2026'"""
    if dt is None:
        dt = datetime.now()
    _days   = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
    _months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    js_day  = (dt.weekday() + 1) % 7  # Python Mon=0...Sun=6 → JS Sun=0...Sat=6
    return f"{_days[js_day]} {_months[dt.month-1]} {dt.day} {dt.year}"

def diagnose(name: str, dt=None, pow_mul: float = 1.0) -> dict:
    """
    index.html の gen() を Node.js 経由で実行 → アプリと完全一致保証。
    Node.js が使えない場合は Python 実装にフォールバック。
    """
    import subprocess, json as _json
    date_arg = dt.strftime("%Y-%m-%d") if dt else None
    cmd = ["node", str(Path(__file__).parent / "diagnose.js"), name]
    if date_arg:
        cmd.append(date_arg)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                           cwd=str(Path(__file__).parent.parent), timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return _json.loads(r.stdout)
        raise RuntimeError(r.stderr.strip())
    except Exception as e:
        # フォールバック: Python 実装
        print(f"  ⚠️ Node.js 失敗 ({e})、Python実装で代替")
        return _diagnose_python(name, dt, pow_mul)

def _diagnose_python(name: str, dt=None, pow_mul: float = 1.0) -> dict:
    """Python 実装フォールバック（Node.js 不可時のみ使用）"""
    seed = _js_hash(name + _js_date_str(dt))
    r    = _js_rng(seed)

    ji = int(r() * len(_DIAG_JOBS))
    _  = int(r() * len(_DIAG_TRAITS))
    mi = int(r() * len(_DIAG_MOVES))
    wi = int(r() * len(_DIAG_WKS))
    _  = int(r() * len(_DIAG_QTS))

    sv, total = {}, 0
    for icon, k in _DIAG_ST:
        v = int(r() * 800) + 100
        if r() > 0.55: v = int(r() * 400) + 800
        if r() > 0.82: v = int(r() * 30) + 1
        if r() > 0.97: v = -1
        if r() > 0.993: v = int(r() * 9000) + 1000
        v = round(v * pow_mul)
        sv[k] = {"icon": icon, "value": v}
        total += v if v > 0 else 500

    lv = min(99, max(1, total // 80))
    ti = 0 if total<1500 else 1 if total<2000 else 2 if total<2800 else 3 if total<3600 else 4 if total<4500 else 5 if total<6000 else 6
    return {
        "name": name, "job": _DIAG_JOBS[ji], "move": _DIAG_MOVES[mi],
        "weakness": _DIAG_WKS[wi], "sv": sv, "level": lv,
        "title": _DIAG_TITLES[ti], "total": total,
    }

# ============================================================
# 文字数カウント（X方式）
# ============================================================
def x_char_count(text):
    url_re = re.compile(r"https?://\S+")
    bare = SITE_URL
    urls = url_re.findall(text)
    text2 = url_re.sub("", text)
    cnt = len(urls) * 23
    for ch in text2:
        cnt += 1 if ord(ch) <= 0xFF else 2
    n = text.count(bare)
    raw = sum(1 if ord(c) <= 0xFF else 2 for c in bare)
    return cnt - n * raw + n * 23

def char_display(text):
    return math.ceil(x_char_count(text) / 2)

def _name_to_hashtag(name: str) -> str:
    """名前/グループ名をXで有効なハッシュタグ文字列に変換"""
    # スペース・中黒・記号を除去または_に変換
    tag = re.sub(r'[\s・\-]', '_', name)
    tag = re.sub(r'[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', tag)
    return tag

def check_post(text):
    cnt = x_char_count(text)
    return cnt, math.ceil(cnt / 2), cnt <= 280

# ============================================================
# フェッチ
# ============================================================
def fetch(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ja-JP,ja;q=0.9"
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""

# ============================================================
# トレンド取得
# ============================================================
def get_rss_headlines(url, max_items=12):
    raw = fetch(url)
    if not raw:
        return []
    try:
        root = ET.fromstring(raw)
        # Atom (<entry>) と RSS (<item>) の両方に対応
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//atom:entry", ns) or root.findall(".//item")
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        titles = []
        for item in items[:max_items]:
            # Atom: <title> または RSS: <title>
            t = (item.findtext("{http://www.w3.org/2005/Atom}title")
                 or item.findtext("title", ""))
            t = html_module.unescape(t).strip()
            if t:
                titles.append(t)
        return titles
    except Exception:
        titles = re.findall(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", raw)
        return [html_module.unescape(t.strip()) for t in titles[2:max_items+2] if t.strip()]

def get_google_trends():
    """Google Trends Japan（RSS）"""
    raw = fetch("https://trends.google.com/trending/rss?geo=JP")
    if not raw:
        return []
    try:
        root = ET.fromstring(raw)
        ns = {"ht": "https://trends.google.com/trending/rss"}
        items = root.findall(".//item")
        result = []
        for item in items[:15]:
            title   = item.findtext("title", "")
            traffic = item.findtext("ht:approx_traffic", "", ns)
            if title:
                result.append((title, traffic))
        return result
    except Exception:
        return []

def get_x_trends(max_items=30):
    """
    trends24.in/japan/ からXのJapanトレンドを取得
    戻り値: [(name, rank), ...]  rank=1が最上位
    """
    raw = fetch('https://trends24.in/japan/')
    if not raw:
        return []
    try:
        # 最初の<ol>が最新トレンドリスト
        m = re.search(r'<ol[^>]*>(.*?)</ol>', raw, re.DOTALL)
        if not m:
            return []
        items = re.findall(r'<a[^>]*>([^<]+)</a>', m.group(1))
        return [(item.strip(), rank) for rank, item in enumerate(items[:max_items], 1) if item.strip()]
    except Exception:
        return []

def get_natalie_trends():
    """音楽/アニメ/エンタメ ナタリー（Z世代向け）"""
    feeds = {
        "音楽ナタリー" : "https://natalie.mu/music/feed/news",
        "アニメナタリー": "https://natalie.mu/comic/feed/news",
        "ナタリー"     : "https://natalie.mu/pop/feed/news",
    }
    result = {}
    for label, url in feeds.items():
        result[label] = get_rss_headlines(url, max_items=10)
    return result

def get_all_trends():
    sources = {
        "エンタメ": get_rss_headlines("https://news.yahoo.co.jp/rss/topics/entertainment.xml"),
        "スポーツ": get_rss_headlines("https://news.yahoo.co.jp/rss/topics/sports.xml"),
        "トップ"  : get_rss_headlines("https://news.yahoo.co.jp/rss/topics/top-picks.xml"),
    }
    sources.update(get_natalie_trends())
    google = get_google_trends()
    x_trends = get_x_trends()
    return sources, google, x_trends

# ============================================================
# 人名抽出
# ============================================================
SKIP_WORDS = {
    "速報","更新","一覧","ランキング","ニュース","アクセス","トピックス",
    "まとめ","続報","詳細","関連","騒然","快進撃","巨人","侍","決勝",
    "準決勝","敗退","惜敗","漫画原作","深夜食堂","公示地価","辺野古",
    "ぺんてる","フジテレビ","華大さん","千鳥くん","未来のムスコ",
}

# ============================================================
# Z世代向け固定ネタプール
# トレンドにA評価候補が少ない日に補充する「いつでも使えるネタ」
# 実績値がアプリと一致するので投稿クオリティも安定
# ============================================================
FIXED_Z_POOL = [
    # ── MLB・現役スポーツ ──────────────────────
    ("大谷翔平",   "ドジャース 圧倒的Z世代人気"),
    ("佐々木朗希", "メッツ 若きエース"),
    ("山本由伸",   "ドジャース 速球王"),
    ("鈴木誠也",   "カブス 日本人MLB"),
    ("今永昇太",   "カブス 奪三振マシン"),
    ("藤浪晋太郎", "MLB挑戦中 浪速のノーラン"),
    # ── 国内スポーツ ──────────────────────────
    ("藤井聡太",   "将棋八冠 天才"),
    ("久保建英",   "レアル・ソシエダ サッカー"),
    ("堂安律",     "フライブルク サッカー"),
    ("古橋亨梧",   "セルティック サッカー"),
    ("高梨沙羅",   "スキージャンプ"),
    ("高木美帆",   "スピードスケート"),
    # ── 若手俳優・女優 ─────────────────────────
    ("浜辺美波",   "女優 Z世代人気"),
    ("橋本環奈",   "女優 天使"),
    ("永野芽郁",   "女優 朝ドラ"),
    ("上白石萌音", "女優・歌手"),
    ("森七菜",     "女優"),
    ("吉岡里帆",   "女優"),
    ("今田美桜",   "女優 博多美人"),
    ("松村北斗",   "SixTONES"),
    ("目黒蓮",     "Snow Man Z世代人気"),
    ("道枝駿佑",   "なにわ男子"),
    ("西畑大吾",   "なにわ男子"),
    ("向井康二",   "Snow Man"),
    # ── 現役アイドル ──────────────────────────
    ("山下美月",   "乃木坂46"),
    ("遠藤さくら", "乃木坂46"),
    ("齋藤飛鳥",   "乃木坂46"),
    ("小坂菜緒",   "日向坂46"),
    ("河田陽菜",   "日向坂46"),
    ("松田好花",   "日向坂46"),
    ("岡田奈々",   "AKB48"),
    ("柏木由紀",   "AKB48"),
    ("田中美久",   "HKT48"),
    ("矢吹奈子",   "HKT48"),
    # ── ミュージシャン・アーティスト ───────────────
    ("Ado",        "歌手 Z世代圧倒的人気"),
    ("藤井風",     "ミュージシャン"),
    ("米津玄師",   "ミュージシャン"),
    ("King Gnu",   "バンド Z世代人気"),
    ("YOASOBI",    "ユニット Z世代"),
    ("Official髭男dism", "バンド ヒゲダン"),
    ("Eve",        "歌手 アニソン"),
    ("緑黄色社会", "バンド"),
    ("あいみょん",  "シンガーソングライター"),
    ("Vaundy",     "ミュージシャン Z世代"),
    # ── YouTube・VTuber ───────────────────────
    ("ヒカキン",   "YouTuber 国民的"),
    ("東海オンエア", "YouTuber"),
    ("フィッシャーズ", "YouTuber"),
    ("にじさんじ",  "VTuber事務所"),
    ("ホロライブ",  "VTuber事務所"),
]

# ============================================================
# ターゲット適合度スコアリング（10-30代向け）
# ============================================================
# 若年層シグナル → スコア +
_YOUNG_KW = [
    # 現役アイドル・K-POP
    "AKB","乃木坂","日向坂","SKE","HKT","NMB","STU","BTS","BLACKPINK","NewJeans",
    "Snow Man","SixTONES","Travis Japan","なにわ男子","King & Prince",
    # 若手アーティスト
    "YOASOBI","Ado","米津","藤井風","King Gnu","Vaundy","ずっと真夜中",
    # 現役プロスポーツ（人気高い）
    "ドジャース","ヤンキース","メッツ","エンゼルス","WBC",
    "DeNA","ヤクルト","阪神","ソフトバンク","日ハム","楽天",
    "代表","五輪","世界選手権",
    # SNS・ゲーム・配信
    "TikTok","YouTube","配信","ゲーム","VTuber","Vtuber","ストリーマー",
    # 若手俳優・女優
    "朝ドラ","NHK朝","モデル",
]
# 中高年寄りシグナル → スコア -
_OLD_KW = [
    "OB","元監督","評論家","解説者","元プロ","元アイドル","元タレント",
    "バラエティ","スタジオ","朝の情報","ワイドショー","再婚","離婚調停",
    "2世タレント","議員","政治家","大臣","知事",
]

def _target_score(name: str, headline: str) -> tuple[str, str]:
    """
    10-30代ターゲット適合度を A/B/C で返す。
    A: 若年層向け  B: 幅広い  C: ターゲット外気味
    戻り値: (grade, reason)
    """
    text = name + headline
    for kw in _YOUNG_KW:
        if kw in text:
            return "A", kw
    for kw in _OLD_KW:
        if kw in text:
            return "C", kw
    return "B", "—"

def extract_names(headlines_dict, google_trends, x_trends=None):
    candidates = []
    seen = set()

    # Xトレンドから（最もリアルタイム性高い）
    for name, rank in (x_trends or []):
        name = name.strip().lstrip('#')
        if name and name not in SKIP_WORDS and name not in seen and len(name) >= 2:
            candidates.append((name, f"Xトレンド {rank}位"))
            seen.add(name)

    # Google Trendsから
    for name, traffic in google_trends:
        name = name.strip()
        if name and name not in SKIP_WORDS and name not in seen and len(name) >= 2:
            candidates.append((name, f"Googleトレンド {traffic}検索"))
            seen.add(name)

    # Yahoo RSSから
    for label, headlines in headlines_dict.items():
        for h in headlines:
            m = re.match(r"^([ァ-ヶー]{2,8}|[一-龥]{2,5}[ぁ-ん]{0,2}[一-龥]{0,3})\s", h)
            if m:
                name = re.sub(r"(さん|氏|選手|アナ|容疑者|監督|コーチ)$", "", m.group(1).strip())
                if name and name not in SKIP_WORDS and name not in seen and len(name) >= 2:
                    candidates.append((name, h))
                    seen.add(name)
                    continue
            m2 = re.search(r"[・]([ァ-ヶー]{2,8}|[一-龥]{2,5}[ぁ-ん]{0,2})", h)
            if m2:
                name = re.sub(r"(さん|氏|選手|アナ)$", "", m2.group(1).strip())
                if name and name not in SKIP_WORDS and name not in seen and len(name) >= 2:
                    candidates.append((name, h))
                    seen.add(name)
    return candidates[:20]

# ============================================================
# Claude Opus で投稿生成
# ============================================================
APP_CONTEXT = """
アプリ「AI人生ステータス診断」(@AILifeStatus)の公式X投稿を作る。
- 概要: 名前を入れるだけで人生がRPG化する無料診断 (ai-life-status.vercel.app)
- ジョブ全32種: 伝説の社畜/深夜のコンビニ賢者/布団の守護神/カフェイン魔術師/散財の錬金術師/孤高のソロキャンパー/妄想の建築家/通知の奴隷/AI魔法剣士/深夜ラーメン背徳者/ドライブの哲学者/推し活の聖女/副業沼の冒険者/永遠の計画マン/カフェ巡りの魔女/ストーリーズの女神/コスメ錬金術師/積ん読の大賢者/昼寝の大魔王/サブスク放置の貴族/推しの騎士/深夜アニメの求道者/Google検索の勇者/タピオカの巫女/Zoom疲れの勇者/TikTok沼の住人/推し活破産者/深夜Xの亡者/週末シェフ見習い/寝落ち配信の伴走者/ガジェット沼の住人/名言コレクターの賢者
- ステータス: 💪体力/🧠知力/💰金運/😎孤独耐性/🔥やる気/🍀運（値1〜9999、稀に???）
- 必殺技: 無限先延ばし/深夜のひらめき/課金カタルシス/布団バリア/推しパワー全開/カフェイン三連/二度寝の覇道/Amazonワンクリック など
- 弱点: 月曜朝 全ステ-50%（解呪不可）/「あと5分」→30分バグ/布団引力への耐性ゼロ/「明日やろう」自動発動 など
- 世界観: RPGの冒険者ギルド。「診断/占い」は使わず「ギルドに登録」と言う
"""

def generate_with_opus(name, headline, num=2, demo_grade="B", demo_reason="—"):
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "ここにキーを貼り付け":
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        demo_note = {
            "A": f"（{demo_reason}関連 → 10-20代メインで刺さりやすい）",
            "B": "（10-40代幅広い層）",
            "C": f"（{demo_reason}のため40代以上も多い → 10-30代にも刺さる普遍的な切り口にすること）",
        }.get(demo_grade, "")
        hashtag = _name_to_hashtag(name)
        prompt = f"""{APP_CONTEXT}

今日のトレンド: 「{name}」（元ネタ: {headline}）
ターゲット層評価: {demo_grade} {demo_note}

このトレンドを使い@AILifeStatusらしい投稿を{num}パターン作成。

ルール:
- ターゲット: 10-30代のSNSヘビーユーザー（推し活/スポーツ/ゲームファン）
  - ターゲット層が40代以上メインの場合は、世代を問わない「あるある」ネタに昇華すること
  - バンド・グループ名の場合は「メンバー全員の総合値」として、そのグループらしさをステータスで表現すること
- 全角換算140文字以内（ai-life-status.vercel.appは23カウント）
- 末尾ハッシュタグ: #AI人生ステータス #{hashtag}（アイドルはグループ名、選手はチーム名も追加。最大3タグ。スペースは_に変換）
- #診断 #やってみて は不要
- トレンドの内容をステータス診断結果として面白おかしく絡める
- 笑い・共感・驚きのどれかを必ず入れる
- URL前に「あなたのジョブは何？↓」を1行入れる

出力形式（説明文なし）:
---[1]
（投稿本文）
---[2]
（投稿本文）"""
        msg = client.messages.create(
            model=OPUS_MODEL, max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        print(f"  ⚠️ Opus エラー: {e}")
        return None

# ============================================================
# フォールバック投稿（diagnose()でアプリ実測値を使用）
# ============================================================
def _pick_interesting(sv: dict) -> tuple:
    """??? > 超高値(≥1000) > 超低値(≤30) > 最大値 の優先度でstatを選ぶ"""
    for k, s in sv.items():
        if s["value"] == -1:
            return k, s
    highs = {k: s for k, s in sv.items() if isinstance(s["value"], int) and s["value"] >= 1000}
    if highs:
        k = max(highs, key=lambda k: highs[k]["value"])
        return k, highs[k]
    lows = {k: s for k, s in sv.items() if isinstance(s["value"], int) and s["value"] <= 30}
    if lows:
        k = min(lows, key=lambda k: lows[k]["value"])
        return k, lows[k]
    k = max(sv, key=lambda k: sv[k]["value"])
    return k, sv[k]

def _make_note(d: dict, source: str) -> str:
    """診断値から投稿のポイントを自動生成"""
    sv = d["sv"]
    points = []
    rare = [s["icon"] for s in sv.values() if s["value"] == -1]
    if rare:
        points.append(f"{'/'.join(rare)}が???（超レア3%演出）")
    highs = [(s["icon"], s["value"]) for s in sv.values()
             if isinstance(s["value"], int) and s["value"] >= 1000]
    for icon, v in highs:
        points.append(f"{icon}{v:,}の異常値")
    lows = [(s["icon"], s["value"]) for s in sv.values()
            if isinstance(s["value"], int) and s["value"] <= 30]
    for icon, v in lows:
        points.append(f"{icon}{v}の超低値がギャップになる")
    if not points:
        points.append(f"ジョブ「{d['job']}」・弱点のギャップをネタに")
    return "💡 " + " / ".join(points)

def _heuristic_buzz(d: dict, headline: str = "", demo_grade: str = "B", variant_label: str = "") -> dict:
    """
    APIなしのフォールバック時に診断値・ソース・バリアントからbuzzスコアを推定する。
    不一致(ic)/覚醒(ar)/自己参照(sr)/情報G(ig)/拡散(sc) それぞれ 1〜10。
    """
    sv = d["sv"]
    ic = ar = sr = ig = sc = 5

    has_rare  = any(s["value"] == -1 for s in sv.values())
    highs     = [s["value"] for s in sv.values() if isinstance(s["value"], int) and s["value"] >= 1000]
    lows      = [s["value"] for s in sv.values() if isinstance(s["value"], int) and 0 < s["value"] <= 30]

    # ??? 超レア → 不一致・拡散 UP
    if has_rare:
        ic = min(10, ic + 4)
        sc = min(10, sc + 3)

    # 異常高値 → 覚醒・不一致 UP
    if highs:
        ic = min(10, ic + 2)
        ar = min(10, ar + 2)

    # 超低値 → 自己参照・不一致 UP（あるある共感）
    if lows:
        ic = min(10, ic + 2)
        sr = min(10, sr + 3)

    # 高値と低値が両方ある → ギャップ最大 → 不一致・拡散 さらに UP
    if highs and lows:
        ic = min(10, ic + 2)
        sc = min(10, sc + 2)

    # Xトレンド順位が高い → 拡散力 UP
    if "Xトレンド" in headline:
        m = re.search(r"Xトレンド (\d+)位", headline)
        if m:
            rank = int(m.group(1))
            bonus = 3 if rank <= 3 else 2 if rank <= 10 else 1
            sc = min(10, sc + bonus)

    # Googleトレンド → 情報価値 UP
    if "Google" in headline:
        ig = min(10, ig + 2)

    # Z世代A評価 → 拡散・自己参照 UP
    if demo_grade == "A":
        sc = min(10, sc + 2)
        sr = min(10, sr + 1)
    elif demo_grade == "C":
        sc = max(1, sc - 1)

    # バリアント別の傾向補正
    if "案A" in variant_label:   # 結論先出し → 拡散・不一致
        sc = min(10, sc + 1); ic = min(10, ic + 1)
    elif "案B" in variant_label:  # 発見型 → 不一致
        ic = min(10, ic + 2)
    elif "案C" in variant_label:  # リスト型 → 情報G
        ig = min(10, ig + 2)
    elif "案D" in variant_label:  # 一言ボケ → 自己参照
        sr = min(10, sr + 2)
    elif "案E" in variant_label:  # ニュースフック → 拡散・情報G
        sc = min(10, sc + 2); ig = min(10, ig + 1)

    return {"ic": ic, "ar": ar, "sr": sr, "ig": ig, "sc": sc}


def make_fallback_variants(name, headline="", demo_grade="B"):
    """診断値から複数フォーマットの投稿案を生成して返す"""
    d   = diagnose(name)
    sv  = d["sv"]
    tag = _name_to_hashtag(name)
    footer = f"あなたのジョブは何？↓\n{SITE_URL}\n{HASHTAGS} #{tag}"

    _, pick = _pick_interesting(sv)
    val_str   = "???" if pick["value"] == -1 else f"{pick['value']:,}"
    stat_line = f"{pick['icon']}：{val_str}"

    job = d["job"]
    wk  = d["weakness"]

    highs = [(s["icon"], s["value"]) for s in sv.values()
             if isinstance(s["value"], int) and s["value"] >= 1000]

    variants = []

    # 案A: 結論先出し
    if highs:
        hi_icon, hi_val = max(highs, key=lambda x: x[1])
        variants.append(("案A 結論先出し",
            f"弱点が「{wk}」なのに\n{hi_icon}{hi_val:,}で戦ってる{name}、\nジョブ「{job}」で全部納得した\n\n{footer}"))
    else:
        variants.append(("案A 結論先出し",
            f"{name}のジョブが「{job}」だった\n\n弱点「{wk}」なのに{stat_line}\nこのギャップが全てを物語ってる\n\n{footer}"))

    # 案B: 発見型（〜だった）
    variants.append(("案B 発見型",
        f"{name}の弱点、「{wk}」だった\n\n{stat_line}あるのにここが限界\nジョブ「{job}」の正体はこれか\n\n{footer}"))

    # 案C: リスト+ツッコミ
    variants.append(("案C リスト型",
        f"{name}の人生ステータスを確認した\n\nジョブ：{job}\n{stat_line}\n弱点：{wk}\n\n{stat_line}でこの弱点、強すぎる\n\n{footer}"))

    # 案D: 一言ボケ
    variants.append(("案D 一言ボケ",
        f"{name}のジョブが「{job}」だった\n\n{stat_line}\n弱点「{wk}」\n\nこれで成立してるの、すごい\n\n{footer}"))

    # 案E: ニュースフック（headline がある場合）
    if headline and len(headline) > 4:
        hook = headline[:20].rstrip("　 、。")
        variants.append(("案E ニュースフック",
            f"{hook}の今日、{name}の人生ステータスを測ってみた\n\nジョブ「{job}」\n{stat_line}\n弱点「{wk}」\n\n{footer}"))

    return d, variants


def make_fallback(name):
    """後方互換用（単一案）"""
    _, variants = make_fallback_variants(name)
    return variants[0][1]

# ============================================================
# HTML テンプレート（編集ダイアログ＋X投稿ボタン付き）
# ============================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>@AILifeStatus 投稿案 - {date}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#faf5ff;color:#2a2040;font-family:'Noto Sans JP',-apple-system,sans-serif;line-height:1.7;font-size:15px}}
.w{{max-width:720px;margin:0 auto;padding:24px 16px}}
h1{{font-size:1.4em;border-bottom:3px solid #7c5ce7;padding-bottom:8px;margin-bottom:20px}}
h2{{font-size:1.0em;color:#7c5ce7;margin:24px 0 8px;padding:5px 12px;background:rgba(124,92,231,.06);border-left:4px solid #7c5ce7;border-radius:0 6px 6px 0}}
h2.hot{{color:#e84393;border-left-color:#e84393;background:rgba(232,67,147,.06)}}
.card{{background:#fff;border-radius:10px;padding:14px;margin-bottom:20px;border:1px solid #e8ddf5}}
.post-box{{background:#000;color:#e0e0e0;border-radius:10px;padding:16px;margin:8px 0;font-size:.88em;line-height:1.85;white-space:pre-wrap;cursor:pointer;position:relative;transition:outline .1s}}
.post-box:hover{{outline:2px solid #7c5ce7}}
.post-box::before{{content:attr(data-label);position:absolute;top:-10px;left:10px;background:#7c5ce7;color:#fff;font-size:.6em;padding:1px 8px;border-radius:3px;white-space:nowrap}}
.tag{{color:#1d9bf0}}
.char-count{{font-size:.72em;color:#00b894;font-weight:700;margin-top:4px}}
.char-count.over{{color:#e84393}}
.note{{font-size:.75em;color:#8a7aaa;margin-top:6px}}
.btns{{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}}
.btn{{padding:7px 16px;border:none;border-radius:6px;font-size:.74em;font-weight:700;cursor:pointer;font-family:inherit;min-height:36px}}
.btn-edit{{background:#7c5ce7;color:#fff}}
.btn-copy{{background:#e8ddf5;color:#2a2040}}
.btn-x{{background:#000;color:#fff}}
.source-tag{{display:inline-block;background:#ff8c42;color:#fff;font-size:.62em;padding:1px 7px;border-radius:3px;margin-bottom:6px}}
.google-tag{{background:#0984e3}}
.score-bar{{display:flex;gap:5px;flex-wrap:wrap;margin:6px 0;align-items:center}}
.sc{{display:inline-flex;align-items:center;gap:2px;font-size:.66em;padding:2px 8px;border-radius:12px;font-weight:600;cursor:default}}
.sc b{{font-size:1.15em;margin-left:1px}}
.sc-high{{background:#00b894;color:#fff}}
.sc-mid{{background:#f9a825;color:#fff}}
.sc-low{{background:#b2bec3;color:#fff}}
.sc-avg{{display:inline-flex;align-items:center;gap:2px;font-size:.72em;font-weight:800;padding:2px 10px;border-radius:12px;background:#7c5ce7;color:#fff}}

/* ソートバー */
.sort-bar{{display:flex;gap:6px;margin-bottom:20px;align-items:center;flex-wrap:wrap}}
.sort-bar span{{font-size:.78em;color:#8a7aaa;font-weight:700;white-space:nowrap}}
.btn-sort{{padding:5px 12px;border:2px solid #7c5ce7;border-radius:20px;background:#fff;color:#7c5ce7;font-size:.72em;font-weight:700;cursor:pointer;font-family:inherit;transition:all .15s;white-space:nowrap}}
.btn-sort.active,.btn-sort:hover{{background:#7c5ce7;color:#fff}}

/* グループコンテナ・ラッパー */
#groups-container{{display:flex;flex-direction:column}}
.post-group{{display:flex;flex-direction:column;transition:order .3s}}
.card-wrap{{transition:order .3s}}

/* 編集モーダル */
.modal-bg{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:200;align-items:center;justify-content:center;padding:16px}}
.modal-bg.on{{display:flex}}
.modal{{background:#fff;border-radius:12px;padding:20px;width:100%;max-width:560px;max-height:90vh;overflow-y:auto}}
.modal h3{{font-size:1em;margin-bottom:10px;color:#7c5ce7}}
.modal textarea{{width:100%;height:240px;padding:12px;border:1.5px solid #e8ddf5;border-radius:8px;font-size:.88em;line-height:1.85;font-family:inherit;resize:vertical;background:#000;color:#e0e0e0}}
.modal textarea:focus{{outline:none;border-color:#7c5ce7}}
.modal-count{{font-size:.74em;font-weight:700;margin:6px 0;color:#00b894}}
.modal-count.over{{color:#e84393}}
.modal-btns{{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}}
.modal-btns .btn{{flex:1}}
</style>
</head>
<body>
<div class="w">
<h1>⚔️ @AILifeStatus 投稿案 <span style="font-size:.6em;color:#8a7aaa">{date}</span></h1>

<div class="sort-bar">
  <span>並び替え:</span>
  <button class="btn-sort active" id="sort-az"  onclick="sortGroups('az')">50音順</button>
  <button class="btn-sort"        id="sort-avg" onclick="sortGroups('avg')">avg ▼</button>
  <button class="btn-sort"        id="sort-ic"  onclick="sortGroups('ic')">不一致</button>
  <button class="btn-sort"        id="sort-ar"  onclick="sortGroups('ar')">覚醒</button>
  <button class="btn-sort"        id="sort-sr"  onclick="sortGroups('sr')">自己参照</button>
  <button class="btn-sort"        id="sort-ig"  onclick="sortGroups('ig')">情報G</button>
  <button class="btn-sort"        id="sort-sc"  onclick="sortGroups('sc')">拡散</button>
</div>

<div id="groups-container">
{body}
</div>

</div>

<!-- 編集モーダル -->
<div class="modal-bg" id="modalBg">
<div class="modal">
  <h3>✏️ 投稿を編集</h3>
  <textarea id="editArea" oninput="updateCount()"></textarea>
  <p class="modal-count" id="modalCount">0 / 140文字</p>
  <div class="modal-btns">
    <button class="btn btn-copy" onclick="applyCopy()">コピー</button>
    <button class="btn btn-x"    onclick="postToX()">𝕏 Xで投稿</button>
    <button class="btn btn-edit" style="background:#8a7aaa" onclick="closeModal()">閉じる</button>
  </div>
</div>
</div>

<script>
// ---- 文字数カウント（X方式） ----
function xCount(text) {{
  const siteUrl = 'ai-life-status.vercel.app';
  const urlRe = /https?:\\/\\/\\S+/g;
  let urls = text.match(urlRe) || [];
  let t = text.replace(urlRe, '');
  let cnt = urls.length * 23;
  for (let ch of t) cnt += ch.charCodeAt(0) <= 0xFF ? 1 : 2;
  // bare URL (https://なし)
  let n = (text.split(siteUrl).length - 1);
  let raw = 0; for (let c of siteUrl) raw += c.charCodeAt(0) <= 0xFF ? 1 : 2;
  cnt = cnt - n * raw + n * 23;
  return cnt;
}}
function charDisplay(text) {{ return Math.ceil(xCount(text) / 2); }}

// ---- モーダル ----
let currentId = null;

function openEdit(id) {{
  currentId = id;
  const el = document.getElementById(id);
  let text = '';
  el.childNodes.forEach(n => text += n.textContent);
  document.getElementById('editArea').value = text.trim();
  updateCount();
  document.getElementById('modalBg').classList.add('on');
}}

function closeModal() {{
  document.getElementById('modalBg').classList.remove('on');
}}

function updateCount() {{
  const text = document.getElementById('editArea').value;
  const d = charDisplay(text);
  const el = document.getElementById('modalCount');
  el.textContent = d + ' / 140文字';
  el.className = 'modal-count' + (d > 140 ? ' over' : '');
}}

function applyCopy() {{
  const text = document.getElementById('editArea').value.trim();
  navigator.clipboard.writeText(text).then(() => {{
    // 元の投稿ボックスも更新
    if (currentId) {{
      const box = document.getElementById(currentId);
      if (box) box.textContent = text;
    }}
    alert('コピーしました！');
    closeModal();
  }});
}}

function postToX() {{
  const text = document.getElementById('editArea').value.trim();
  const encoded = encodeURIComponent(text);
  window.open('https://x.com/intent/tweet?text=' + encoded, '_blank');
}}

function copyOnly(id) {{
  const el = document.getElementById(id);
  let text = '';
  el.childNodes.forEach(n => text += n.textContent);
  navigator.clipboard.writeText(text.trim()).then(() => {{
    alert('コピーしました！');
  }});
}}

function postDirect(id) {{
  const el = document.getElementById(id);
  let text = '';
  el.childNodes.forEach(n => text += n.textContent);
  window.open('https://x.com/intent/tweet?text=' + encodeURIComponent(text.trim()), '_blank');
}}

// モーダル背景クリックで閉じる
document.getElementById('modalBg').addEventListener('click', function(e) {{
  if (e.target === this) closeModal();
}});

// ---- ソート ----
let currentSort = 'az';
function sortGroups(mode) {{
  currentSort = mode;
  document.querySelectorAll('.btn-sort').forEach(b => b.classList.remove('active'));
  document.getElementById('sort-' + mode).classList.add('active');
  const container = document.getElementById('groups-container');
  const groups = [...container.querySelectorAll('.post-group')];
  const allCards = [...document.querySelectorAll('.card-wrap')];

  if (mode === 'az') {{
    // カードを各グループに戻す
    allCards.forEach(c => {{
      const g = container.querySelector('.post-group[data-person="' + c.dataset.person + '"]');
      if (g) g.appendChild(c);
    }});
    // グループ内を元の順序に
    groups.forEach(g => {{
      const cards = [...g.querySelectorAll('.card-wrap')];
      cards.sort((a, b) => parseInt(a.dataset.origOrder) - parseInt(b.dataset.origOrder));
      cards.forEach(c => g.appendChild(c));
    }});
    // グループを50音順に
    groups.sort((a, b) => a.dataset.person.localeCompare(b.dataset.person, 'ja'));
    groups.forEach(g => container.appendChild(g));
    groups.forEach(g => {{ g.style.display = ''; }});
  }} else {{
    // 全カードをスコア順にフラット並び替え
    allCards.sort((a, b) => parseFloat(b.dataset[mode]) - parseFloat(a.dataset[mode]));
    allCards.forEach(c => container.appendChild(c));
    // 空になったグループを非表示
    groups.forEach(g => {{ g.style.display = 'none'; }});
  }}
}}
</script>
</body>
</html>"""

CARD_TEMPLATE = """
<div class="card-wrap" data-avg="{avg}" data-ic="{ic}" data-ar="{ar}" data-sr="{sr}" data-ig="{ig}" data-sc="{sc}" data-person="{person}" data-orig-order="{orig_order}">
<h2 class="{h2class}">{label}</h2>
<div class="card">
<span class="source-tag {src_cls}">📰 {source}</span>
{score_bar}
<div class="post-box" id="{pid}" data-label="{label}" onclick="openEdit('{pid}')">{post_text}</div>
<p class="char-count {cnt_cls}">{disp} / 140文字 {ok_str}</p>
<p class="note">{note}</p>
<div class="btns">
  <button class="btn btn-edit" onclick="openEdit('{pid}')">✏️ 編集</button>
  <button class="btn btn-copy" onclick="copyOnly('{pid}')">コピー</button>
  <button class="btn btn-x"   onclick="postDirect('{pid}')">𝕏 Xで投稿</button>
</div>
</div>
</div>"""

_AXES = [('不一致','ic'), ('覚醒','ar'), ('自己参照','sr'), ('情報G','ig'), ('拡散','sc')]

def _sc_cls(v):
    return "sc-high" if v >= 8 else "sc-mid" if v >= 6 else "sc-low"

def _score_bar(buzz):
    """buzz dict → (html, avg, ic, ar, sr, ig, sc)"""
    if isinstance(buzz, int):
        buzz = {k: buzz for _, k in _AXES}
    ic = buzz.get('ic', 5); ar = buzz.get('ar', 5); sr = buzz.get('sr', 5)
    ig = buzz.get('ig', 5); sc = buzz.get('sc', 5)
    avg = round((ic + ar + sr + ig + sc) / 5, 1)
    axes = [('不一致', ic), ('覚醒', ar), ('自己参照', sr), ('情報G', ig), ('拡散', sc)]
    parts = [f'<span class="sc {_sc_cls(v)}" title="{n}">{n}<b>{v}</b></span>' for n, v in axes]
    parts.append(f'<span class="sc-avg">avg<b>{avg}</b></span>')
    return '<div class="score-bar">' + ''.join(parts) + '</div>', avg, ic, ar, sr, ig, sc

def build_html(posts_data, date_str):
    # personごとにグループ化（出現順を保持）
    from collections import OrderedDict
    groups = OrderedDict()
    for i, item in enumerate(posts_data):
        person = item.get("person", item["label"])
        if person not in groups:
            groups[person] = []
        groups[person].append((i, item))

    group_blocks = []
    for person, items in groups.items():
        cards = []
        max_avg = max_ic = max_ar = max_sr = max_ig = max_sc = 0.0
        for orig_order, (i, item) in enumerate(items):
            pid = f"p{i}"
            raw, disp, ok = check_post(item["post"])
            post_escaped = (item["post"]
                            .replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))
            buzz = item.get("buzz", {"ic":5,"ar":5,"sr":5,"ig":5,"sc":5})
            sb_html, avg, ic, ar, sr, ig, sc = _score_bar(buzz)
            max_avg = max(max_avg, avg)
            max_ic  = max(max_ic,  ic)
            max_ar  = max(max_ar,  ar)
            max_sr  = max(max_sr,  sr)
            max_ig  = max(max_ig,  ig)
            max_sc  = max(max_sc,  sc)
            cards.append(CARD_TEMPLATE.format(
                h2class   = "hot" if item.get("hot") else "",
                label     = item["label"],
                source    = item["source"][:40],
                src_cls   = "google-tag" if "Google" in item["source"] else "",
                pid       = pid,
                post_text = post_escaped,
                disp      = disp,
                cnt_cls   = "over" if not ok else "",
                ok_str    = "✅" if ok else "❌ オーバー",
                note      = item.get("note",""),
                score_bar = sb_html,
                avg        = avg,
                ic         = ic,
                ar         = ar,
                sr         = sr,
                ig         = ig,
                sc         = sc,
                person     = person.replace('"', '&quot;'),
                orig_order = orig_order,
            ))
        person_esc = person.replace('"', '&quot;')
        group_blocks.append(
            f'<div class="post-group" data-person="{person_esc}" '
            f'data-avg="{max_avg}" data-ic="{max_ic}" data-ar="{max_ar}" '
            f'data-sr="{max_sr}" data-ig="{max_ig}" data-sc="{max_sc}">\n'
            + "\n".join(cards)
            + "\n</div>"
        )
    return HTML_TEMPLATE.format(date=date_str, body="\n".join(group_blocks))

# ============================================================
# メイン
# ============================================================
def main():
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*55}")
    print(f"  @AILifeStatus トレンド投稿ネタ収集ツール")
    print(f"  実行時刻: {date_str}")
    print(f"{'='*55}\n")

    use_opus = bool(ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "ここにキーを貼り付け")
    print(f"  AI: {'✅ Claude Opus' if use_opus else '⚠️  テンプレートモード（config.py にAPIキーを設定）'}\n")

    print("📡 トレンド取得中...\n")
    yahoo_trends, google_trends, x_trends = get_all_trends()

    # 表示
    print("  𝕏 Xトレンド Japan (trends24.in)")
    for rank, (name, _) in enumerate(x_trends[:20], 1):
        print(f"    {rank:2}. {name}")
    print()

    for label, headlines in yahoo_trends.items():
        icon = "🎭" if label=="エンタメ" else "⚾" if label=="スポーツ" else "📰"
        print(f"  {icon} Yahoo {label}")
        for i,h in enumerate(headlines[:6],1): print(f"    {i}. {h}")
        print()

    print("  🔍 Google Trends Japan")
    for i,(name,traffic) in enumerate(google_trends[:10],1):
        print(f"    {i:2}. {name:<12} ({traffic})")
    print()

    # 人名抽出
    names = extract_names(yahoo_trends, google_trends, x_trends)

    # ターゲット適合度スコアリング → A優先で並び替え
    scored = []
    seen_names = {name for name, _ in names}
    for name, src in names:
        grade, reason = _target_score(name, src)
        scored.append((name, src, grade, reason))
    scored.sort(key=lambda x: {"A": 0, "B": 1, "C": 2}[x[2]])

    # Z世代A候補が2本未満 → 固定プールから補充
    import random as _random
    a_count = sum(1 for *_, g, _ in scored[:6] if g == "A")
    if a_count < 2:
        need = 2 - a_count
        pool = [(n, s) for n, s in FIXED_Z_POOL if n not in seen_names]
        extras = _random.sample(pool, min(need, len(pool)))
        for name, src in extras:
            scored.insert(0, (name, src, "A", "固定Z世代候補"))
            seen_names.add(name)
        if extras:
            print(f"  ℹ️  Z世代A候補が少ないため固定プールから {len(extras)} 件補充")

    grade_icon = {"A": "🟢", "B": "🟡", "C": "🔴"}
    print("👤 投稿ネタ候補（10-30代適合度順）")
    for i,(name,src,grade,reason) in enumerate(scored[:10],1):
        print(f"  {i:2}. {grade_icon[grade]}{grade} {name:<10} ← {src[:30]}")
    print()

    # 投稿生成
    posts_data = []
    print(f"{'='*55}")
    print("  投稿生成中...")
    print(f"{'='*55}\n")

    for name, headline, demo_grade, demo_reason in scored[:6]:
        print(f"  ⚡ {name} [{grade_icon[demo_grade]}{demo_grade}]...")
        if use_opus:
            result = generate_with_opus(name, headline, num=4,
                                        demo_grade=demo_grade, demo_reason=demo_reason)
            if result:
                parts = re.split(r"---\[\d+\]\n?", result)
                for j, rp in enumerate([p.strip() for p in parts if p.strip()], 1):
                    _, disp, ok = check_post(rp)
                    print(f"    Opus 案{j}: {disp}/140 {'✅' if ok else '❌'}")
                    posts_data.append({
                        "label"  : f"🔥 {name} Opus案{j}",
                        "source" : headline[:35],
                        "post"   : rp,
                        "note"   : f"Claude Opus生成 | {headline[:40]}",
                        "hot"    : True,
                        "person" : name,
                    })
                continue
        # フォールバック: 複数フォーマット生成
        d, variants = make_fallback_variants(name, headline, demo_grade)
        note_base = _make_note(d, headline)
        if demo_grade == "C":
            note_base += f" ⚠️ ターゲット層やや外（{demo_reason}）"
        for v_label, post in variants:
            _, disp, ok = check_post(post)
            buzz = _heuristic_buzz(d, headline, demo_grade, v_label)
            print(f"    {v_label}: {disp}/140 {'✅' if ok else '❌'}")
            posts_data.append({
                "label"  : f"{name} {v_label}",
                "source" : headline[:35],
                "post"   : post,
                "note"   : note_base,
                "hot"    : False,
                "person" : name,
                "buzz"   : buzz,
            })

    # HTML出力
    html_out = build_html(posts_data, date_str)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"\n✅ {OUTPUT_HTML} に {len(posts_data)} 件出力")
    print("   ブラウザで開いて「編集」「コピー」「𝕏 Xで投稿」ボタンを使ってください\n")

if __name__ == "__main__":
    main()

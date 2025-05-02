from flask import Flask
import threading
import os
import asyncio
import json
import random
import websockets
from misskey import Misskey
from datetime import datetime

# ========== Flask（Render + UptimeRobot用） ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# ========== Misskey設定 ==========
INSTANCE = "pri.monster"
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN が設定されていません。Renderの環境変数を確認してください。")

misskey = Misskey(INSTANCE, i=TOKEN)
WS_URL = f"wss://{INSTANCE}/streaming?i={TOKEN}"

# ========== 起動時ノート投稿 ==========
try:
    misskey.notes_create(
        text="<small>（ワタを詰め替えられている...）</small>",
        visibility="home",
        localOnly=True
    )
    print("📝 起動時にローカル限定ノートを投稿しました")
except Exception as e:
    print(f"❌ 起動ノート投稿失敗: {e}")

# ========== ユーザーリアクションデータ ==========
USER_REACTIONS_FILE = "user_reactions.json"
if os.path.exists(USER_REACTIONS_FILE):
    with open(USER_REACTIONS_FILE, "r", encoding="utf-8") as f:
        user_reactions = json.load(f)
else:
    user_reactions = {}

def save_user_reactions():
    with open(USER_REACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(user_reactions, f, ensure_ascii=False, indent=2)

# ========== キーワード ==========
KEYWORDS = {
    "はんこ": [":hanko_sumi:", ":hanko_sena_miss:", ":hanko_sena2:", ":hanko_sakuma_r2:", ":hanko_hasumi_miss:", ":hanko_hasumi:", ":hanko_sagami:", ":hanko_nagumo:", ":hanko_kunugi:", ":ksmc_kakuin:", ":kiryu_hanko:", ":hanko_sena:", ":hanko_mikejima:"],
    "ぱんれ": [":panre_close:", ":gohan_time_cat:", ":panre_dabadaba:", ":panre_half:", ":panre_iq:", ":panre_mirror:", ":panre_ndi:", ":panre_ore:"],
    "パン": [":ibuki_nomming:", ":ibuki_nomming2:", ":panre_fes_0point:", ":panre_fes_1point:", ":panre_fes_2point:", ":panre_fes_3point:", ":pandead_1point:", ":pandead_3point_foul:"],
    "ほめて": [":petthex:", ":panre_shortarms:"],
    "ほめろ": [":petthex:", ":panre_shortarms:"],
    "おはよう": [":panle_morning:", ":panle_sleep:"],
    "おやすみ": [":panre_honmono:", ":oyasumi2:", ":panre_cry:"],
    "ぱんれおやすみ": [":panre_honmono:", ":oyasumi2:", ":panre_cry:"],
    "ねるか": [":panre_honmono:", ":oyasumi2:", ":panre_cry:"],
    "寝るか": [":panre_honmono:", ":oyasumi2:", ":panre_cry:"],
    ":oyapumi:": [":panre_honmono:", ":oyasumi2:", ":panre_cry:"],
    "ぷりしろ": [":panre_honmono_silence:", ":panre_puri:", ":panre_honmono_close:", ":panre_pote:", ":panre_iq:", ":panre_honmono:", ":panre_cry:"]
}

EXCLUDE_KEYWORDS = [
    "食べたい", "パンツ", "フライパン", "パンフレット", "パンダ",
    "パントマイム", "チノパン", "ジーパン", "パンチ", "ジャパン"
]

# ========== 時間帯遅延 ==========
def get_reaction_delay():
    now_hour = datetime.now().hour
    if 6 <= now_hour < 12:
        return random.randint(8, 13)
    elif 12 <= now_hour < 18:
        return random.randint(6, 10)
    elif 18 <= now_hour < 24:
        return random.randint(2, 4)
    else:
        return random.randint(2, 7)

# ========== WebSocket処理 ==========
async def listen():
    print("WebSocket 接続を開始しています...")
    async with websockets.connect(WS_URL) as websocket:
        await websocket.send(json.dumps({
            "type": "connect",
            "body": {
                "channel": "localTimeline",
                "id": "local"
            }
        }))
        print("✅ タイムラインのストリーミング接続が確立しました")

        while True:
            msg = await websocket.recv()
            data = json.loads(msg)

            if data["type"] == "channel" and data["body"]["type"] == "note":
                note = data["body"]["body"]
                text = note.get("text", "")
                note_id = note["id"]
                user_name = note["user"]["username"]
                visibility = note.get("visibility", "unknown")

                print(f"\n--- ノート受信 ---")
                print(f"👤 投稿者: {user_name}")
                print(f"📄 内容: {text}")
                print(f"🔒 可視性: {visibility}")

                if visibility not in ["public", "home", "followers"]:
                    continue

                delay = get_reaction_delay()
                print(f"⏳ {delay}秒待機してから反応します")
                await asyncio.sleep(delay)

                # 好きな絵文字登録
                if text.startswith("好きな絵文字は") and "だよ" in text:
                    emoji = text.split("好きな絵文字は")[-1].split("だよ")[0].strip()
                    if emoji:
                        user_reactions[user_name] = emoji
                        save_user_reactions()
                        print(f"📝 {user_name} の好きな絵文字を {emoji} として保存しました")
                        try:
                            misskey.notes_reactions_create(note_id=note_id, reaction=":panre_happy:")
                        except Exception as e:
                            print(f"❌ 登録リアクションエラー: {e}")
                    continue

                if any(word in text for word in EXCLUDE_KEYWORDS):
                    print("⚠️ 除外ワードが含まれているためスキップ")
                    continue

                if user_name in user_reactions:
                    fav_emoji = user_reactions[user_name]
                    if fav_emoji in text:
                        try:
                            misskey.notes_reactions_create(note_id=note_id, reaction=fav_emoji)
                            print(f"💖 好きな絵文字でリアクション：{fav_emoji}")
                        except Exception as e:
                            print(f"❌ リアクションエラー: {e}")
                        continue

                for word, reactions in KEYWORDS.items():
                    if word in text:
                        reaction = random.choice(reactions)
                        try:
                            misskey.notes_reactions_create(note_id=note_id, reaction=reaction)
                            print(f"✅ キーワード反応: {reaction}")
                        except Exception as e:
                            print(f"❌ リアクションエラー: {e}")
                        break

# ========== 自動再接続付き起動 ==========
async def main_loop():
    while True:
        try:
            await listen()
        except Exception as e:
            print(f"❌ 接続エラー（再接続します）: {e}")
            await asyncio.sleep(10)

asyncio.run(main_loop())

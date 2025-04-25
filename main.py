import os
import asyncio
import json
import random
import websockets
from misskey import Misskey
from keep_alive import keep_alive
from datetime import datetime

# Misskeyのインスタンス情報
INSTANCE = "pri.monster"
TOKEN = os.getenv("TOKEN")  # 環境変数からトークンを取得

if not TOKEN:
    raise ValueError("TOKEN が設定されていません。Renderの環境変数を確認してください。")

misskey = Misskey(INSTANCE, i=TOKEN)
WS_URL = f"wss://{INSTANCE}/streaming?i={TOKEN}"

# 好きな絵文字の記録用ファイル
USER_REACTIONS_FILE = "user_reactions.json"
if os.path.exists(USER_REACTIONS_FILE):
    with open(USER_REACTIONS_FILE, "r", encoding="utf-8") as f:
        user_reactions = json.load(f)
else:
    user_reactions = {}

def save_user_reactions():
    with open(USER_REACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(user_reactions, f, ensure_ascii=False, indent=2)

# キーワードとランダムリアクション候補
KEYWORDS = {
    "はんこ": [":hanko_sumi:", ":hanko_sena_miss::hanko_sena2:", ":hanko_sakuma_r2:", ":hanko_hasumi_miss:", ":hanko_hasumi:", ":hanko_sagami:", ":hanko_nagumo:", ":hanko_kunugi:", ":ksmc_kakuin:", ":kiryu_hanko:", ":hanko_sena:", ":hanko_mikejima:"],
    "ハンコ": [":hanko_sumi:", ":hanko_sena_miss::hanko_sena2:", ":hanko_sakuma_r2:", ":hanko_hasumi_miss:", ":hanko_hasumi:", ":hanko_sagami:", ":hanko_nagumo:", ":hanko_kunugi:", ":ksmc_kakuin:", ":kiryu_hanko:", ":hanko_sena:", ":hanko_mikejima:"],
    "判子": [":hanko_sumi:", ":hanko_sena_miss::hanko_sena2:", ":hanko_sakuma_r2:", ":hanko_hasumi_miss:", ":hanko_hasumi:", ":hanko_sagami:", ":hanko_nagumo:", ":hanko_kunugi:", ":ksmc_kakuin:", ":kiryu_hanko:", ":hanko_sena:", ":hanko_mikejima:"],
    "印鑑": [":hanko_sumi:", ":hanko_sena_miss::hanko_sena2:", ":hanko_sakuma_r2:", ":hanko_hasumi_miss:", ":hanko_hasumi:", ":hanko_sagami:", ":hanko_nagumo:", ":hanko_kunugi:", ":ksmc_kakuin:", ":kiryu_hanko:", ":hanko_sena:", ":hanko_mikejima:"],
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

# 反応しないキーワード（除外ワード）
EXCLUDE_KEYWORDS = [
    "食べたい", 
    "パンツ",
    "フライパン", 
    "パンフレット",
    "パンダ", 
    "パントマイム",
    "チノパン", 
    "ジーパン",
    "パンチ",
    "ジャパン"
]

# 時間帯に応じた遅延（秒）
def get_reaction_delay():
    now_hour = datetime.now().hour
    if 6 <= now_hour < 12:
        return random.randint(4, 8)  # 朝
    elif 12 <= now_hour < 18:
        return random.randint(6, 8)   # 昼
    elif 18 <= now_hour < 24:
        return random.randint(2, 4)   # 夜
    else:
        return random.randint(2, 7)   # 深夜

# Render の自動起動保持用サーバー
keep_alive()

# メイン処理
async def listen():
    try:
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
                        print("🔒 可視性が対応外なのでスキップ")
                        continue

                    # 遅延時間を取得して待機
                    delay = get_reaction_delay()
                    print(f"⏳ {delay}秒待機してから反応します")
                    await asyncio.sleep(delay)

                    # 絵文字記録コマンド処理
                    if text.startswith("好きな絵文字は") and "だよ" in text:
                        emoji = text.split("好きな絵文字は")[-1].split("だよ")[0].strip()
                        if emoji:
                            user_reactions[user_name] = emoji
                            save_user_reactions()
                            print(f"📝 {user_name} の好きな絵文字を {emoji} として保存しました")
                            try:
                                misskey.notes_reactions_create(note_id=note_id, reaction=":panre_happy:")
                                print("🎉 リアクション（登録成功）: :panre_happy:")
                            except Exception as e:
                                print(f"❌ 登録リアクションエラー: {e}")
                        continue

                    # 除外ワードチェック
                    if any(exclude_word in text for exclude_word in EXCLUDE_KEYWORDS):
                        print("⚠️ 除外ワードが含まれているため、リアクションをスキップします")
                        continue

                    # ユーザー登録済みの絵文字で自動リアクション
                    if user_name in user_reactions:
                        fav_emoji = user_reactions[user_name]
                        if fav_emoji in text:
                            try:
                                misskey.notes_reactions_create(note_id=note_id, reaction=fav_emoji)
                                print(f"💖 ユーザーの好きな絵文字が含まれていたのでリアクション：{fav_emoji}")
                            except Exception as e:
                                print(f"❌ 好きな絵文字リアクションエラー: {e}")
                            continue

                    # 通常のキーワード反応
                    for word, reactions in KEYWORDS.items():
                        if word in text:
                            reaction = random.choice(reactions)
                            print(f"🎯 キーワード「{word}」に反応 → ランダムリアクション：{reaction}")
                            try:
                                misskey.notes_reactions_create(note_id=note_id, reaction=reaction)
                                print(f"✅ リアクション完了: {reaction}")
                            except Exception as e:
                                print(f"❌ リアクションエラー: {e}")
                            break

    except Exception as e:
        print(f"❌ 接続エラー: {e}")

# 実行
asyncio.run(listen())

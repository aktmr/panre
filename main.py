import asyncio
import json
import random
import websockets
from misskey import Misskey

# Misskeyのインスタンス情報
INSTANCE = "pri.monster"
TOKEN = "CLO1PhbNQ0G9TJ0F3L7ITMXqqqQNJrOv"

misskey = Misskey(INSTANCE, i=TOKEN)
WS_URL = f"wss://{INSTANCE}/streaming?i={TOKEN}"

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
    "駄目"
]

from keep_alive import keep_alive

keep_alive()

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

                    # 「DMや非表示ノート」などには反応しない（公開/ホーム/フォロワー限定のみに）
                    if visibility not in ["public", "home", "followers"]:
                        print("🔒 可視性が対応外なのでスキップ")
                        continue

                    # 除外ワードが含まれていたらスキップ
                    if any(exclude_word in text for exclude_word in EXCLUDE_KEYWORDS):
                        print("⚠️ 除外ワードが含まれているため、リアクションをスキップします")
                        continue

                    for word, reactions in KEYWORDS.items():
                        if word in text:
                            # ランダムにリアクションを選ぶ
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


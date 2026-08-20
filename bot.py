import asyncio
import json
import websockets
import aiohttp
from telegram import Bot
from telegram.constants import ParseMode

TELEGRAM_BOT_TOKEN = "7803249795:AAEbVXqtOFFwFAOkdvZ2T0ab4DqVVe_mquA"
TELEGRAM_CHANNEL_ID = -1003823187020

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def post_to_channel(text: str):
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False
        )
    except Exception as e:
        print("Telegram error:", e)

async def get_socials(uri: str):
    twitter = ""
    telegram = ""
    if not uri:
        return twitter, telegram

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(uri, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    twitter = data.get("twitter") or data.get("x") or ""
                    telegram = data.get("telegram") or data.get("tg") or ""
                    if not twitter and not telegram:
                        extensions = data.get("extensions") or {}
                        twitter = extensions.get("twitter") or extensions.get("x") or ""
                        telegram = extensions.get("telegram") or extensions.get("tg") or ""
    except:
        pass

    return twitter, telegram

async def listen():
    while True:
        try:
            async with websockets.connect("wss://pumpdev.io/ws", ping_interval=20) as ws:
                await ws.send(json.dumps({"method": "subscribeNewToken"}))
                print("✅ Connected – posting any coin that has Telegram...")

                async for message in ws:
                    data = json.loads(message)

                    if data.get("txType") != "create":
                        continue

                    name     = data.get("name", "Unknown")
                    symbol   = data.get("symbol", "???")
                    mint     = data.get("mint", "")
                    mcap_sol = data.get("marketCapSol") or data.get("marketCapQuote") or 0
                    uri      = data.get("uri") or ""

                    twitter, telegram = await get_socials(uri)

                    if not telegram:
                        continue

                    msg = (
                        f"🆕 <b>{name}</b> (${symbol})\n\n"
                        f"<code>{mint}</code>\n"
                        f"💰 MC: ~{mcap_sol:.1f} SOL\n\n"
                        f"🔗 <a href='https://pump.fun/{mint}'>Open on Pump.fun</a>\n"
                        f"🔍 <a href='https://solscan.io/token/{mint}'>Solscan</a>\n"
                        f"📢 <a href='{telegram}'>Telegram</a>"
                    )

                    if twitter:
                        msg += f"\n🐦 <a href='{twitter}'>Twitter / X</a>"

                    await post_to_channel(msg)
                    print(f"Posted → {name} | Has Telegram")

                    await asyncio.sleep(4)

        except Exception as e:
            print("Connection lost, reconnecting in 5s...", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(listen())

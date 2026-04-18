import asyncio
from transport import send_chat

# ---------------- CHAT INPUT ----------------
async def chat_input():
    while True:
        msg = await asyncio.to_thread(input, "chat> ")
        if msg.strip():
            send_chat(msg)

# ---------------- CHAT RECEIVER ----------------
# NOTE: incoming messages are handled and printed directly in transport.py net_to_tun to prevent blocking
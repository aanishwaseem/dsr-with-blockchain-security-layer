import socket
import asyncio
import os
from logger import log
from discovery import PEERS
from config import DATA_PORT

# ---------------- SOCKET (OWNER OF PORT 1002) ----------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", DATA_PORT))
sock.setblocking(False)

# ---------------- SEND API ----------------
def send(peer_phys_ip, payload_bytes):
    try:
        sock.sendto(payload_bytes, (peer_phys_ip, DATA_PORT))
    except Exception as e:
        print(f"[ERROR][SEND] {e}")

def send_chat(msg):
    payload = b"CHAT|" + msg.encode('utf-8')
    for phys_ip in list(PEERS.keys()):
        send(phys_ip, payload)
        log("OUTGOING", "CHAT", "user", phys_ip, msg)

# ---------------- TUN → NETWORK ----------------
async def tun_to_net(tun):
    loop = asyncio.get_running_loop()

    while True:
        packet = await loop.run_in_executor(None, os.read, tun, 2048)
        payload = b"TUN|" + packet

        for phys_ip in list(PEERS.keys()):
            send(phys_ip, payload)

# ---------------- NETWORK → TUN ----------------
async def net_to_tun(tun):
    loop = asyncio.get_running_loop()

    while True:
        data, addr = await loop.sock_recvfrom(sock, 2048)
        phys_ip = addr[0]

        if data.startswith(b"TUN|"):
            packet = data[4:]
            # Write raw IP packet back into kernel
            os.write(tun, packet)
            
            # Optional logging for TUN packets
            # log("INCOMING", "TUN", phys_ip, "local_tun", f"{len(packet)} bytes")
            
        elif data.startswith(b"CHAT|"):
            msg = data[5:].decode('utf-8', errors='ignore')
            log("INCOMING", "CHAT", phys_ip, "user", msg)
            # Print cleanly to UI
            print(f"\n[CHAT from {phys_ip}]: {msg}\nchat> ", end="", flush=True)
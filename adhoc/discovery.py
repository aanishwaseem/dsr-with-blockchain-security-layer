import socket
import asyncio
import struct
import time
from logger import log
from config import MCAST_GROUP, DISCOVERY_PORT, HEARTBEAT_INTERVAL, PEER_TIMEOUT, VIRTUAL_IP

# PEERS table: phys_ip -> {'virt_ip': virtual_ip, 'last_seen': timestamp}
PEERS = {}

# Setup UDP socket for multicasting
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("0.0.0.0", DISCOVERY_PORT))

# Join multicast group
group = socket.inet_aton(MCAST_GROUP)
mreq = struct.pack("4sL", group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

sock.setblocking(False)

def send(msg):
    sock.sendto(msg.encode(), (MCAST_GROUP, DISCOVERY_PORT))

async def discovery_loop():
    loop = asyncio.get_running_loop()

    while True:
        data, addr = await loop.sock_recvfrom(sock, 1024)
        msg = data.decode()
        phys_ip = addr[0]

        if msg.startswith("HELLO|"):
            _, virt_ip = msg.split("|")
            
            # Don't track ourselves if we receive our own broadcast
            if virt_ip == VIRTUAL_IP:
                continue

            PEERS[phys_ip] = {'virt_ip': virt_ip, 'last_seen': time.time()}
            log("INCOMING", "DISCOVERY", phys_ip, "local", msg)

            send(f"ACK|{VIRTUAL_IP}")

        elif msg.startswith("ACK|"):
            _, virt_ip = msg.split("|")
            
            # Don't track ourselves
            if virt_ip == VIRTUAL_IP:
                continue
                
            PEERS[phys_ip] = {'virt_ip': virt_ip, 'last_seen': time.time()}
            log("INCOMING", "DISCOVERY_ACK", phys_ip, "local", msg)

async def announce_loop():
    while True:
        send(f"HELLO|{VIRTUAL_IP}")
        log("OUTGOING", "DISCOVERY", "local", "broadcast", f"HELLO|{VIRTUAL_IP}")
        await asyncio.sleep(HEARTBEAT_INTERVAL)

async def cleanup():
    while True:
        now = time.time()
        stale_peers = []
        
        for phys_ip, info in PEERS.items():
            if now - info['last_seen'] > PEER_TIMEOUT:
                stale_peers.append(phys_ip)
                
        for phys_ip in stale_peers:
            log("SYSTEM", "CLEANUP", "local", phys_ip, f"Removing stale peer {PEERS[phys_ip]['virt_ip']}")
            del PEERS[phys_ip]
            
        await asyncio.sleep(5)
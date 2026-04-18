import os
import fcntl
import struct
import socket
import threading
import subprocess
import time

# ---------------- CONFIG ----------------
TUN_NAME = "dataexsys_p"

CONTROL_PORT = 1000
DISCOVERY_PORT = 1001
DATA_PORT = 1002

BROADCAST_IP = "255.255.255.255"

NODE_IP = "10.10.0.1"   # CHANGE PER NODE

PEERS = {}
peer_last_seen = {}

# ---------------- TUN SETUP ----------------
TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000


def create_tun():
    tun = os.open("/dev/net/tun", os.O_RDWR)

    ifr = struct.pack("16sH", TUN_NAME.encode(), IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun, TUNSETIFF, ifr)

    return tun


def setup_interface():
    subprocess.run(["ip", "link", "set", TUN_NAME, "up"], check=True)
    subprocess.run(["ip", "addr", "add", f"{NODE_IP}/24", "dev", TUN_NAME], check=True)


# ---------------- SOCKETS ----------------
discovery_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
discovery_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
discovery_sock.bind(("0.0.0.0", DISCOVERY_PORT))

data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
data_sock.bind(("0.0.0.0", DATA_PORT))


# ---------------- DISCOVERY ----------------
def broadcast_presence():
    while True:
        msg = f"HELLO|{NODE_IP}|{get_local_ip()}|{DATA_PORT}"
        discovery_sock.sendto(msg.encode(), (BROADCAST_IP, DISCOVERY_PORT))
        time.sleep(3)


def handle_peer(vip, rip, port):
    now = time.time()

    if vip not in PEERS:
        print(f"[NEW PEER] {vip} → {rip}:{port}")

    PEERS[vip] = (rip, port)
    peer_last_seen[vip] = now


def listen_discovery():
    while True:
        data, _ = discovery_sock.recvfrom(1024)
        msg = data.decode()

        if msg.startswith("HELLO"):
            _, vip, rip, port = msg.split("|")

            if vip != NODE_IP:
                handle_peer(vip, rip, int(port))


def cleanup_peers():
    while True:
        now = time.time()
        remove = []

        for p, t in peer_last_seen.items():
            if now - t > 15:
                remove.append(p)

        for p in remove:
            print(f"[PEER LOST] {p}")
            PEERS.pop(p, None)
            peer_last_seen.pop(p, None)

        time.sleep(5)


# ---------------- DATA TEST LAYER ----------------
def send_hello_packets():
    while True:
        if PEERS:
            for vip, (rip, port) in PEERS.items():
                msg = f"HELLO_PACKET from {NODE_IP}"
                data_sock.sendto(msg.encode(), (rip, port))
                print(f"[SEND] → {vip}")

        time.sleep(4)


def listen_data():
    while True:
        data, addr = data_sock.recvfrom(2048)
        print(f"[RECV] {addr} → {data.decode(errors='ignore')}")


# ---------------- UTIL ----------------
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


# ---------------- MAIN ----------------
def main():
    print("[+] Starting mesh v1 (DISCOVERY + DATA TEST)")

    tun = create_tun()
    setup_interface()

    print(f"[+] TUN ready: {TUN_NAME} → {NODE_IP}")

    threading.Thread(target=broadcast_presence, daemon=True).start()
    threading.Thread(target=listen_discovery, daemon=True).start()
    threading.Thread(target=cleanup_peers, daemon=True).start()

    threading.Thread(target=send_hello_packets, daemon=True).start()
    threading.Thread(target=listen_data, daemon=True).start()

    print("[+] Running... waiting for peers + packets")

    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
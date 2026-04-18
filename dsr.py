import os
import fcntl
import struct
import socket
import threading
import subprocess
import time

# ---------------- CONFIG ----------------
TUN_NAME = "dataexsys_p"
NODE_IP = "10.10.0.2"   # CHANGE PER NODE

DISCOVERY_PORT = 1001
DATA_PORT = 1002
BROADCAST_IP = "255.255.255.255"

PEERS = {}
peer_last_seen = {}

state = "NOT_CONNECTED"
connected_peer = None

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
disc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
disc_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
disc_sock.bind(("0.0.0.0", DISCOVERY_PORT))

data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
data_sock.bind(("0.0.0.0", DATA_PORT))


# ---------------- DISCOVERY ----------------
def send_hello():
    global state

    while state != "CONNECTED":
        msg = f"HELLO|{NODE_IP}"
        disc_sock.sendto(msg.encode(), (BROADCAST_IP, DISCOVERY_PORT))
        print("[DISCOVERY] HELLO sent")
        time.sleep(3)


def listen_discovery():
    global state, connected_peer

    while True:
        data, addr = disc_sock.recvfrom(1024)
        msg = data.decode()

        if msg.startswith("HELLO"):
            _, vip = msg.split("|")

            if vip != NODE_IP:
                print(f"[DISCOVERY] HELLO from {vip}")

                # send ACK back directly
                ack = f"ACK|{NODE_IP}"
                disc_sock.sendto(ack.encode(), addr)

        elif msg.startswith("ACK"):
            _, vip = msg.split("|")

            if state != "CONNECTED":
                print(f"[DISCOVERY] ACK received from {vip}")

                connected_peer = addr
                state = "CONNECTED"
                print("[STATE] CONNECTED")


# ---------------- CHAT / DATA ----------------
def send_chat():
    global state, connected_peer

    while True:
        if state == "CONNECTED":
            msg = input("Enter message: ")
            full = f"MSG|{NODE_IP}|{msg}"
            data_sock.sendto(full.encode(), connected_peer)
            print("[SENT]")
        else:
            time.sleep(1)


def listen_data():
    while True:
        data, addr = data_sock.recvfrom(2048)
        msg = data.decode()

        if msg.startswith("MSG"):
            _, sender, text = msg.split("|", 2)
            print(f"\n[CHAT] {sender}: {text}")


# ---------------- UTIL ----------------
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


# ---------------- MAIN ----------------
def main():
    print("[+] Starting Mesh v2 (Handshake + Chat)")

    tun = create_tun()
    setup_interface()

    print(f"[+] TUN ready: {TUN_NAME} → {NODE_IP}")

    threading.Thread(target=send_hello, daemon=True).start()
    threading.Thread(target=listen_discovery, daemon=True).start()
    threading.Thread(target=listen_data, daemon=True).start()
    threading.Thread(target=send_chat, daemon=True).start()

    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
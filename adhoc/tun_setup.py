import os
import fcntl
import struct
import subprocess
from config import TUN_NAME, TUN_IP, VIRTUAL_IP

TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

def create():
    tun = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack("16sH", TUN_NAME.encode(), IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun, TUNSETIFF, ifr)
    return tun

def setup():
    subprocess.run(["sudo", "ip", "link", "set", TUN_NAME, "up"], check=True)
    subprocess.run(["sudo", "ip", "addr", "add", TUN_IP, "dev", TUN_NAME], check=True)

def get_tun():
    tun = create()
    setup()
    print(f"[TUN] {TUN_NAME} ready with IP {VIRTUAL_IP}")
    return tun
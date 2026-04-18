import hashlib
import socket

# Generate a stable 10.0.0.x IP based on hostname
def generate_stable_ip():
    hostname = socket.gethostname()
    hash_digest = hashlib.sha256(hostname.encode()).digest()
    # Use the first byte of the hash to pick a number between 2 and 254
    last_octet = (hash_digest[0] % 253) + 2
    return f"10.0.0.{last_octet}"

DISCOVERY_PORT = 1001
DATA_PORT = 1002

MCAST_GROUP = "239.10.10.10"

HEARTBEAT_INTERVAL = 3
PEER_TIMEOUT = 12

TUN_NAME = "dataexsys_p"
VIRTUAL_IP = generate_stable_ip()
TUN_IP = f"{VIRTUAL_IP}/24"
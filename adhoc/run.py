import asyncio
from adhoc_setup import setup_system
from tun_setup import get_tun
from transport import tun_to_net, net_to_tun
from discovery import announce_loop, discovery_loop, cleanup
from chat import chat_input

# ---------------- MAIN ----------------
async def main():
    print("[BOOT] Mesh Stack Starting")

    # 1. system prep
    setup_system()

    # 2. TUN init
    print("[STEP 2] Initializing TUN")
    tun = get_tun()

    print("[OK] TUN Ready")

    # 3. start async mesh tasks
    print("[STEP 3] Starting runtime")

    await asyncio.gather(
        announce_loop(),     # discovery broadcast
        discovery_loop(),    # discovery receiver
        cleanup(),           # peer cleanup

        tun_to_net(tun),     # tun → udp
        net_to_tun(tun),     # udp → tun

        chat_input()         # CLI chat
    )

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Mesh stopped cleanly")
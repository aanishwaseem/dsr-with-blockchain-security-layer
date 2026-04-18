import subprocess

def run_cmd(cmd):
    print(f"[SETUP] {cmd}")
    subprocess.run(cmd, shell=True, check=False)

def setup_system():
    print("[STEP 1] Adhoc Setup")
    run_cmd("sudo sysctl -w net.ipv4.ip_forward=1")
    run_cmd("sudo ufw allow 1000/udp")
    run_cmd("sudo ufw allow 1001/udp")
    run_cmd("sudo ufw allow 1002/udp")

if __name__ == "__main__":
    setup_system()
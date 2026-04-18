# DSR Chat

A lightweight Python mesh runtime that combines peer discovery, UDP transport, a Linux TUN interface, and terminal chat for ad hoc node-to-node communication.

## Importance

This project demonstrates core ideas used in decentralized and infrastructure-less networking:

- Nodes can find each other automatically on a local network.
- Data forwarding can happen without a central server.
- Virtual IP-based communication can be built over raw UDP links.
- The same transport can carry both packet data (`TUN|...`) and application messages (`CHAT|...`).

It is useful for learning and prototyping mesh networking behavior, routing logic, and overlay communication.

## Motivation

Traditional communication often assumes stable infrastructure (routers, fixed paths, centralized services). In ad hoc environments, that assumption breaks.

This stack is motivated by the need to:

- Bootstrap communication quickly between nearby nodes.
- Keep discovery and data transport simple enough to inspect and extend.
- Build a reproducible base for experimenting with DSR-style ideas and custom routing logic.
- Validate concepts such as peer liveness, forwarding over virtual interfaces, and message exchange in one integrated runtime.

## Pathway (How It Works End-to-End)

1. System preparation enables IP forwarding and opens required UDP ports.
2. A TUN interface is created and assigned a stable virtual IP (`10.0.0.x`) derived from hostname.
3. Discovery loop multicasts periodic `HELLO|<virt_ip>` heartbeats to group `239.10.10.10:1001`.
4. Nodes receiving `HELLO` reply with `ACK|<virt_ip>` and update peer state.
5. Data plane runs on UDP port `1002`:
- TUN packets are sent as `TUN|<raw_packet>` to known peers.
- Chat messages are sent as `CHAT|<text>` to known peers.
6. Incoming `TUN|...` payloads are written back to the local TUN device.
7. Incoming `CHAT|...` payloads are printed in the CLI.
8. Cleanup loop removes stale peers after timeout.

## Architecture

The runtime is orchestrated by `run.py` and executes multiple async tasks in parallel:

- Discovery broadcast: announces local node presence.
- Discovery receiver: learns and refreshes peers.
- Peer cleanup: removes stale entries.
- TUN to network bridge: encapsulates local packets into UDP.
- Network to TUN bridge: decapsulates incoming packets.
- Chat input loop: sends user-entered messages.

### Logical Layers

- Control plane:
- `discovery.py` handles HELLO/ACK and peer table maintenance.
- Data plane:
- `transport.py` handles packet and chat transport over UDP.
- Interface layer:
- `tun_setup.py` creates and configures the TUN device.
- Bootstrap/system layer:
- `adhoc_setup.py` configures host networking prerequisites.
- App interaction layer:
- `chat.py` captures terminal chat input.
- Observability:
- `logger.py` prints timestamped runtime events.

## Project Structure

- `run.py`: Main async orchestrator and startup entrypoint.
- `config.py`: Ports, multicast group, timing constants, and stable virtual IP generation.
- `discovery.py`: Peer discovery, multicast socket handling, peer table (`PEERS`), and stale cleanup.
- `transport.py`: UDP data socket owner (`1002`), TUN encapsulation/decapsulation, and chat send/receive.
- `chat.py`: Async CLI input loop for outgoing chat messages.
- `tun_setup.py`: TUN device creation and IP assignment.
- `adhoc_setup.py`: IP forwarding + firewall port allowances.
- `logger.py`: Structured timestamped console logging.
- `run.sh`: Convenience launcher for setup + runtime lifecycle.
- `logs/`: Runtime log directory used by launcher scripts.

## Flow Details

### Discovery Flow

1. Node sends `HELLO|<virtual_ip>` every `HEARTBEAT_INTERVAL` seconds.
2. Receiver stores sender physical IP and virtual IP in `PEERS` with `last_seen` timestamp.
3. Receiver responds with `ACK|<virtual_ip>`.
4. ACK receiver also updates `PEERS`.
5. Cleanup task removes peers not seen within `PEER_TIMEOUT`.

### Data Flow (Packet)

1. OS writes an IP packet into local TUN.
2. `tun_to_net` reads it and wraps as `TUN|...`.
3. Payload is sent to each known peer on UDP `1002`.
4. Peer `net_to_tun` unwraps payload.
5. Raw packet is written into peer TUN, returning it to kernel networking stack.

### Chat Flow

1. User types a line in terminal (`chat>` prompt).
2. `chat.py` calls `send_chat` in `transport.py`.
3. Message is wrapped as `CHAT|<text>` and sent to all peers.
4. Receivers decode and print message immediately.

## Ports and Network Values

- Discovery UDP port: `1001`
- Data/chat UDP port: `1002`
- Multicast group: `239.10.10.10`
- Virtual subnet: `10.0.0.0/24`
- Default TUN name: `dataexsys_p`

## Run

Use root privileges because TUN setup and networking commands require elevated permissions.

```bash
sudo python3 run.py
```

You should see boot steps, then a `chat>` prompt.

## Stop

Press `Ctrl+C` for graceful shutdown.

## Notes

- This runtime expects Linux with `/dev/net/tun` available.
- Firewall configuration is attempted by `adhoc_setup.py` using `ufw` commands.
- If running multiple nodes, ensure they are on the same reachable network segment for multicast discovery.

#!/usr/bin/env python3
"""Start Hermes on ECS — v2: no prune, just start."""
import paramiko, time

HOST = "120.24.220.126"
USER = "root"
PASSWORD = "AHu$$HvkfD5v8+."

def run(ssh, cmd, desc="", timeout=300):
    if desc: print(f"\n>>> {desc}")
    print(f"    $ {cmd[:130]}{'...' if len(cmd) > 130 else ''}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    for line in out.split('\n')[-20:]:
        print(f"    {line}")
    if err:
        el = err.lower()
        if any(kw in el for kw in ['error', 'fail', 'denied', 'cannot']):
            print(f"    [err] {err[:300]}")
    return out, err

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print("Connected.")

# Kill stuck processes
run(c, "pkill -9 -f 'docker compose' 2>/dev/null; pkill -9 -f 'docker-compose' 2>/dev/null; echo done", "Killing stuck compose")

# Re-pull the image (through mirror)
print("\n>>> Re-pulling pre-built Hermes image...")
stdin, stdout, stderr = c.exec_command(
    "docker pull nousresearch/hermes-agent:latest 2>&1",
    timeout=600)
stdout.channel.recv_exit_status()
out = stdout.read().decode().strip()
if 'Downloaded' in out or 'Image is up to date' in out:
    print("    Image pulled successfully")
else:
    print(out[-500:])

# Create compose file using pre-built image
compose_yml = """services:
  gateway:
    image: nousresearch/hermes-agent:latest
    container_name: hermes
    restart: unless-stopped
    network_mode: host
    volumes:
      - /root/.hermes:/opt/data
    environment:
      - HERMES_UID=0
      - HERMES_GID=0
    command: ["gateway", "run"]

  dashboard:
    image: nousresearch/hermes-agent:latest
    container_name: hermes-dashboard
    restart: unless-stopped
    network_mode: host
    depends_on:
      - gateway
    volumes:
      - /root/.hermes:/opt/data
    environment:
      - HERMES_UID=0
      - HERMES_GID=0
    command: ["dashboard", "--host", "127.0.0.1", "--no-open"]
"""

run(c,
    f"cat > /root/hermes-agent/docker-compose.yml << 'EOF'\n{compose_yml}\nEOF",
    "Writing docker-compose.yml with pre-built image")

# Start!
run(c,
    "cd /root/hermes-agent && docker compose up -d 2>&1",
    "Starting Hermes containers")

time.sleep(8)

# Verify
print("\n" + "=" * 55)
run(c, "docker ps --format 'table {{.Names}}\t{{.Status}}'", "Container status")

# Wait a bit more and check gateway
if 'hermes' in run(c, "docker ps --format '{{.Names}}'", ""):
    run(c, "docker logs hermes --tail 15 2>&1", "Gateway logs")
    run(c, "cat /root/.hermes/gateway_state.json 2>/dev/null | python3 -m json.tool 2>/dev/null || cat /root/.hermes/gateway_state.json", "Gateway state")

print("\n" + "=" * 55)
print("Done!")
print("ssh root@120.24.220.126")
print("Dashboard: ssh -L 9119:localhost:9119 root@120.24.220.126")
c.close()

#!/usr/bin/env python3
"""Start Hermes on ECS using pre-built Docker Hub image."""
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

# Check image
run(c, "docker images | grep hermes", "Hermes image")

# Create a docker-compose.yml that uses the pre-built image
compose = """#
# Hermes Agent — Docker Compose (pre-built image from Docker Hub)
#
services:
  gateway:
    image: nousresearch/hermes-agent:latest
    container_name: hermes
    restart: unless-stopped
    network_mode: host
    volumes:
      - /root/.hermes:/opt/data
    environment:
      - HERMES_UID=${HERMES_UID:-10000}
      - HERMES_GID=${HERMES_GID:-10000}
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
      - HERMES_UID=${HERMES_UID:-10000}
      - HERMES_GID=${HERMES_GID:-10000}
    command: ["dashboard", "--host", "127.0.0.1", "--no-open"]
"""

run(c,
    f"cat > /root/hermes-agent/docker-compose.yml << 'COMPOSE_EOF'\n{compose}\nCOMPOSE_EOF",
    "Creating docker-compose.yml with pre-built image")

# Clean up failed builds
run(c, "docker system prune -af 2>&1 | tail -3", "Cleaning up failed builds")

# Start!
print("\n>>> Starting Hermes containers")
stdin, stdout, stderr = c.exec_command(
    "cd /root/hermes-agent && HERMES_UID=0 HERMES_GID=0 docker compose up -d 2>&1",
    timeout=120)
stdout.channel.recv_exit_status()
out = stdout.read().decode().strip()
print(out)

time.sleep(8)

# Verify
print("\n" + "=" * 55)
run(c, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'", "Container status")
run(c, "docker logs hermes --tail 20 2>&1", "Gateway logs")
run(c, "cat /root/.hermes/gateway_state.json 2>/dev/null", "Gateway state")

# systemd
unit = """[Unit]
Description=Hermes Agent
Requires=docker.service
After=docker.service
[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/root/hermes-agent
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
StandardOutput=journal
StandardError=journal
[Install]
WantedBy=multi-user.target
"""
run(c,
    f"cat > /etc/systemd/system/hermes-agent.service << 'EOF'\n{unit}\nEOF",
    "Updating systemd service")
run(c, "systemctl daemon-reload && systemctl enable hermes-agent.service 2>&1", "Enabling boot auto-start")

print("\n" + "=" * 55)
print("Done! ssh root@120.24.220.126")
print("Dashboard: ssh -L 9119:localhost:9119 root@120.24.220.126")
c.close()

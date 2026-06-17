#!/usr/bin/env python3
"""Try pulling pre-built Hermes image via Aliyun mirror."""
import paramiko

HOST = "120.24.220.126"
USER = "root"
PASSWORD = "AHu$$HvkfD5v8+."

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print("Connected.\n")

def run(cmd, desc="", timeout=120):
    print(f"=== {desc} ===")
    stdin, o, e = c.exec_command(cmd, timeout=timeout)
    o.channel.recv_exit_status()
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    print(out[-600:] if len(out) > 600 else (out or "(empty)"))
    if err:
        for kw in ['error', 'fail', 'denied', 'not found']:
            if kw in err.lower():
                print(f"[err] {err[:300]}")
                break
    print()
    return out

# Try to find pre-built Hermes image on Docker Hub via mirror
run("docker search nousresearch/hermes-agent 2>&1", "Search for Hermes on Docker Hub")
run("docker pull nousresearch/hermes-agent:latest 2>&1", "Pull nousresearch/hermes-agent:latest")

# Also check docker-compose.yml for the image name
run("grep -E 'image:|build:' /root/hermes-agent/docker-compose.yml", "docker-compose.yml image config")
run("grep -E 'image:|build:' /root/hermes-agent/docker-compose.windows.yml", "docker-compose.windows.yml")

c.close()

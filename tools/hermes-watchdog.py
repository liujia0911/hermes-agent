#!/usr/bin/env python3
"""
Hermes Gateway Watchdog — 10-minute health check & auto-repair.
Monitors container health, gateway state, Feishu connection, permissions, memory.
Deploys to: /root/hermes-watchdog.py on ECS
Cron: */10 * * * * /root/hermes-watchdog.py >> /root/hermes-watchdog.log 2>&1
"""
import subprocess, json, os, time
from datetime import datetime

DATA_DIR = "/root/.hermes"
PROFILES = ["default", "xiaoao", "xiaoke"]

def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 124
    except Exception as e:
        return "", str(e), 1

def dexec(cmd):
    return run(f"docker exec hermes {cmd}")

def dlogs(pattern, tail=50):
    out, _, _ = run(f"docker logs hermes --tail {tail} 2>&1")
    if pattern:
        return "\n".join(line for line in out.split("\n") if pattern.lower() in line.lower())
    return out

def check_container():
    out, _, code = run("docker ps --format '{{.Names}}' 2>&1 | grep -q '^hermes$' && echo OK")
    if "OK" not in out:
        log("ERROR: Container dead, restarting...")
        run("docker start hermes")
        time.sleep(8)
        out, _, code = run("docker ps | grep -q hermes && echo OK || echo FAIL")
        if "FAIL" in out:
            log("FATAL: compose up...")
            run("cd /root/hermes-agent && docker compose up -d")
            time.sleep(15)
        return False
    return True

def s6_stat(profile):
    out, _, _ = dexec(f"/command/s6-svstat /run/service/gateway-{profile}")
    return out

def s6_restart(profile):
    log(f"  Restarting gateway-{profile}...")
    dexec(f"/command/s6-svc -r /run/service/gateway-{profile}")
    time.sleep(5)

def gateway_state(profile):
    path = f"{DATA_DIR}/profiles/{profile}/gateway_state.json"
    try:
        with open(path) as f:
            d = json.load(f)
        return d.get("gateway_state","?"), d.get("platforms",{}).get("feishu",{}).get("state","none"), d.get("pid",0)
    except Exception:
        return "missing", "none", 0

def fix_permissions():
    out = dlogs("Permission")
    if out and "denied" in out:
        log("Fix: permission errors, chown 10000:10000...")
        os.system(f"chown -R 10000:10000 {DATA_DIR}/ 2>/dev/null")
        os.system(f"find {DATA_DIR} -name '.env' -exec chmod 600 {{}} + 2>/dev/null")
        os.system(f"find {DATA_DIR} -name '*.yaml' -exec chmod 644 {{}} + 2>/dev/null")
        return True
    return False

def check_memory():
    out, _, _ = run("free | awk '/Mem:/{printf \"%d\", ($3/$2)*100}'")
    try:
        pct = int(out)
        if pct > 90:
            log(f"Memory {pct}%, checking swap...")
            swap, _, _ = run("free | awk '/Swap:/{print $2}'")
            if swap == "0":
                log("Re-enabling swap...")
                os.system("swapon /swapfile 2>/dev/null")
        return pct
    except: return -1

def clean_stale():
    out, _, _ = run("ps aux | grep 's6-log.*gateways' | grep -v grep | awk '{print $2}'")
    if out:
        for pid in out.split():
            log(f"Killing stale s6-log PID={pid}")
            os.system(f"kill -9 {pid} 2>/dev/null")
    os.system(f"find {DATA_DIR}/logs/gateways/ -name 'lock' -mmin +30 -delete 2>/dev/null")

# ═══════════════════════════════════════════════════════════
def main():
    log("="*50)
    log("Watchdog check")

    issues = fixes = 0

    if not check_container():
        issues += 1; fixes += 1
        return

    mem = check_memory()
    log(f"Memory: {mem}% | Swap: active")

    clean_stale()

    if fix_permissions():
        fixes += 1

    for p in PROFILES:
        state, feishu, pid = gateway_state(p)
        s6 = s6_stat(p)

        if state != "running":
            log(f"ISSUE: {p} state={state} feishu={feishu}")
            issues += 1
            s6_restart(p)
            state2, feishu2, _ = gateway_state(p)
            if state2 == "running":
                log(f"  FIXED: {p} running, feishu={feishu2}")
                fixes += 1
            else:
                log(f"  FAILED: {p} state={state2}, full container restart...")
                run("docker restart hermes")
                fixes += 1
                break
        elif feishu != "connected":
            log(f"ISSUE: {p} running but feishu={feishu}")
            issues += 1
            s6_restart(p)
            fixes += 1
        else:
            log(f"OK: {p} running feishu=connected pid={pid}")

    log(f"Done: {issues} issues, {fixes} fixes")

if __name__ == "__main__":
    main()

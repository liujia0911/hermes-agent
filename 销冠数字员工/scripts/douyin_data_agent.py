"""douyin_data_agent.py - 数据Agent：抓取抖音数据并发送播报到飞书群"""
import subprocess, json, os, sys

SCRIPTS_DIR = r"E:\hermes\销冠数字员工\scripts"
NODE_EXE = r"C:\Program Files\nodejs\node.exe"
LARK_CLI = r"C:\Users\Administrator\AppData\Roaming\npm\lark-cli.cmd"
HERMES_HOME = r"C:\Users\Administrator\.hermes"
OPS_GROUP = "oc_a5fa23511a0027a1b8568c6daf86b3b6"

def fetch_data():
    """Run the Node.js fetch script and return parsed data."""
    result = subprocess.run(
        [NODE_EXE, "douyin_fetch_v4.js"],
        capture_output=True, text=True, timeout=90,
        cwd=SCRIPTS_DIR
    )
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            try:
                return json.loads(line)
            except:
                continue
    print(f"Fetch failed: {result.stderr[:200]}", file=sys.stderr)
    return None

def format_report(data):
    """Format the data report for Feishu."""
    if not data:
        return """📊 销冠数据日报
━━━━━━━━━━━━━━━━━━━━
⚠ 数据抓取失败，请检查抖音登录状态。
手动检查：https://creator.douyin.com/"""
    
    account = data.get('account', '未知')
    douyin_id = data.get('douyinId', '')
    fans = data.get('fans', '0')
    likes = data.get('likes', '0')
    has_videos = data.get('hasVideos', False)
    
    report = f"""📊 销冠数据日报
━━━━━━━━━━━━━━━━━━━━
{account}
抖音号：{douyin_id}

📈 账号概览：
  粉丝：{fans}  获赞：{likes}"""
    
    if not has_videos:
        report += "\n\n⚠ 暂无作品数据。发布首条视频后数据自动更新。"
    else:
        report += f"\n\n📹 最新作品数据：（待接入详细API）"
    
    report += f"\n\n🕐 统计周期：近7日 | 每日12:00更新"
    report += f"\n@小马 | 运营数据组 · 自动播报"
    
    return report

def send_report(report):
    """Send report to 运营数据组."""
    result = subprocess.run(
        [LARK_CLI, "im", "+messages-send",
         "--chat-id", OPS_GROUP,
         "--text", report,
         "--as", "bot", "--format", "json"],
        capture_output=True, text=True, timeout=15,
        env={**os.environ, "HERMES_HOME": HERMES_HOME}
    )
    if result.returncode == 0:
        print("Report sent OK")
        return True
    else:
        print(f"Send failed: {result.stderr[:200]}", file=sys.stderr)
        return False

def main():
    data = fetch_data()
    report = format_report(data)
    print(report)
    send_report(report)

if __name__ == "__main__":
    main()

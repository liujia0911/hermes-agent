# Hybrid Vision Pipeline: DeepSeek + Gemini 3 Flash + cua-driver

The full "看图-决策-执行-验证" loop split across two models. Validated 2026-06-22.

## Why

DeepSeek V4 Pro is the primary model (Chinese text, fast, cheap) but has no vision. Gemini 3 Flash has vision (free tier, 1500 req/day) and ranks #20 on Arena (above DeepSeek's #38). This pipeline combines both without switching Hermes profiles.

## Complete Pipeline

```
1. cua-driver captures screenshot + AX tree
2. Gemini analyzes screenshot → returns element indices + action plan
3. DeepSeek executes clicks/keys via cua-driver MCP
4. cua-driver re-captures for verification
5. Gemini confirms result
```

## Step-by-Step Recipe

### 1. Capture Screenshot + AX Tree

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_window_state","arguments":{"pid":PID,"window_id":WID}}}' \
  | cua-driver mcp \
  | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
for c in d['result']['content']:
    if c.get('type') == 'image':
        with open('/tmp/som-screenshot-b64.txt','w') as f:
            f.write(c['data'])
        print(f'Screenshot: {len(c[\"data\"])} chars base64')
    elif c.get('type') == 'text':
        print(c['text'][:2000])
"
```

### 2. Send to Gemini for Analysis

Use the script `scripts/hybrid_vision_analyze.py`:

```bash
python3 /path/to/scripts/hybrid_vision_analyze.py \
  --image /tmp/som-screenshot-b64.txt \
  --prompt "点击'新对话'按钮，返回元素索引"
```

Or inline:

```python
import yaml, urllib.request, json, base64

with open('/Users/xinguan/.hermes/profiles/vision/config.yaml') as f:
    config = yaml.safe_load(f)

key = config['inference']['api_key']
model = config['model']  # gemini-3-flash-preview
base = config['inference']['base_url']

with open('/tmp/som-screenshot-b64.txt') as f:
    img_b64 = f.read()

prompt = """你是桌面自动化助手。分析截图和AX元素树，返回操作指令。
AX元素树: [2] 新对话, [5] 搜索, [57] 设置, [78] 输入框
任务: 点击新对话按钮
只返回: {"element_index": 2, "action": "click"}"""

body = {
    "contents": [{"parts": [
        {"text": prompt},
        {"inlineData": {"mimeType": "image/png", "data": img_b64}}
    ]}]
}

url = f'{base}/models/{model}:generateContent?key={key}'
req = urllib.request.Request(url, data=json.dumps(body).encode(),
    headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read())
print(data['candidates'][0]['content']['parts'][0]['text'])
```

### 3. Execute Based on Gemini's Output

```bash
echo '{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"click","arguments":{"pid":51549,"window_id":5264,"element_index":2}}}' \
  | cua-driver mcp
```

### 4. Verify with Gemini

Re-capture (step 1) → ask Gemini "界面是否变化？操作是否成功？" (step 2).

## Validated Results (Codex app, 2026-06-22)

| Step | Action | Result |
|------|--------|--------|
| Capture | Screenshot Codex window | ✅ 124KB base64 |
| Analyze | Gemini: "3个对话，点元素25" | ✅ Accurate |
| Execute | Click [25] "协助做电商" | ✅ AXPress OK |
| Verify | Gemini: "对话已成功打开" | ✅ Confirmed |

## Gemini Prompt Design Tips

- **Always include AX tree context** in the prompt — Gemini needs element index numbers to return actionable output
- **Ask for JSON format**: `{"element_index": N, "action": "click|type|press"}`
- **Be specific about the task**: "点击元素25进入对话" not "帮我打开对话"
- **Keep prompts short**: Gemini 3 Flash is fast but prompt length adds latency (~2-3s per analysis)

## Limitations

- **Latency**: Each round-trip takes ~3-5s (capture + API call). Not suitable for real-time interactions.
- **No SOM overlays**: cua-driver screenshots don't have numbered element overlays like Hermes `som` mode. Gemini relies on AX tree context + visual matching.
- **API costs**: Free tier sufficient (1500 req/day), but Pro models would add cost.
- **Python bolierplate**: Current approach needs small Python scripts. Future: could be integrated as a Hermes tool plugin.

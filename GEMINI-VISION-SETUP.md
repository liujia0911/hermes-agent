# Gemini 视觉配置指南

> 昕冠科技 · 三台机器通过 GitHub 共享。Gemini 用作 Hermes auxiliary vision 后端。
> DeepSeek（当前主力模型）不支持原生图片分析，所有 vision_analyze 调用必须走 Gemini。

## 前置条件

- Google AI Studio API Key（新版以 `AQ.` 开头）
- 获取地址：https://aistudio.google.com/app/apikey

## 快速配置（每台新机器执行一次）

```bash
# 1. 写入 Gemini Key 到 .env（新版 Key 走原生 Gemini API）
echo 'GOOGLE_API_KEY=*** >> ~/.hermes/.env

# 2. 配置 auxiliary vision 走 Google Gemini 原生端点
hermes config set auxiliary.vision.provider google
hermes config set auxiliary.vision.model gemini-2.5-flash

# 3. 重开会话生效（CLI 里输入 /reset）
```

## 验证

```bash
hermes chat -q "看这张截图描述内容" --image /tmp/test.png
```

返回文字分析而非 `[Unsupported Image]` 即成功。

## 备选：自定义端点（如果 Google 原生 API 不通）

在 `config.yaml` 中添加：

```yaml
custom_providers:
  gemini-vision:
    api_key_env: GOOGLE_API_KEY
    base_url: https://generativelanguage.googleapis.com/v1beta
    api_mode: gemini
```

然后：

```bash
hermes config set auxiliary.vision.provider custom:gemini-vision
hermes config set auxiliary.vision.model gemini-2.5-flash
```

## 扩展到其他 auxiliary 任务

```bash
hermes config set auxiliary.web_extract.provider google
hermes config set auxiliary.web_extract.model gemini-2.5-flash
hermes config set auxiliary.compression.provider google
hermes config set auxiliary.compression.model gemini-2.5-flash
```

## 关键坑

1. 新版 Key（AQ.开头）不能走 OpenAI 兼容端点 `/v1beta/openai`，必须走原生 `/v1beta`。provider 用 `google` 不用 `openai_compat`。
2. Gemini 2.5 Flash 有免费 tier，日常 vision 够用。
3. Key 本身不入 Git（`.gitignore` 已排除 `.env`），每台机器手动写入一次即可。`auxiliary.vision.*` 配置已写在 `config.yaml` 里，git pull 后自动生效。

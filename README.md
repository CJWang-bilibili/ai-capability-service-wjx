# AI 模型能力统一调用服务

一个 production-ready 的后端服务，提供统一的 API 接口来调用 AI 模型能力。

## 功能特性

- `POST /v1/capabilities/run` — 统一能力调度接口
- `text_summary` — 文本摘要，支持自定义最大长度
- `sentiment_analysis` — 情感分析，返回情感分类、置信度评分及解释（加分项）
- 接入真实 Claude API（claude-opus-4-6），未配置 API Key 时自动降级为 Mock 模式
- 结构化日志，含 `request_id` 追踪与 `elapsed_ms` 耗时统计
- `/healthz` 健康检查端点
- 9 个自动化测试，无需 API Key 即可运行

---

## 快速启动

### 第一步：安装依赖

```bash
pip install -r requirements.txt
```

### 第二步：配置环境变量

```bash
cp .env.example .env
```

用编辑器打开 `.env` 文件，填入你的 Claude API Key（详细获取步骤见下方）：

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
```

> **没有 API Key？** 留空即可——服务会自动进入 **Mock 模式**，返回预设的模拟响应。
> 所有接口仍然正常工作，适合本地开发和接口调试。

### 第三步：启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问 `http://localhost:8000`。

启动日志示例：
```
INFO  Service starting — mode: LIVE (Claude API)
INFO  Available capabilities: ['sentiment_analysis', 'text_summary']
```

---

## Claude API Key 获取与配置

### 1. 注册 Anthropic 账号

访问 [console.anthropic.com](https://console.anthropic.com)，点击右上角 **Sign Up** 注册账号（支持 Google 登录）。

### 2. 创建 API Key

1. 登录后，点击左侧导航栏的 **API Keys**
2. 点击右上角 **Create Key** 按钮
3. 为 Key 起一个名称，例如 `ai-capability-service`
4. 点击 **Create Key**，立即复制生成的 Key（**只显示一次，关闭后无法再查看**）

Key 格式示例：
```
sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-xxxxxxxx
```

### 3. 配置到项目

将复制好的 Key 填入 `.env` 文件：

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-你的真实Key
```

### 4. 验证配置是否生效

启动服务后，观察日志输出：

```
# 配置成功（真实调用）
INFO  Service starting — mode: LIVE (Claude API)

# 未配置或 Key 格式错误（模拟模式）
INFO  Service starting — mode: MOCK (no real API calls)
```

或调用健康检查接口：

```bash
curl http://localhost:8000/healthz
```

返回 `"mode": "live"` 表示 API Key 已生效：

```json
{
  "status": "ok",
  "mode": "live",
  "capabilities": ["sentiment_analysis", "text_summary"]
}
```

### 5. 费用说明

| 模型 | 输入价格 | 输出价格 |
|---|---|---|
| claude-opus-4-6 | $5.00 / 百万 tokens | $25.00 / 百万 tokens |

> 本服务默认使用 **claude-opus-4-6**。一次典型的文本摘要请求约消耗 200~500 tokens，费用约 $0.001。
> 详见 [Anthropic 定价页面](https://www.anthropic.com/pricing)。

### 常见问题

| 问题 | 原因 | 解决方法 |
|---|---|---|
| 服务仍在 Mock 模式 | Key 未以 `sk-` 开头或为空 | 检查 `.env` 文件格式，确认无多余空格 |
| `AUTH_ERROR` | API Key 无效或已失效 | 在 Console 重新创建 Key |
| `RATE_LIMIT` | 请求频率超限 | 稍后重试，或升级账号套餐 |

---

## 示例请求

### text_summary（文本摘要）

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "text_summary",
    "input": {
      "text": "人工智能是指计算机系统执行通常需要人类智能才能完成的任务的能力，例如视觉感知、语音识别、决策制定和语言翻译。近年来，随着深度学习技术的突破，人工智能在医疗、金融、教育等多个领域取得了显著进展。",
      "max_length": 80
    },
    "request_id": "req-001"
  }'
```

成功响应：

```json
{
  "ok": true,
  "data": {
    "result": "人工智能使计算机完成视觉、语音等智能任务，近年随深度学习突破在多领域取得显著进展。"
  },
  "meta": {
    "request_id": "req-001",
    "capability": "text_summary",
    "elapsed_ms": 843
  }
}
```

### sentiment_analysis（情感分析）

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "sentiment_analysis",
    "input": {
      "text": "这个产品真的太棒了！用了之后完全超出预期，强烈推荐给大家。"
    },
    "request_id": "req-002"
  }'
```

成功响应：

```json
{
  "ok": true,
  "data": {
    "result": {
      "sentiment": "positive",
      "score": 0.97,
      "explanation": "文本表达了强烈的满意度和热情推荐，情感非常积极。"
    }
  },
  "meta": {
    "request_id": "req-002",
    "capability": "sentiment_analysis",
    "elapsed_ms": 612
  }
}
```

### 错误响应示例

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{"capability": "text_summary", "input": {}}'
```

```json
{
  "ok": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "'text' field is required and must be a non-empty string",
    "details": {}
  },
  "meta": {
    "request_id": "...",
    "capability": "text_summary",
    "elapsed_ms": 1
  }
}
```

### 调用不存在的 capability

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{"capability": "unknown_cap", "input": {}}'
```

```json
{
  "ok": false,
  "error": {
    "code": "UNKNOWN_CAPABILITY",
    "message": "Unknown capability 'unknown_cap'. Available: ['sentiment_analysis', 'text_summary']",
    "details": {}
  },
  "meta": {
    "request_id": "...",
    "capability": "unknown_cap",
    "elapsed_ms": 0
  }
}
```

### 健康检查

```bash
curl http://localhost:8000/healthz
```

---

## 运行测试

测试在 Mock 模式下运行，**无需配置 API Key**：

```bash
pytest
```

期望输出：

```
collected 9 items

tests/test_api.py::test_healthz PASSED
tests/test_api.py::test_text_summary_success PASSED
tests/test_api.py::test_text_summary_auto_request_id PASSED
tests/test_api.py::test_text_summary_missing_text PASSED
tests/test_api.py::test_text_summary_empty_text PASSED
tests/test_api.py::test_sentiment_analysis_success PASSED
tests/test_api.py::test_sentiment_analysis_missing_text PASSED
tests/test_api.py::test_unknown_capability PASSED
tests/test_api.py::test_error_response_has_meta PASSED

9 passed in 0.45s
```

---

## 项目结构

```
ai-capability-service-wjx/
├── app/
│   ├── main.py                  # FastAPI 应用、路由、日志配置
│   ├── config.py                # 配置项（读取 .env）
│   ├── models.py                # Pydantic 请求/响应模型
│   └── capabilities/
│       ├── base.py              # 抽象基类 + CapabilityError
│       ├── registry.py          # Capability 注册表
│       ├── text_summary.py      # 文本摘要实现
│       └── sentiment_analysis.py # 情感分析实现
├── tests/
│   └── test_api.py              # API 测试（Mock 模式）
├── .env.example                 # 环境变量模板
├── requirements.txt             # Python 依赖
└── README.md
```

---

## API 接口文档

### `POST /v1/capabilities/run`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `capability` | string | 是 | 调用的能力名称，见下方支持列表 |
| `input` | object | 是 | 能力对应的输入参数 |
| `request_id` | string | 否 | 请求追踪 ID，不填则自动生成 UUID |

**支持的 capability：**

#### `text_summary` — 文本摘要

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `text` | string | 是 | 待摘要的原始文本 |
| `max_length` | integer | 否 | 摘要最大字符数，默认 150 |

#### `sentiment_analysis` — 情感分析

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `text` | string | 是 | 待分析的文本 |

**返回的 sentiment 取值：** `positive`（正面）/ `negative`（负面）/ `neutral`（中性）

**错误码说明：**

| 错误码 | HTTP 状态 | 含义 |
|---|---|---|
| `INVALID_INPUT` | 400 | 请求参数缺失或格式错误 |
| `UNKNOWN_CAPABILITY` | 404 | 不支持的 capability 名称 |
| `AUTH_ERROR` | 400 | API Key 无效 |
| `RATE_LIMIT` | 400 | 触发上游限流 |
| `UPSTREAM_ERROR` | 400 | 上游 API 异常 |
| `INTERNAL_ERROR` | 500 | 服务内部错误 |

---

## 环境变量说明

| 变量名 | 默认值 | 说明 |
|---|---|---|
| `ANTHROPIC_API_KEY` | 空 | Claude API Key，留空则进入 Mock 模式 |
| `HOST` | `0.0.0.0` | 服务监听地址 |
| `PORT` | `8000` | 服务监听端口 |
| `LOG_LEVEL` | `INFO` | 日志级别：`DEBUG` / `INFO` / `WARNING` / `ERROR` |

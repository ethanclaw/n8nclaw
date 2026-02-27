# n8n + Telegram + Claude Code 集成

通过 Telegram 触发 n8n 工作流，调用宿主机上的 Claude Code 来写代码。

## 架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Telegram      │────▶│   n8n (Docker)  │────▶│  FastAPI Server │
│   User          │     │   Workflow     │     │  (Host Machine) │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │ Claude Code CLI │
                                                 │ (pnpm global)   │
                                                 └─────────────────┘
```

## 组件

### 1. FastAPI Server (`server/main.py`)

运行在宿主机的 HTTP 服务，接收 n8n 的请求并调用 Claude Code CLI。

- **端口**: 8080
- **端点**:
  - `POST /claude` - 执行 Claude 命令
  - `GET /health` - 健康检查

### 2. n8n Workflow (`n8n-workflow.json`)

n8n 工作流定义，包含：
- Telegram Trigger: 接收用户消息
- HTTP Request: 调用 FastAPI
- Telegram: 发送回复

## 安装

### 1. 安装 Python 依赖

```bash
cd server
pip install -r requirements.txt
# 或使用 pipx
pipx install fastapi uvicorn pydantic
```

### 2. 启动 FastAPI 服务

```bash
cd server
python3 main.py
```

服务将在 `http://localhost:8080` 启动。

### 3. 配置 n8n

1. 打开 n8n (http://localhost:5678)
2. 导入 `n8n-workflow.json`
3. 配置 Telegram Trigger:
   - 从 @BotFather 获取 Bot Token
   - 在 Trigger 节点设置 Token
   - 点击 "Create Webhook" 激活

### 4. 端口映射（如果从 Docker 访问）

n8n 容器需要访问宿主机服务，使用：
- Mac: `http://host.docker.internal:8080`
- Linux: `http://172.17.0.1:8080`

## 使用

1. 向 Telegram Bot 发送消息
2. n8n 接收消息并转发给 FastAPI
3. FastAPI 调用 Claude Code 执行
4. 结果通过 Telegram 返回

示例：
```
用户: 帮我写一个 hello world 的 Python 函数
Bot: 当然可以！以下是 Python hello world 示例：
...
```

## API

### POST /claude

执行 Claude Code 命令。

**请求体**:
```json
{
  "prompt": "你的指令",
  "project_path": "/可选/项目路径"
}
```

**响应**:
```json
{
  "success": true,
  "output": "Claude 的回复",
  "error": null
}
```

### GET /health

健康检查。

**响应**:
```json
{
  "status": "ok"
}
```

## 代码说明

### server/main.py

```python
# Claude CLI 路径
CLAUDE_BIN = "/Users/ethan/Library/pnpm/claude"

# 默认工作目录
WORK_DIR = "/Users/ethan/Projects"

def run_claude(prompt, project_path):
    # 移除 CLAUDECODE 环境变量（避免嵌套会话）
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    # 执行 claude --print -p "prompt"
    result = subprocess.run(
        [CLAUDE_BIN, "--print", "-p", prompt],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=120,
        env=env
    )
    return result.stdout, result.stderr
```

### 关键技术点

1. **嵌套会话处理**: Claude Code 检测到在自身会话内运行会报错，需要移除 `CLAUDECODE` 环境变量
2. **超时设置**: 120 秒超时，防止长时间运行的命令
3. **工作目录**: 支持指定项目路径，否则使用默认目录

## 扩展

可以扩展的功能：
- 代码文件读写操作
- Git 操作（commit, push）
- 项目结构分析
- 多模态支持（代码截图）

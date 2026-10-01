# ShortLink

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.12-blue">
  <img alt="FastAPI" src="https://img.shields.io/badge/fastapi-latest-009688">
  <img alt="SQLAlchemy" src="https://img.shields.io/badge/sqlalchemy-latest-d71f00">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/database-postgresql%20%7C%20sqlite-336791">
  <img alt="Docker" src="https://img.shields.io/badge/deploy-docker%20%7C%20render-2496ed">
</p>

ShortLink 是一个基于 FastAPI 实现的短链接服务。项目提供创建短链接、短链接跳转、访问次数统计等功能，数据可以保存到本地 SQLite，也可以通过环境变量切换到云端 PostgreSQL 数据库。项目已配置 Dockerfile 和 Render 所需的启动方式，适合直接部署到云端运行。

## 功能特性

- **创建短链接**：`POST /shorten` 接收原始 URL，生成 6 位随机短码，并返回完整短链接。
- **短链接跳转**：`GET /{code}` 根据短码查找原始 URL，并返回 `307` 重定向。
- **访问统计**：每次短链接跳转都会将点击次数加 1。
- **统计接口**：`GET /stats/{code}` 返回短码、原始 URL、点击次数和创建时间。
- **URL 校验**：使用 Pydantic 的 `HttpUrl` 校验输入 URL，非法 URL 会返回 `422`。
- **数据库兼容**：本地默认使用 SQLite；上线时可通过 `DATABASE_URL` 使用 PostgreSQL。
- **云端部署**：已提供 `requirements.txt`、`Dockerfile`、`.dockerignore`，可用于 Render 的 Docker 部署。
- **自动建表**：服务启动时会自动创建 `links` 表。

## 项目结构

```text
.
├── main.py              # FastAPI 应用、数据库初始化、短链接接口
├── test_main.py         # 基于 pytest 和 TestClient 的接口测试
├── requirements.txt     # 线上运行依赖
├── Dockerfile           # Docker 镜像构建和启动配置
├── .gitignore           # Git 忽略规则
├── .dockerignore        # Docker 构建忽略规则
└── README.md            # 项目说明文档
```

## 快速开始

### 环境要求

- Python 3.12
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

如果需要运行测试，还需要额外安装测试依赖：

```bash
pip install pytest httpx
```

### 本地启动

```bash
uvicorn main:app --reload
```

启动后访问：

```text
http://127.0.0.1:8000
```

### 创建短链接

```bash
curl -X POST "http://127.0.0.1:8000/shorten" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.python.org"}'
```

返回示例：

```json
{
  "code": "Ab12Cd",
  "short_url": "http://127.0.0.1:8000/Ab12Cd"
}
```

### 访问统计

```bash
curl "http://127.0.0.1:8000/stats/Ab12Cd"
```

返回示例：

```json
{
  "code": "Ab12Cd",
  "url": "https://www.python.org/",
  "clicks": 3,
  "created_at": "2026-10-01 12:00:00"
}
```

### 运行测试

```bash
pytest
```

## 环境变量

| 变量名 | 说明 | 默认值 |
| --- | --- | --- |
| `DATABASE_URL` | 数据库连接地址。本地可使用 SQLite，上线可使用 PostgreSQL / Neon 地址。 | `sqlite:///shortlink.db` |
| `BASE_URL` | 生成短链接时使用的站点根地址。上线后应改为 Render 分配的域名或自定义域名。 | `http://127.0.0.1:8000` |
| `PORT` | 服务监听端口，Render 会自动注入。 | `8000` |

如果 `DATABASE_URL` 使用 `postgresql://` 开头，程序会自动转换为 SQLAlchemy 使用的 `postgresql+psycopg://`。

## Docker 部署

```bash
docker build -t shortlink .
docker run -p 8000:8000 shortlink
```

`Dockerfile` 使用 `python:3.12-slim` 作为基础镜像，安装 `requirements.txt` 中的依赖，并通过下面的命令启动服务：

```dockerfile
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

其中 `--host 0.0.0.0` 用于接受容器外部请求，`${PORT:-8000}` 会优先读取 Render 提供的 `PORT` 环境变量，没有时使用 `8000`。

## Render 部署说明

部署到 Render 时建议使用 Docker 部署方式，并配置环境变量：

- `DATABASE_URL`：云端 PostgreSQL 数据库连接地址。
- `BASE_URL`：Render 服务域名，例如 `https://your-service-name.onrender.com`。

Render 会自动提供 `PORT` 环境变量，不需要手动填写。

## 当前状态

项目已完成短链接服务的核心流程：

- 创建短链接
- 根据短码跳转
- 统计访问次数
- 本地 SQLite 存储
- 云端 PostgreSQL 存储
- Docker / Render 部署配置
- 基础接口测试

后续可继续完善：

- 增加首页或简单前端页面，方便在浏览器中创建短链接。
- 增加自定义短码功能。
- 增加短链接过期时间。
- 增加管理接口或删除接口。
- 为 `/health` 添加健康检查接口，方便 Render 监控服务状态。

## 数据和敏感信息

虚拟环境、本地缓存和本地数据库文件已通过 `.gitignore` 排除，不应提交到仓库：

```text
.venv/
__pycache__/
.pytest_cache/
*.db
```

Docker 构建时也会通过 `.dockerignore` 排除这些文件，并额外排除 `.git/`，避免把 Git 历史打包进镜像。

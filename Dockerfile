# 以官方的 Python 3.12 精简版作为基础环境
FROM python:3.12-slim
# 之后的命令都在容器里的 /app 文件夹执行
WORKDIR /app
# 先只复制依赖清单并安装，这样代码改了而依赖没变时，可以复用这一步的缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 再复制其余的代码
COPY . .
# 启动服务。Render 会通过 PORT 环境变量告诉程序该监听哪个端口
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

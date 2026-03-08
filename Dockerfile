# 使用轻量的 python 3.11 slim 镜像构建 HuggingFace Spaces 的运行环境
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装必要的系统库 (可能被 chroma 等组件依赖)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖定义
COPY requirements.txt .

# 优化 Docker 层缓存，提升 HF 环境的 rebuilding 速度
RUN pip install --no-cache-dir -r requirements.txt

# 创建数据存储的持久化路径 (HF 默认利用 /data，我们在 memory_manager.py 中已通过环境预留适配)
ENV CHROMA_PERSIST_DIRECTORY=/data

# 暴露端口，HF Spaces 默认使用 7860
EXPOSE 7860

# 复制整个项目工程到镜像内部（包含 backend, frontend 的 dist 静态文件）
# 注意：在真实的 CI/CD 流程中，前端一般由 multi-stage 的 node 层构建。
# 为符合目前轻量架构设定，假设开发者已预先 npm run build 出静态代码。
COPY . .

# 通过 uvicorn 启动主应用，开启到 7860，允许外部所有的 host 访问以便代理映射
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]

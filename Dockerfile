# 使用一个官方的 Python 运行环境作为父镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器中
COPY . /app

# 安装 virtualenv
RUN pip install virtualenv

# 创建和激活虚拟环境，并安装依赖项
RUN virtualenv venv
RUN . venv/bin/activate && pip install -r requirements.txt

# 暴露 Flask 应用运行的端口
EXPOSE 5000

# 设置环境变量，告诉 Flask 在生产环境中运行
ENV FLASK_ENV=production

# 启动 Flask 应用
CMD ["bash", "-c", ". venv/bin/activate && gunicorn --bind 0.0.0.0:5000 main:app"]

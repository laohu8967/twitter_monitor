# 使用一个官方的 Python 运行环境作为父镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器中
COPY . /app

# 安装 virtualenv
RUN pip install virtualenv

# 创建和激活虚拟环境，并安装依赖项
RUN virtualenv venv && . venv/bin/activate && pip install -r requirements.txt

# 暴露 Flask 应用运行的端口
EXPOSE 5000

# 安装 Gunicorn
RUN . venv/bin/activate && pip install gunicorn

# 启动 Flask 应用
CMD ["bash", "-c", ". venv/bin/activate && gunicorn -w 4 -b 0.0.0.0:5000 main:app"]
CMD ["bash", "-c", ". venv/bin/activate && gunicorn -w 4 -b 0.0.0.0:5000 main:app --log-level=debug --access-logfile - --error-logfile -"]

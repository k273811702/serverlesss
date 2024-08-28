# 使用 Python 3.9 作为基础镜像
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 将本地目录复制到容器中
COPY ./solidate /app/solidate

# 安装依赖
RUN pip install requests
RUN pip install -U cos-python-sdk-v5 

# 设置 JAVA_HOME 环境变量
ENV JAVA_HOME /app/solidate/shieldClient_10058033/client_jdk/jdk-17.0.1

# 设置 PATH 环境变量，包含 JAVA_HOME/bin
ENV PATH $JAVA_HOME/bin:$PATH


# 设置 entrypoint 和 cmd
CMD ["python","/app/solidate/index.py"]

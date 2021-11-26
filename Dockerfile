FROM apache/airflow:2.2.1

USER root
ENV REPOSITRY="https://mirrors.aliyun.com/pypi/simple"  TRUST_HOST="mirrors.aliyun.com"
RUN cp /etc/apt/sources.list /etc/apt/sources.list.bak && sed -i "s@http://deb.debian.org@http://mirrors.aliyun.com@g" /etc/apt/sources.list && rm -Rf /var/lib/apt/lists/* && apt-get update
RUN apt-get install -y  --no-install-recommends  wget iputils-ping vim &&  apt-get autoremove -yqq --purge && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow

COPY requirements.txt .
RUN /usr/local/bin/python -m pip install  --no-cache-dir  --upgrade pip -i ${REPOSITRY} && pip install  --no-cache-dir  -r requirements.txt -i ${REPOSITRY}


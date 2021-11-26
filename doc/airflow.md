## airflow 
airflow 是一个可编程，调度和监控的工作流平台

### 架构图

单机
![单机](./images/单机.png)




集群
![集群](./images/集群.png)

DAG文件扫描变化
![DAG](./images/DAG.png)

**服务组件类型**

1. airflow-scheduler - 包含所有的任务和 DAG。决定任务的运行以及优先级等

2. airflow-webserver   -  web 服务器，提供图形界面。默认地址 http://localhost:8080

3. airflow-worker - 用来执行调度器下发的任务

4. airflow-init - 初始化服务（执行完安装就会结束）

5. flower -  主要用来监控和管理  Celery 集群，默认地址 http://localhost:5555.

6. postgres - 数据库，可为 mysql，sqlite 等。存储 DAG, 任务定义，运行历史，用户，权限等

7. redis -  将消息从 scheduler 转发到 worker 的代理

   

### airflow 安装

官方安装方式主要有 `pip` ， `docker` 以及 `helm`(k8s)。当前使用的 是 `docker`安装，减少依赖以及不污染环境

docker 安装要求如下：

1. 至少 4 GB 内存
2. docker-compose v1.29.1 版本及以上 

**补充 docker-compose 1.29.2 安装示例**
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

docker-compose --version

# sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose  # 如果 docker-compose 提示找不到
```
#### 安装过程

1.    检验内存是否满足要求
```bash
docker run --rm "debian:buster-slim" bash -c 'numfmt --to iec $(echo $(($(getconf _PHYS_PAGES) * $(getconf PAGE_SIZE))))'
```

2. 创建 airflow 相关文件夹

```bash
mkdir ./airflow 
cd ./airflow 
mkdir  ./dags ./logs ./plugins
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

3.  获取 Airflow 配置文件 ( 2.2.1 版本)
按需修改
```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.2.1/docker-compose.yaml'
```
4. 初始化数据库，并创建管理用户

```bash
docker-compose up airflow-init
```

5. 启动 airflow
建议先前台启动测试没问题再后台启动
```bash
docker-compose up  #  docker-compose up -d  
```


### 简单测试

#### 1. 命令行操作
```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.2.1/airflow.sh'
chmod +x airflow.sh

./airflow.sh info
```

进入 bash  或 python 终端

```bash
./airflow.sh bash

./airflow.sh python
```

### 基于官方镜像制作个人镜像
跑 DAG 中的代码可能需要用到shell, python三方包等原因，一般实际使用还需要在官方镜像上集成

当前 airflow 最新版本为 2.2.1，以此为基础安装部分软件，以及 python 三方包,详细可参考  https://github.com/itswl/airflow

```bash
git clone git@github.com:itswl/airflow.git
cd airflow
```

Dockflie 文件
```dockerfile
FROM apache/airflow:2.2.1

USER root
ENV REPOSITRY="https://mirrors.aliyun.com/pypi/simple"  TRUST_HOST="mirrors.aliyun.com"
RUN cp /etc/apt/sources.list /etc/apt/sources.list.bak && sed -i "s@http://deb.debian.org@http://mirrors.aliyun.com@g" /etc/apt/sources.list && rm -Rf /var/lib/apt/lists/* && apt-get update
RUN apt-get install -y  --no-install-recommends  wget iputils-ping vim &&  apt-get autoremove -yqq --purge && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow

COPY requirements.txt .
RUN /usr/local/bin/python -m pip install  --no-cache-dir  --upgrade pip -i ${REPOSITRY} && pip install  --no-cache-dir  -r requirements.txt -i ${REPOSITRY}

```

requirements.txt 

```python
lxml
plyvel
```

仅在 原始镜像上换源安装 wget iputils-ping vim，以及 python 包的  lxml plyvel。可根据实际情况修改

**制作镜像文件**
镜像为  imwl/airflow:2.2.1
```bash
docker_image_version=' imwl/airflow:2.2.1'
docker build -t  ${docker_image_version}  .
```

制作镜像完成

#### 修改 docker-compose 文件
docker-compose.yaml 节选，详细可参考完整文件
```bash
##############################################
#
#      当前只在官方文修改以下内容
#
#    image: imwl/airflow:2.2.1  # 更换镜像
#    - ./airflow.cfg:/opt/airflow/airflow.cfg   # 添加配置文件
#    _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-zetyun}    # 用户名 zetyun
#    _AIRFLOW_WWW_USER_PASSWORD:  ${_AIRFLOW_WWW_USER_PASSWORD:-zetyun}  # 密码 zetyun
#
#
##############################################
---
version: '3'
x-airflow-common:
  &airflow-common
  # In order to add custom dependencies or upgrade provider packages you can use your extended image.
  # Comment the image line, place your Dockerfile in the directory where you placed the docker-compose.yaml
  # and uncomment the "build" line below, Then run `docker-compose build` to build the images.
#  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.2.1}
  image: imwl/airflow:v1
  # build: .
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'true'
    AIRFLOW__API__AUTH_BACKEND: 'airflow.api.auth.backend.basic_auth'
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-}
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
    - ./airflow.cfg:/opt/airflow/airflow.cfg

......

    # yamllint enable rule:line-length
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_UPGRADE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-zetyn}
      _AIRFLOW_WWW_USER_PASSWORD:  ${_AIRFLOW_WWW_USER_PASSWORD:-zetyun}

    user: "0:0"
    volumes:
      - .:/sources



```




#### airflow.cfg 配置文件

airflow 官方文件 ： https://github.com/apache/airflow/blob/main/airflow/config_templates/default_airflow.cfg

airflow.cfg 也可以不用，需要用到的 环境变量都可以定义在  docker-compose 文件中
参考 https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html

当  docker-compose 与 airflow.cfg 冲突时，使用的是 docker-compose 中的值

配置节选，当前为 邮件 的配置示例
```


[email]

# Configuration email backend and whether to
# send email alerts on retry or failure
# Email backend to use
email_backend = airflow.utils.email.send_email_smtp

# Email connection to use
email_conn_id = smtp_default

# Whether email alerts should be sent when a task is retried
default_email_on_retry = True

# Whether email alerts should be sent when a task failed
default_email_on_failure = True

# File that will be used as the template for Email subject (which will be rendered using Jinja2).
# If not set, Airflow uses a base template.
# Example: subject_template = /path/to/my_subject_template_file
# subject_template =

# File that will be used as the template for Email content (which will be rendered using Jinja2).
# If not set, Airflow uses a base template.
# Example: html_content_template = /path/to/my_html_content_template_file
# html_content_template =

[smtp]

# If you want airflow to send emails on retries, failure, and you want to use
# the airflow.utils.email.send_email_smtp function, you have to configure an
# smtp server here
smtp_host = smtp.zetyun.com
smtp_starttls = False
smtp_ssl = True
# Example: smtp_user = airflow
smtp_user = test_user@zetyun.com
# Example: smtp_password = airflow
smtp_password = test_password
smtp_port = 465
smtp_mail_from = test_user@zetyun.com
smtp_timeout = 30
smtp_retry_limit = 5
```

将上述文件中的变量改为环境变量

```
AIRFLOW__EMAIL__EMAIL_BACKEND: 'airflow.utils.email.send_email_smtp'
AIRFLOW__EMAIL__EMAIL_CONN_ID: 'smtp_default'
AIRFLOW__EMAIL__DEFAULT_EMAIL_ON_RETRY: 'true'
AIRFLOW__EMAIL__DEFAULT_EMAIL_ON_FAILURE: 'true'
#AIRFLOW__EMAIL__SUBJECT_TEMPLATE：'/path/to/my_subject_template_file'
#AIRFLOW__EMAIL__HTML_CONTENT_TEMPLATE: '/path/to/my_html_content_template_file'


AIRFLOW__SMTP__SMTP_HOST: 'smtp.zetyun.com'
AIRFLOW__SMTP__SMTP_STARTTLS='false'
AIRFLOW__SMTP__SMTP_SSL='true'
AIRFLOW__SMTP__SMTP_USER: 'test_user@zetyun.com'
AIRFLOW__SMTP__SMTP_PASSWORD: 'test_password'
#AIRFLOW__SMTP__SMTP_PASSWORD_CMD
#AIRFLOW__SMTP__SMTP_PASSWORD_SECRET
AIRFLOW__SMTP__SMTP_PORT: '465'
AIRFLOW__SMTP__SMTP_MAIL_FROM: 'test_user@zetyun.com'
AIRFLOW__SMTP__SMTP_TIMEOUT: 30
AIRFLOW__SMTP__SMTP_RETRY_LIMIT: 5

```

最后启动

```bash
docker-compose up -d
```


#### airflow.cfg 配置文件

#### 2. 网页操作

账号密码已改为 zetyun/zetyun ，默认 airflow/airflow

![airflow网页](./images/airflow网页.png)


#### 3. Rest API 操作
```
[root@k8s01 airflow]# ENDPOINT_URL="http://localhost:8080/"
[root@k8s01 airflow]# curl -X GET \
                          --user "zetyun:zetyun" \ 
                            "${ENDPOINT_URL}/api/v1/pools"
{
  "pools": [
    {
      "name": "default_pool",
      "occupied_slots": 0,
      "open_slots": 128,
      "queued_slots": 0,
      "running_slots": 0,
      "slots": 128
    }
  ],
  "total_entries": 1
}

```

## 附录

### 目录结构
airflow/
├── dags                                  # DAG 文件路径
├── docker-compose.yaml     # airflow 配置文件

├── Dockerfile                          # 制作docker 镜像 文件

├── logs                                  # 日志路径

├── plugins                            # 自定义插件路径

└── requirements.txt          # 安装的 pip包

### 卸载 airflow

```bash
cd ./airflow
docker-compose down --volumes --remove-orphans
cd ..
rm -rf ./airflow

# 完整卸载，包含数据库和镜像
# docker-compose down --volumes --rmi all
```

### docker-compose.yaml 文件示例

2.2.1 官方文件 https://airflow.apache.org/docs/apache-airflow/2.2.2/docker-compose.yaml

```bash
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

# Basic Airflow cluster configuration for CeleryExecutor with Redis and PostgreSQL.
#
# WARNING: This configuration is for local development. Do not use it in a production deployment.
#
# This configuration supports basic configuration using environment variables or an .env file
# The following variables are supported:
#
# AIRFLOW_IMAGE_NAME           - Docker image name used to run Airflow.
#                                Default: apache/airflow:2.2.1
# AIRFLOW_UID                  - User ID in Airflow containers
#                                Default: 50000
# Those configurations are useful mostly in case of standalone testing/running Airflow in test/try-out mode
#
# _AIRFLOW_WWW_USER_USERNAME   - Username for the administrator account (if requested).
#                                Default: airflow
# _AIRFLOW_WWW_USER_PASSWORD   - Password for the administrator account (if requested).
#                                Default: airflow
# _PIP_ADDITIONAL_REQUIREMENTS - Additional PIP requirements to add when starting all containers.
#                                Default: ''
#
# Feel free to modify this file to suit your needs.
---
version: '3'
x-airflow-common:
  &airflow-common
  # In order to add custom dependencies or upgrade provider packages you can use your extended image.
  # Comment the image line, place your Dockerfile in the directory where you placed the docker-compose.yaml
  # and uncomment the "build" line below, Then run `docker-compose build` to build the images.
  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.2.1}
  # build: .
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'true'
    AIRFLOW__API__AUTH_BACKEND: 'airflow.api.auth.backend.basic_auth'
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-}
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on:
    &airflow-common-depends-on
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5
    restart: always

  redis:
    image: redis:latest
    expose:
      - 6379
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 30s
      retries: 50
    restart: always

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - 8080:8080
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type SchedulerJob --hostname "$${HOSTNAME}"']
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-worker:
    <<: *airflow-common
    command: celery worker
    healthcheck:
      test:
        - "CMD-SHELL"
        - 'celery --app airflow.executors.celery_executor.app inspect ping -d "celery@$${HOSTNAME}"'
      interval: 10s
      timeout: 10s
      retries: 5
    environment:
      <<: *airflow-common-env
      # Required to handle warm shutdown of the celery workers properly
      # See https://airflow.apache.org/docs/docker-stack/entrypoint.html#signal-propagation
      DUMB_INIT_SETSID: "0"
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-triggerer:
    <<: *airflow-common
    command: triggerer
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type TriggererJob --hostname "$${HOSTNAME}"']
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    # yamllint disable rule:line-length
    command:
      - -c
      - |
        function ver() {
          printf "%04d%04d%04d%04d" $${1//./ }
        }
        airflow_version=$$(gosu airflow airflow version)
        airflow_version_comparable=$$(ver $${airflow_version})
        min_airflow_version=2.2.0
        min_airflow_version_comparable=$$(ver $${min_airflow_version})
        if (( airflow_version_comparable < min_airflow_version_comparable )); then
          echo
          echo -e "\033[1;31mERROR!!!: Too old Airflow version $${airflow_version}!\e[0m"
          echo "The minimum Airflow version supported: $${min_airflow_version}. Only use this or higher!"
          echo
          exit 1
        fi
        if [[ -z "${AIRFLOW_UID}" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: AIRFLOW_UID not set!\e[0m"
          echo "If you are on Linux, you SHOULD follow the instructions below to set "
          echo "AIRFLOW_UID environment variable, otherwise files will be owned by root."
          echo "For other operating systems you can get rid of the warning with manually created .env file:"
          echo "    See: https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#setting-the-right-airflow-user"
          echo
        fi
        one_meg=1048576
        mem_available=$$(($$(getconf _PHYS_PAGES) * $$(getconf PAGE_SIZE) / one_meg))
        cpus_available=$$(grep -cE 'cpu[0-9]+' /proc/stat)
        disk_available=$$(df / | tail -1 | awk '{print $$4}')
        warning_resources="false"
        if (( mem_available < 4000 )) ; then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough memory available for Docker.\e[0m"
          echo "At least 4GB of memory required. You have $$(numfmt --to iec $$((mem_available * one_meg)))"
          echo
          warning_resources="true"
        fi
        if (( cpus_available < 2 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough CPUS available for Docker.\e[0m"
          echo "At least 2 CPUs recommended. You have $${cpus_available}"
          echo
          warning_resources="true"
        fi
        if (( disk_available < one_meg * 10 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough Disk space available for Docker.\e[0m"
          echo "At least 10 GBs recommended. You have $$(numfmt --to iec $$((disk_available * 1024 )))"
          echo
          warning_resources="true"
        fi
        if [[ $${warning_resources} == "true" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: You have not enough resources to run Airflow (see above)!\e[0m"
          echo "Please follow the instructions to increase amount of resources available:"
          echo "   https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#before-you-begin"
          echo
        fi
        mkdir -p /sources/logs /sources/dags /sources/plugins
        chown -R "${AIRFLOW_UID}:0" /sources/{logs,dags,plugins}
        exec /entrypoint airflow version
    # yamllint enable rule:line-length
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_UPGRADE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: zetyun
      _AIRFLOW_WWW_USER_PASSWORD: zetyun
    user: "0:0"
    volumes:
      - .:/sources

  airflow-cli:
    <<: *airflow-common
    profiles:
      - debug
    environment:
      <<: *airflow-common-env
      CONNECTION_CHECK_MAX_COUNT: "0"
    # Workaround for entrypoint issue. See: https://github.com/apache/airflow/issues/16252
    command:
      - bash
      - -c
      - airflow

  flower:
    <<: *airflow-common
    command: celery flower
    ports:
      - 5555:5555
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:5555/"]
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

volumes:
  postgres-db-volume:

```
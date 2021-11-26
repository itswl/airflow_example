## airflow安装扩展
### 基于官方镜像制作个人镜像

当前 airflow 最新版本为 2.2.1，以此为基础安装部分软件，以及 python 三方包,详细文件可参考  https://github.com/itswl/airflow

```
git clone git@github.com:itswl/airflow.git
cd airflow
```

Dockflie 文件
```
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

```
lxml
plyvel
```

仅在 原始镜像上换源安装 wget iputils-ping vim，以及 python 包的  lxml plyvel

**制作镜像文件**
镜像为  imwl/airflow:2.2.1
```
docker_image_version=' imwl/airflow:2.2.1'
docker build -t  ${docker_image_version}  .
```

制作镜像完成

### 修改 docker-compose 文件
docker-compose.yaml 节选，详细可参考完整文件
```
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

启动

```
docker-compose up -d
```


### airflow.cfg 配置文件

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

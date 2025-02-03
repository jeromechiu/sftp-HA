FROM alpine:latest


# Steps done in one RUN layer:
# - Install upgrades and new packages
RUN apk update && apk upgrade && \
    apk add bash shadow openssh-server-pam openssh-sftp-server python3 py3-pip  && \
    rm -rf /var/cache/apk/*
RUN mkdir -p /var/run/stressTest/stressTest/stressTest
RUN mkdir -p /var/run/stressTest/tools
COPY ./stressTest/stressTest /var/run/stressTest/stressTest/stressTest
COPY ./stressTest/requirements.txt  /var/run/stressTest/stressTest
COPY ./tools/sftp.py /var/run/stressTest/tools

WORKDIR /var/run/stressTest/stressTest
RUN pip install -r requirements.txt --break-system-packages

WORKDIR /var/run/stressTest/stressTest/stressTest
RUN python manage.py makemigrations

EXPOSE 2224

ENTRYPOINT ["python",  "manage.py", "runserver", "0.0.0.0:8080"]

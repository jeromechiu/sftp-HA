FROM alpine:latest


# Steps done in one RUN layer:
# - Install upgrades and new packages
RUN apk update && apk upgrade && \
    apk add bash shadow openssh-server-pam openssh-sftp-server python3 py3-pip  && \
    rm -rf /var/cache/apk/*
RUN mkdir -p /var/run/filesync/filesync
RUN mkdir -p /var/run/filesync/tools
COPY config.yaml /var/run/filesync/filesync
COPY requirements.txt /var/run/filesync/filesync
COPY filesync.py /var/run/filesync/filesync


COPY ./tools/sftp.py /var/run/filesync/tools

WORKDIR /var/run/filesync/filesync
RUN pip install -r requirements.txt --break-system-packages

ENTRYPOINT ["python",  "filesync.py"]
# ENTRYPOINT ["bash"]
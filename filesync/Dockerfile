FROM alpine:latest


# Steps done in one RUN layer:
# - Install upgrades and new packages
RUN apk update && apk upgrade && \
    apk add bash shadow openssh-server-pam openssh-sftp-server python3 py3-pip  && \
    rm -rf /var/cache/apk/*
COPY config.yaml /
COPY requirements.txt /
COPY filesync.py /

RUN pip install -r requirements.txt --break-system-packages

ENTRYPOINT ["python",  "filesync.py"]
#  ENTRYPOINT ["bash"]

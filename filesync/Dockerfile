FROM alpine:latest


ARG BUILDPATH
RUN echo ${BUILDPATH}

# Steps done in one RUN layer:
# - Install upgrades and new packages
RUN apk update && apk upgrade && \
    apk add bash shadow openssh-server-pam openssh-sftp-server python3 py3-pip  && \
    rm -rf /var/cache/apk/*
RUN mkdir -p /var/run/filesync/filesync
RUN mkdir -p /var/run/filesync/tools
COPY ${BUILDPATH}/filesync/config.yaml /var/run/filesync/filesync
COPY ${BUILDPATH}/filesync/requirements.txt /var/run/filesync/filesync
COPY ${BUILDPATH}/filesync/filesync.py /var/run/filesync/filesync


COPY ${BUILDPATH}tools/sftp.py /var/run/filesync/tools

WORKDIR /var/run/filesync/filesync
RUN pip install -r requirements.txt --break-system-packages

ENTRYPOINT ["python",  "filesync.py"]
# ENTRYPOINT ["bash"]
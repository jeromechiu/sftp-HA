FROM alpine:latest


# Steps done in one RUN layer:
# - Install upgrades and new packages
# - OpenSSH needs /var/run/sshd to run
# - Remove generic host keys, entrypoint generates unique keys
RUN apk update && apk upgrade && \
    apk add bash shadow openssh-server-pam openssh-sftp-server python3 py3-pip  && \
    rm -rf /var/cache/apk/* && \
    ln -s /usr/sbin/sshd.pam /usr/sbin/sshd && \
    mkdir -p /var/run/sshd && \
    rm -f /etc/ssh/ssh_host_*key*


COPY config/sshd_config /etc/ssh/sshd_config
COPY tools/create-sftp-user /usr/local/bin/
COPY tools/runsftp.sh /
COPY tools/main.py /

EXPOSE 22

ENTRYPOINT ["python",  "main.py"]

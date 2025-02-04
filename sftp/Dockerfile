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
    rm -f /etc/ssh/ssh_host_*key*  && \
    mkdir -p /home/admin/admin/


COPY config/sshd_config /etc/ssh/sshd_config

COPY config/users.yaml /
COPY tools/runsftp.sh /
COPY tools/main.py /
COPY requirements.txt /


RUN cp /users.yaml /home/admin/admin/users.yaml
RUN useradd -m -s /bin/false admin
RUN chown admin:admin /home/admin/admin/users.yaml
RUN pip install -r requirements.txt --break-system-packages

EXPOSE 22

ENTRYPOINT ["python",  "main.py"]
#  ENTRYPOINT ["bash"]

from random import randint
import time
from tempfile import TemporaryDirectory
import os
import sys
from pathlib import Path
from stressTest import settings

sys.path.insert(1, os.path.join(settings.BASE_DIR.parent.parent, 'tools'))  # nopep8
from sftp import sftp  # nopep8


def writeDummyFiles(folder, sftp_url, sftp_port, sftp_username, sftp_password):
    with TemporaryDirectory() as root:
        size = randint(500, 10000)
        filename = f'{int(time.time())}.txt'
        try:
            f = open(os.path.join(root, filename), "w")
            for _ in range(size):
                f.write(f'{int(time.time())}\n')
            f.close()
        except Exception as e:
            print(e)
        master = sftp(hostname=sftp_url, port=sftp_port,
                      username=sftp_username, password=sftp_password)
        try:
            master.connect()
        except Exception as ex:
            print(f'Connect to Master error: {ex}')
        try:
            master.upload(os.path.join(root, filename),
                          os.path.join(sftp_username, folder), filename)
            print(
                f'File {filename} uploaded to {os.path.join(sftp_username, folder)} done')

        except Exception as ex:
            print(f'Upload error: {ex}')
            master.disconnect()
            return False
        master.disconnect()
        return True

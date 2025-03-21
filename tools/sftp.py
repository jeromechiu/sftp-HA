import os
import time
from stat import S_ISDIR, S_ISREG

import pysftp


class sftp:
    def __init__(self, hostname, username, password, port=22):
        """Constructor Method"""
        # Set connection object to None (initial value)
        self.connection = None
        self.hostname = hostname
        self.username = username
        self.password = str(password).encode('utf-8')
        self.port = port

    def connect(self):
        """Connects to the sftp server and returns the sftp connection object"""
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        try:
            # Get the sftp connection object
            self.connection = pysftp.Connection(
                host=self.hostname,
                username=self.username,
                password=self.password,
                port=self.port,
                cnopts=cnopts,

            )
        except Exception as err:
            raise Exception(err)

    def disconnect(self):
        """Closes the sftp connection"""
        self.connection.close()
        print(f"Disconnected from host {self.hostname}")

    def listDirsandFiles(self, remote_path):
        """lists all the files and directories in the specified path and returns them"""
        dirs = []
        files = []
        ufiles = []

        self.connection.walktree(
            remote_path, fcallback=files.append, dcallback=dirs.append, ucallback=ufiles.append, recurse=True)

        dirs.sort(key=lambda d: len(d))
        files = [(os.path.split(f)[0], os.path.split(f)[1], self.connection.stat(f)) for f in files]

        return files, dirs, ufiles

    def listdir_attr(self, remote_path):
        """lists all the files and directories (with their attributes) in the specified path and returns them"""
        for attr in self.connection.listdir_attr(remote_path):
            yield attr

    def fileAttr(self, remote_path, filename):
        attr = None
        full_filename = os.path.join(remote_path, filename)
        try:
            attr = self.connection.stat(full_filename)
        except FileNotFoundError:
            print('No Such file at target')
        return attr

    def upload(self, source_local_path, remote_dir, remote_filename):
        """
        Uploads the source files from local to the sftp server.
        """
        print(f'uploading {remote_filename} to {self.hostname} as {self.username} [(remote path: {remote_dir});\
            (source local path: {source_local_path})]')

        root = '/'
        with self.connection.cd():
            if not self.connection.exists(remote_dir):
                print(f'Remote folder {remote_dir} not exist')
                folders = remote_dir.split('/')[1:]
                for f in folders:
                    if not self.connection.exists(f):
                        print(f'Prepare to create folder: {f}')
                        try:
                            self.connection.mkdir(f)
                        except Exception as err:
                            raise Exception(err)
                    self.connection.chdir(f)
        try:
            # Upload file from SFTP
            self.connection.put(localpath=source_local_path, remotepath=os.path.join(
                remote_dir, remote_filename), confirm=True)
            print("upload completed")

        except Exception as err:
            raise Exception(err)

    def download(self, remote_path, target_local_path):
        """
        Downloads the file from remote sftp server to local.
        Also, by default extracts the file to the specified target_local_path
        """

        try:
            print(f'downloading from {self.hostname} as {self.username} [(remote path : \
                {remote_path});(local path: {target_local_path})]')

            # Create the target directory if it does not exist
            path, _ = os.path.split(target_local_path)
            if not os.path.isdir(path):
                try:
                    os.makedirs(path)
                except Exception as err:
                    raise Exception(err)

            # Download from remote sftp server to local
            self.connection.get(remote_path, target_local_path)
            print("download completed")

        except Exception as err:
            raise Exception(err)

    def delete(self, remote_path):
        """
        Deletes the specified file from the remote sftp server.
        """
        try:
            print(
                f'deleting {remote_path} from {self.hostname} as {self.username}')
            self.connection.remove(remote_path)
            print("delete completed")
        except Exception as err:
            raise Exception(err)

    def removeDir(self, remote_path):
        """
        Deletes the specified directory from the remote sftp server.
        """
        try:
            print(
                f'deleting {remote_path} from {self.hostname} as {self.username}')
            self.connection.rmdir(remote_path)
            print("delete completed")
        except Exception as err:
            raise Exception(err)

    def isDirEmpty(self, remote_path):
        """
        Checks if the specified directory is empty or not.
        """
        try:
            if len(self.connection.listdir(remote_path)) == 0:
                return True
            else:
                return False
        except Exception as err:
            raise Exception(err)

    def isDirExist(self, remote_path):
        """
        Checks if the specified directory exists or not.
        """
        try:
            if self.connection.isdir(remote_path):
                return True
            else:
                return False
        except Exception as err:
            raise Exception(err)

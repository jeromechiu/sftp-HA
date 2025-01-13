import os
import pysftp
import yaml
import subprocess
from multiprocessing import Event
import multiprocessing as mp
from tempfile import TemporaryDirectory
from time import strftime, localtime
import time
from stat import S_ISDIR, S_ISREG
import time

configName = 'config.yaml'


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

    def listdir(self, remote_path):
        """lists all the files and directories in the specified path and returns them"""
        for obj in self.connection.listdir(remote_path):
            yield obj

    def listdir_attr(self, remote_path):
        """lists all the files and directories (with their attributes) in the specified path and returns them"""
        for attr in self.connection.listdir_attr(remote_path):
            yield attr

    def listfiles(self, remote_path):
        """lists all files in sftp with directory and returns them"""
        files = list()
        try:
            # for file in master.listdir('/'):
            for file in self.listdir_attr(remote_path):
                # print(file.filename, file.st_mode, file.st_size, file.st_atime, file.st_mtime)
                if S_ISDIR(file.st_mode):
                    # print(file.filename + " is folder")
                    files.extend(self.listfiles(
                        os.path.join(remote_path, file.filename)))
                elif S_ISREG(file.st_mode):

                    if list(file.filename)[0] != '.':
                        # print(file.filename + " is file")
                        files.append(
                            [remote_path, file.filename, file.st_mtime])

        except Exception as ex:
            print(f'Get File List error: {ex}')
        return files

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
                        self.connection.mkdir(f)
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


def doSync(mode, master, standby, masterFiles, standbyFiles):
    with TemporaryDirectory(prefix="sftp_") as tmpdirname:
        if mode == 'single':
            standbyFilesNoMktime = [[x1, x2] for [x1, x2, _] in standbyFiles]
            """Master files first"""
            for directory, filename, mktime in masterFiles:
                print(
                    f'Check file {os.path.join(directory,filename)} of Standby')
                # print([directory, filename])
                # print(f'standbyFilesNoMktime {standbyFilesNoMktime}')
                if [directory, filename] not in standbyFilesNoMktime:
                    print(f'File {filename} in Master ----> standby')
                    master.download(os.path.join(directory, filename),
                                    os.path.join(tmpdirname, filename))
                    standby.upload(os.path.join(
                        tmpdirname, filename), directory, filename)
        else:
            """Not yet implement"""
            pass


def monitorConfig(event):
    lastModoft = os.path.getmtime(configName)
    while True:
        if lastModoft != os.path.getmtime(configName):
            lastModoft = os.path.getmtime(configName)
            event.set()
            print(
                f'config.yaml is changed at {strftime("%Y-%m-%d %H:%M:%S", localtime(os.path.getmtime(configName)))}')
        time.sleep(1)


def syncFile(config):
    """
    Synchronizes files between a master and standby SFTP server based on the configuration file.
    """
    print('Start to run Sync admin files')
    with open(config, 'r') as fp:
        configContext = yaml.load(fp, Loader=yaml.FullLoader)
        masterIP = configContext['Master']['IP']
        masterPORT = configContext['Master']['PORT']
        masterUSER = configContext['Master']['USERNAME']
        masterPASSWD = configContext['Master']['PASSWORD']
        # Currently, the program only support single direction synchronization.
        syncMETHOD = configContext['Master']['SYNCMETHOD']

        standyIP = configContext['Standby']['IP']
        standyPORT = configContext['Standby']['PORT']
        standyUSER = configContext['Standby']['USERNAME']
        standyPASSWD = configContext['Standby']['PASSWORD']

    while True:
        master = sftp(hostname=masterIP, port=masterPORT,
                      username=masterUSER, password=masterPASSWD)
        try:
            master.connect()
            print(f"Connected to {masterIP} as {masterUSER}.")
        except Exception as ex:
            print(f'Connect to Master error: {ex}')
            return
        standby = sftp(hostname=standyIP, port=standyPORT,
                       username=standyUSER, password=standyPASSWD)
        try:
            standby.connect()
        except Exception as ex:
            print(f'Connect to Standby error: {ex}')
            return

        root = f'/'
        masterFiles = master.listfiles(root)
        standbyFiles = standby.listfiles(root)
        print('______________________')
        print(f'masterFiles: {masterFiles}')
        print(f'standbyFiles: {standbyFiles}')

        # Sync user account info
        doSync(syncMETHOD, master=master, standby=standby,
               masterFiles=masterFiles, standbyFiles=standbyFiles)

        standby.disconnect()
        # Sync user's files
        with TemporaryDirectory(prefix="sftp_") as tmpdirname:
            master.download(os.path.join(
                '/admin', 'users.yaml'), f'{tmpdirname}/users.yaml')
            master.disconnect()

            with open(f'{tmpdirname}/users.yaml', 'r') as fp:
                users = yaml.load(fp, Loader=yaml.FullLoader)
                for user in users['users']:
                    if users['users'][user]['name'] != 'admin':
                        username = users['users'][user]['name']
                        password = users['users'][user]['password']
                        print(f'User {username} is going to sync')
                        master = sftp(hostname=masterIP, port=masterPORT,
                                      username=username, password=password)
                        try:
                            master.connect()
                        except Exception as ex:
                            print(f'Connect to Master error: {ex}')
                            continue
                        standby = sftp(hostname=standyIP, port=standyPORT,
                                       username=username, password=password)
                        try:
                            standby.connect()
                        except Exception as ex:
                            print(f'Connect to Standby error: {ex}')
                            continue
                        root = f'/{username}'
                        masterFiles = master.listfiles(root)
                        standbyFiles = standby.listfiles(root)
                        print('______________________')
                        print(f'masterFiles: {masterFiles}')
                        print(f'standbyFiles: {standbyFiles}')

                        # Sync user account info
                        doSync(syncMETHOD, master=master, standby=standby,
                               masterFiles=masterFiles, standbyFiles=standbyFiles)
                        master.disconnect()
                        standby.disconnect()
                        time.sleep(1)

        time.sleep(100)


def runAll():
    """
    Runs the monitorConfig and syncFile processes concurrently.
    """
    config_flag = Event()
    working_flag = Event
    monitor = mp.Process(target=monitorConfig, args=(config_flag,))
    sync = mp.Process(target=syncFile, args=(configName,))

    monitor.start()
    sync.start()

    while True:
        if config_flag.is_set() and not working_flag.is_set():
            sync.terminate()
            sync = mp.Process(target=syncFile, args=(configName,))
            sync.start()
            config_flag.clear()
        elif not sync.is_alive():
            print('Sync Process is not alive')
            sync = mp.Process(target=syncFile, args=(configName,))
            sync.start()
        elif not monitor.is_alive():
            print('Monitor Process is not alive')
            monitor = mp.Process(target=monitorConfig, args=(config_flag,))
            monitor.start()
        else:
            time.sleep(5)


if __name__ == '__main__':
    mp.set_start_method('spawn')
    run = mp.Process(target=runAll, args=())
    run.start()
    run.join()

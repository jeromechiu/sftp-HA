import multiprocessing as mp
import os
import sys
import time
import warnings
from multiprocessing import Event
from pathlib import Path
from tempfile import TemporaryDirectory
from time import localtime, strftime

import yaml

warnings.filterwarnings('ignore')

sys.path.insert(1, os.path.join(Path(__file__).resolve().parent.parent, 'tools'))  # nopep8
from sftp import sftp  # nopep8

configName = 'config.yaml'
syncInterval = 100


def doSync(mode, master, standby, masterFiles, standbyFiles, standbyDirs):
    with TemporaryDirectory(prefix="sftp_") as tmpdirname:
        if mode == 'single':
            standbyFilesNoMktime = [[x1, x2] for [x1, x2, _] in standbyFiles]
            """Master files first, update to Standby"""
            for directory, filename, mktime in masterFiles:
                print(
                    f'Check file {os.path.join(directory,filename)} of Standby')

                if [directory, filename] not in standbyFilesNoMktime:
                    print(f'File {filename} in Master ----> standby')
                    master.download(os.path.join(directory, filename),
                                    os.path.join(tmpdirname, filename))
                    standby.upload(os.path.join(
                        tmpdirname, filename), directory, filename)
                else:
                    if master.fileAttr(directory, filename).st_size != standby.fileAttr(directory, filename).st_size:
                        print(
                            f'{filename} of Master is not the same size as Standby')
                        print(f'File {filename} in Master ----> standby')
                        master.download(os.path.join(directory, filename),
                                        os.path.join(tmpdirname, filename))
                        standby.upload(os.path.join(
                            tmpdirname, filename), directory, filename)
            """Master files first, delete in Standby"""
            for directory, filename, _ in standbyFiles:
                if directory != '/admin':
                    print(
                        f'Check file {os.path.join(directory,filename)} of Master')
                    msasterFilesNoMktime = [[x1, x2]
                                            for [x1, x2, _] in masterFiles]
                    if [directory, filename] not in msasterFilesNoMktime:
                        print(f'File {filename} in Standby ----> delete')
                        standby.delete(os.path.join(directory, filename))
            for directory in standbyDirs:
                if not master.isDirExist(directory):
                    print(
                        f'Directory {directory} in Master is not Exist, delete in Standby')
                    standby.removeDir(directory)
                    continue
                if not master.isDirEmpty(directory):
                    pass

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

    with open(config, 'r') as fp:
        configContext = yaml.load(fp, Loader=yaml.FullLoader)
        masterIP = configContext['Master']['IP']
        masterPORT = configContext['Master']['PORT']
        masterUSER = configContext['Master']['USERNAME']
        masterPASSWD = configContext['Master']['PASSWORD']
        # Currently, the program only support single direction synchronization.
        syncMETHOD = configContext['Master']['SYNCMETHOD']
        syncInterval = configContext['Master']['SYNCINTERVAL']

        standyIP = configContext['Standby']['IP']
        standyPORT = configContext['Standby']['PORT']
        standyUSER = configContext['Standby']['USERNAME']
        standyPASSWD = configContext['Standby']['PASSWORD']
    print(
        f'Start to run program. Master: {masterIP}, Standby: {standyIP}, SyncMethod: {syncMETHOD}, SyncInterval: {syncInterval}')
    while True:

        # Sync admin account info
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

        root = '/'
        # Some time, the first listfiles will return empty list, so we need to try again
        masterFiles = master.listfiles(root)
        standbyFiles = standby.listfiles(root)

        if masterFiles == []:
            time.sleep(0.1)
            masterFiles = master.listfiles(root)
        if standbyFiles == []:
            time.sleep(0.1)
            standbyFiles = standby.listfiles(root)

        # Sync user account info
        doSync(syncMETHOD, master=master, standby=standby,
               masterFiles=masterFiles, standbyFiles=standbyFiles, standbyDirs=[])

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

                        # Some time, the first listfiles will return empty list, so we need to try again
                        masterFiles = master.listfiles(root)
                        standbyFiles = standby.listfiles(root)
                        standbyDirs = standby.listDirs(root)

                        if masterFiles == []:
                            time.sleep(0.1)
                            masterFiles = master.listfiles(root)
                        if standbyFiles == []:
                            time.sleep(0.1)
                            standbyFiles = standby.listfiles(root)
                        if standbyDirs == []:
                            time.sleep(0.1)
                            standbyDirs = standby.listDirs(root)

                        print('______________________')
                        print(f'{username}\'s master data files: {masterFiles}')
                        print(f'{username}\'s standby data files: {standbyFiles}')
                        print(
                            f'{username}\'s standby data directories: {standbyDirs}')

                        doSync(syncMETHOD, master=master, standby=standby,
                               masterFiles=masterFiles, standbyFiles=standbyFiles, standbyDirs=standbyDirs)
                        master.disconnect()
                        standby.disconnect()
                        time.sleep(1)

                        break

        time.sleep(syncInterval)


def runAll():
    """
    Runs the monitorConfig and syncFile processes concurrently.
    """
    config_flag = Event()
    monitor = mp.Process(target=monitorConfig, args=(config_flag,))
    sync = mp.Process(target=syncFile, args=(configName,))

    monitor.start()
    sync.start()

    while True:
        if config_flag.is_set():
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

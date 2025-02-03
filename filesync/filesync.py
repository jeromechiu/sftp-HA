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
syncFrrquency = 100


def doSync(mode, master, standby, masterFiles, standbyFiles):
    with TemporaryDirectory(prefix="sftp_") as tmpdirname:
        if mode == 'single':
            standbyFilesNoMktime = [[x1, x2] for [x1, x2, _] in standbyFiles]
            """Master files first"""
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

        root = '/'
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

        time.sleep(syncFrrquency)


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

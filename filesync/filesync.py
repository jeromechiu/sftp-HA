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


def doSync(mode, master, standby, masterFiles, standbyFiles, standbyDirs, folderHouseKeeping):
    with TemporaryDirectory(prefix="sftp_") as tmpdirname:
        if mode == 'single':
            masterfileNoAttr = [(x, y) for x, y, z in masterFiles]
            standbyfileNoAttr = [(x, y) for x, y, z in standbyFiles]
            """Master files first, update to Standby"""
            for directory, filename, attr in masterFiles:
                # Remove outofdate files in Master, ignore admin
                if directory != '/admin' and len(folderHouseKeeping) != 0:

                    # {'/EPuser/Packinglist': 180, '/EPuser/Invoices': 60}
                    if attr.st_mtime + folderHouseKeeping.get(directory, 0) < time.time():
                        print(
                            f'File {os.path.join(directory,filename)} in Master is out of date, delete')
                        master.delete(os.path.join(directory, filename))
                        continue

                # Update Master file to Standby
                print(
                    f'Check file {os.path.join(directory,filename)} of Standby')
                # print(attr.st_mtime)

                if (directory, filename) not in standbyfileNoAttr:
                    print(f'File {filename} in Master ----> standby')
                    try:
                        master.download(os.path.join(directory, filename),
                                        os.path.join(tmpdirname, filename))
                    except Exception as ex:
                        print(f'Download error: {ex}')
                        continue
                    standby.upload(os.path.join(
                        tmpdirname, filename), directory, filename)
                else:
                    # check the last modified time is the same or not
                    if attr.st_size != standby.fileAttr(directory, filename).st_size:
                        print(
                            f'{filename} of Master is not the same size as Standby')
                        print(f'File {filename} in Master ----> standby')
                        master.download(os.path.join(directory, filename),
                                        os.path.join(tmpdirname, filename))
                        standby.upload(os.path.join(
                            tmpdirname, filename), directory, filename)
            """Master files first, delete in Standby"""
            for directory, filename, attr in standbyFiles:
                if directory != '/admin':
                    print(
                        f'Check file {os.path.join(directory,filename)} of Master')
                    if (directory, filename) not in masterfileNoAttr:
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
        masterFiles, _, _ = master.listDirsandFiles(root)
        standbyFiles, standbyDirs, _ = standby.listDirsandFiles(root)

        # Sync user account info
        doSync(syncMETHOD, master=master, standby=standby,
               masterFiles=masterFiles, standbyFiles=standbyFiles, standbyDirs=[], folderHouseKeeping=[])

        standby.disconnect()

        # Sync user's files
        with TemporaryDirectory(prefix="sftp_") as tmpdirname:
            master.download(os.path.join(
                '/admin', 'users.yaml'), f'{tmpdirname}/users.yaml')
            master.disconnect()

            with open(f'{tmpdirname}/users.yaml', 'r') as fp:
                users = yaml.load(fp, Loader=yaml.FullLoader)
                for num in users['users']:
                    if users['users'][num]['name'] != 'admin':
                        folderHouseKeeping = dict()
                        username = users['users'][num]['name']
                        password = users['users'][num]['password']

                        monthTimeUnit = 60 * 60 * 24 * 30
                        # minuteTimeUnit = 60
                        """    files_house_keeping:
                                enabled: true
                                folders: 
                                    - Packinglist: 3 #months
                                    - Invoices: 1 #months
                        """
                        fileHouseKeeping = users['users'][num]['files_house_keeping']

                        if fileHouseKeeping['enabled']:
                            print(f'HouseKeeping: {username} is enabled')
                            for folder in fileHouseKeeping['folders']:
                                folder_name = list(folder.keys())[0]
                                houseKeepingInterval = folder[folder_name]
                                print(
                                    f'HouseKeeping: {username}\'s {folder_name} for {houseKeepingInterval} months')
                                folderHouseKeeping[os.path.join(
                                    root, username, folder_name)] = houseKeepingInterval * monthTimeUnit

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
                        root = os.path.join('/', username)
                        # Because of getting empty, so that we retrieve agin
                        masterFiles, masterDirs, _ = master.listDirsandFiles(
                            root)
                        standbyFiles, standbyDirs, _ = standby.listDirsandFiles(
                            root)
                        if masterFiles == []:
                            masterFiles, masterDirs, _ = master.listDirsandFiles(
                                root)
                        if standbyFiles == []:
                            standbyFiles, standbyDirs, _ = standby.listDirsandFiles(
                                root)

                        print('______________________')
                        print(f'{username}\'s master data files: {masterFiles}')
                        print(f'{username}\'s standby data files: {standbyFiles}')
                        print(
                            f'{username}\'s master data directories: {masterDirs}')
                        print(
                            f'{username}\'s standby data directories: {standbyDirs}')

                        doSync(syncMETHOD, master=master, standby=standby,
                               masterFiles=masterFiles, standbyFiles=standbyFiles, standbyDirs=standbyDirs, folderHouseKeeping=folderHouseKeeping)
                        master.disconnect()
                        standby.disconnect()
                        time.sleep(0.5)
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

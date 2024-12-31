import os
import pysftp
import yaml
import subprocess
import multiprocessing as mp
import hashlib
import json
from time import strftime, localtime
import time
from stat import S_ISDIR, S_ISREG

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
        finally:
            print(f"Connected to {self.hostname} as {self.username}.")


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


def monitorConfig(q):
    lastModoft = os.path.getmtime(configName)
    while True:
        if lastModoft != os.path.getmtime(configName):
            lastModoft = os.path.getmtime(configName)   
            q.put('changed')
            print(f'config.yaml is changed at {strftime('%Y-%m-%d %H:%M:%S', \
                localtime(os.path.getmtime(configName)))}')
        time.sleep(1)

def syncFile(config):
    print('Start to run Sync function')

    with open(config,'r') as fp:
        configContext = yaml.load(fp, Loader=yaml.FullLoader)
        masterIP = configContext['Master']['IP']
        masterPORT = configContext['Master']['PORT']
        masterUSER = configContext['Master']['USERNAME']
        masterPASSWD = configContext['Master']['PASSWORD']
        syncMETHOD = configContext['Master']['SYNCMETHOD'] # Currently, the program only support single direction synchronization.
        
        standyIP = configContext['Standby']['IP']
        standyPORT = configContext['Standby']['PORT']
        standyUSER = configContext['Standby']['USERNAME']
        standyPASSWD = configContext['Standby']['PASSWORD']
        
    master = sftp(hostname = masterIP,port = masterPORT, username = masterUSER,password = masterPASSWD)
    master.connect()
    standby = sftp(hostname = standyIP,port = standyPORT, username = standyUSER,password = standyPASSWD)
    standby.connect()
    root = '/'
    try:
        # for file in master.listdir('/'):
        for file in master.listdir_attr(root):
            print(file.filename, file.st_mode, file.st_size, file.st_atime, file.st_mtime)
            if S_ISDIR(file.st_mode):
                print(file.filename + " is folder")
            elif S_ISREG(file.st_mode):
                print(file.filename + " is file")
    except Exception as ex:
        print(f'Get File List error: {ex}')
            
    time.sleep(1)

def runAll():
    q = mp.Queue()
    monitor = mp.Process(target=monitorConfig, args=(q,))
    sync = mp.Process(target=syncFile, args=(configName,))
    
    monitor.start()
    sync.start()
    
    while True:
        if q.get() == 'changed':
            print('j')
            sync.terminate()
            print('fefe')
            sync = mp.Process(target=syncFile, args=(configName,))
            sync.start()
            
        else:
            time.sleep(0.5)


if __name__ == '__main__':
    mp.set_start_method('spawn')
    # q = mp.Queue()
    run = mp.Process(target=runAll, args=())
    run.start()
    run.join()
    

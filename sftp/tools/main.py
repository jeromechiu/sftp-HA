#!/usr/bin/python3.12

import os
import subprocess
import traceback
import sys
import multiprocessing as mp
import time
from time import strftime, localtime
import logging
import logging.handlers


def monitorUserAccount(q):
    account = '/etc/sftp/users.conf'
    lastModoft = os.path.getmtime(account)
    while True:
        if lastModoft != os.path.getmtime(account):
            lastModoft = os.path.getmtime(account)
            
            with open(account, 'r') as f:
                lines = [line.rstrip('\n') for line in f]
            for l in lines:
                addcmd = ['/usr/local/bin/create-sftp-user', l]
                subprocess.Popen(addcmd)
    
            q.put('changed')
            print(f'users.conf is changed at {strftime('%Y-%m-%d %H:%M:%S', \
                localtime(os.path.getmtime(account)))}')
        time.sleep(10)

def runSftp(q):

    cmd = ['./runsftp.sh']
    p = subprocess.Popen(cmd, shell=True)
    print(f'sftp {p.pid} is running')
    
    delAdminFolderCmd = ['rm', '-rf', '/home/admin']
    subprocess.Popen(delAdminFolderCmd)
        
    time.sleep(5)
    chaneAdminHomeCmd = ['usermod', '-d', '/home', 'admin']
    subprocess.Popen(chaneAdminHomeCmd)
    
    while q.get() == 'changed':
        subprocess.Popen.kill(p)
        print(f'{p.pid} is been killed')
        p = subprocess.Popen(cmd, shell=True)
    
def runAll(q):
    monitor = mp.Process(target=monitorUserAccount, args=(q,))
    sftp = mp.Process(target=runSftp, args=(q,))
    
    monitor.start()
    sftp.start()
    monitor.join()
    sftp.join()

        
        
if __name__ == '__main__':
    mp.set_start_method('spawn')
    q = mp.Queue()
    run = mp.Process(target=runAll, args=(q,))
    run.start()
    run.join()
    
            
    
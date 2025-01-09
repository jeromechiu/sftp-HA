#!/usr/bin/python3.12

import os
import subprocess
# from threading import Event
import yaml
import multiprocessing as mp
import time
from time import strftime, localtime
import logging
import subprocess
import logging.handlers


# def monitorUserAccount(q):
#     account = '/etc/sftp/users.conf'
#     lastModoft = os.path.getmtime(account)
#     while True:
#         if lastModoft != os.path.getmtime(account):
#             lastModoft = os.path.getmtime(account)

#             with open(account, 'r') as f:
#                 lines = [line.rstrip('\n') for line in f]
#             for l in lines:
#                 addcmd = ['/usr/local/bin/create-sftp-user', l]
#                 subprocess.run(addcmd)

#             q.put('changed')
#             print(f'users.conf is changed at {strftime(' % Y-%m-%d % H: % M: % S', \
#                 localtime(os.path.getmtime(account)))}')
#         time.sleep(10)

"""Create a linux user for sftp"""


class userAccount():
    def createUser(self, username, password):
        # create a new user
        cmd = ['useradd', '-m', '-s', '/bin/false', username]
        subprocess.run(cmd)

        # set the password for the user
        self.changePassword(username, password)

        # create user's home
        cmd = ['mkdir', '-p', f'/home/{username}/{username}']
        subprocess.run(cmd)

        # set home directory
        cmd = ['usermod', '-d', f'/home/{username}', username]
        subprocess.run(cmd)

        # set permission
        cmd = ['chown',  f'{username}:{username}',
               f'/home/{username}/{username}']
        subprocess.run(cmd)
        cmd = ['chown',  f'root:root',
               f'/home/{username}']
        subprocess.run(cmd)

    def changePassword(self, username, password):
        cmd = ['passwd', username]
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.stdin.write(bytes(password + '\n', 'utf-8'))
        proc.stdin.write(bytes(password + '\n', 'utf-8'))
        proc.stdin.flush()
        stdout, stderr = proc.communicate()
        # print(stdout.decode())
        # print(stderr.decode())

    def user_IsExist(self, username):
        cmd = ['id', '-u', username]
        result = subprocess.run(cmd, capture_output=True, text=True)
        # 1 for user not exist
        if result.returncode == 1:
            return False
        return True


def monitorUserAccount(account):
    lastModoft = os.path.getmtime(account)
    firstRun = True
    usermanager = userAccount()
    while True:
        if firstRun:
            with open(account, 'r') as file:
                users = yaml.safe_load(file)['users']

            firstRun = False

            # add user when system first load
            for user in users:
                if not usermanager.user_IsExist(users[user]['name']):
                    usermanager.createUser(
                        users[user]['name'], users[user]['password'])
                    print(f'User {users[user]["name"]} is created')
                else:
                    print(f'User {users[user]["name"]} is already exist')
                    usermanager.changePassword(
                        users[user]['name'], users[user]['password'])

        if lastModoft != os.path.getmtime(account):
            lastModoft = os.path.getmtime(account)

            print(
                f'users.yaml is changed at {strftime("%Y-%m-%d %H:%M:%S", localtime(os.path.getmtime(account)))}')
            with open(account, 'r') as file:
                users = yaml.safe_load(file)['users']

            firstRun = False

            # add user when system first load
            for user in users:
                if not usermanager.user_IsExist(users[user]['name']):
                    usermanager.createUser(
                        users[user]['name'], users[user]['password'])
                    print(f'User {users[user]["name"]} is created')
                else:
                    print(f'User {users[user]["name"]} is already exist')
                    usermanager.changePassword(
                        users[user]['name'], users[user]['password'])

        time.sleep(10)
        # break


def runSftp():

    cmd = ['./runsftp.sh']
    p = subprocess.run(cmd, shell=True)
    print(f'sftp {p.pid} is running')

    # while event.is_set():
    #     subprocess.run.kill(p)
    #     print(f'{p.pid} is been killed')
    #     p = subprocess.run(cmd, shell=True)


def runAll(account):
    monitor = mp.Process(target=monitorUserAccount, args=(account,))
    sftp = mp.Process(target=runSftp, args=())

    monitor.start()
    sftp.start()
    monitor.join()
    sftp.join()


if __name__ == '__main__':
    account = '/home/admin/admin/users.yaml'
    mp.set_start_method('spawn')
    run = mp.Process(target=runAll, args=(account,))
    run.start()
    run.join()

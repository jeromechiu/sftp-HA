import time
import os
from random import randint

count = 10
folders = ['jerome', 'jerome1', 'jerome2']

root = '/Users/kuan-linchiu/Documents/Codes/sftp-HA/sftp/data'
for i in range(count):
    print(i)
    sub = str(randint(1,2))
    for folder in folders:
        if not os.path.exists(os.path.join(root, folder, sub)):
            os.makedirs(os.path.join(root, folder, sub))
        
        
        size = randint(500, 10000)
        f = open(os.path.join(root, folder, sub, f'{int(time.time())}.txt'), "w")
        for _ in range(size):
            f.write(f'{int(time.time())}\n')
        f.close()
        time.sleep(0.2)
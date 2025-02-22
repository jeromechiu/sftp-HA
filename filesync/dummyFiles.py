
import time
import os
from random import randint
from multiprocessing import Pool
import multiprocessing as mp

count = 1000
folders = ['user1', 'user2', 'user3', 'user4', 'user5',
           'user6', 'user7', 'user8', 'user9', 'EPuser']

root = '/mnt/c/Users/11107390/Downloads/dummydata'


def writeDummyFiles(args):
    """
    Writes dummy files to the specified folder and subfolder.

    Args:
        args (tuple): A tuple containing the folder and subfolder names.

    Returns:
        None
    """
    print(args)
    folder = args[0]
    sub = args[1]
    size = randint(500, 10000)
    try:
        f = open(os.path.join(root, folder, sub,
                              f'{int(time.time())}.txt'), "w")
        for _ in range(size):
            f.write(f'{int(time.time())}\n')
        f.close()
    except Exception as e:
        print(e)

    time.sleep(0.1)


if __name__ == '__main__':
    """
    Main entry point of the script.
    """
    cpus = mp.cpu_count()
    poolCount = cpus*2
    args = list()

    for _ in range(count):
        folder = folders[randint(0, len(folders)-1)]
        sub = str(randint(1, 2))
        if not os.path.exists(os.path.join(root, folder, sub)):
            os.makedirs(os.path.join(root, folder, sub))
        args.append((folder, sub,))
    # print(args)
    with mp.Pool(processes=poolCount, maxtasksperchild=2) as p:
        p.map(writeDummyFiles, args)
    p.close
    p.join()

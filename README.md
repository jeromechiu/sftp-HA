
# Introduction
This is a new project for providing high availability of sFTP service. The sFTP service can work in Docker container. The files that are uploaded to master sFTP will be synchronized to standby sFTP automatically by filesync.py and user account can be created in standby sFTP when admin upload updated account information as well.

The service is conducted with sFTP sub-service and file sychnoization sub-service. The sFTP sub-service, refer to sftp main.py, is responslbe for creating a new account and also change password for specific user. The site IT or dev IT can upload users.yaml to admin folder. The account will be created or changed password automatically.

On the other hand, the file sychnoization sub-service, refer to filesync.py, will synchnoizate the file from master to standby. Currently, <strong>the direction of synchnoization is only support one way sync.</strong> 

## FileSync

FileSync is a tool designed to synchronize files between a master and standby SFTP server.

### Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

### Installation

1. Clone the repository:
    
2. Build the Docker images:
    ```sh
    docker-compose build
    ```

3. Start the services:
    ```sh
    docker-compose -f docker-compose-XXX.yaml up -d
    ```
For offical deploymenet, please don't run mater and standby at one physical machine.

### Usage

To run the synchronization process, execute the following command:
```sh
python filesync.py
```

### Stress Test

To get more dummy files when doing stress test, please run dummyfiles.py to generate lots of dummy files.




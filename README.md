# sftp-upload

Example script to upload files to dreamdata custom crm sftp server.

source code in [GO](src/main.go) and [Python](src/main.py)

## Installation

You can install this script to use it locally:

```bash
$ go install github.com/dreamdata-io/sftp-upload@latest
```

## Usage

Upload files or directories to the sftp server:

```bash
$ sftp-upload -username <username> path/to/file1 path/to/dir 
```
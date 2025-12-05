# sftp-upload

Example code to upload files to Dreamdata(c) custom crm sftp server.

If you have any specific requirements, you will need to modify the code to suit your needs.

source code available in [GO](main.go) and [Python](main.py)

## Usage

### Installation

You can install this script, as is, to use it as a CLI:
```bash
$ go install github.com/dreamdata-io/sftp-upload@latest
```

or you can clone the repository and run the script directly:
```bash
$ git clone github.com/dreamdata-io/sftp-upload
$ cd sftp-upload
```

### Running
To upload files to the sftp server, you can run the following command:
- with CLI:
```bash
$ sftp-upload -username <username> path/to/file_1.csv path/to/dir
```
- with Go script:
```bash
$ go run main.go -username <username> path/to/file_1.csv path/to/dir
```
- with Python script:
```bash
$ python main.py -username <username> path/to/file_1.csv path/to/dir
```
You can specify multiple files and directories to upload.

You will be prompted for the sftp login password, that is the same one you can get on the Dreamdata(c) platform.
```
> Enter your password for <username>:
```

If any directories are specified, the script will attempt to upload all files in the directory.
You will be prompted to confirm the upload for each directory.
```
> You will upload all files in path/to/dir. Continue? (y/[n])
```

You must type `y` to confirm the upload. If you type anything else, the upload will skip the directory.

You can skip all directory prompts by specifying the `--no-prompt` flag.
```bash
$ sftp-upload -username <username> --no-prompt path/to/file_1.csv path/to/dir
```

The command will upload all supported files specified in paths to the sftp server.

## License

[MIT](LICENSE)
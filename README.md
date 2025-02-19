# sftp-upload

Example code to upload files to Dreamdata(c) custom crm sftp server.

If you have any specific requirements, you will need to modify the code to suit your needs.

source code in [GO](main.go) and [Python](main.py)

## Installation

Download the [known_hosts](known_hosts) file.

You can install this script, as is, to use it as a CLI:

```bash
$ go install github.com/dreamdata-io/sftp-upload@latest
```

## Usage

### cli
```
$ sftp-upload -username <username> path/to/file1 path/to/dir
# you will be prompted for the password
Enter your password for testmarketo_biz:
```

The command will upload all supported files specified in paths to the sftp server.

## License

[MIT](LICENSE)
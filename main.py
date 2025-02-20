import os
import subprocess
import sys
import tempfile
import paramiko
import argparse
import getpass
import importlib.metadata

REQUIREMENTS_FILE = 'requirements.txt'
KNOWN_HOSTS = """ftp.dreamdata.io ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDQQtl6pUnabMzYU/dmBlCmZ3ef8grqCDjnuWZBzevR9wiIbi6mWZhTLyRAlCTaB8EiLiBTeyGGRWXvQXSiXYoC7CpIu6x0u26XZIL6kOBt9qRo2DjIfMZuLOar191Zcj1WnANrzFrjw6cxBsNOS6E7hjzCfKqPU2b/ldLGBptm2C7gMUQSULaNzPLOqfhAC2TW5a+Ah9nLyZvxJL7+7fL3u76hIOS0uJqN4nsqncC4ql14GWr+zA2wltRVoYywAHqrDQqkfC/IDeURQzpzjb1WW+5vt51mVye+ULwmJxQXredo4X4AAdTNm8zyxnxZvKR7SbBfDlpxo3a3GF8Ohvc6wkBp8OnLdJexIw+ejtDZZiqWX4qqtOjUAS61a6u2wjgjTX7PpI2t4KVoZ09rLDkvDRu3bTKuj6FZ6qY7zq96Uo7W1guAEEgKr5NfgY3zcxxmFFL+SR5Yj+v06vPiA6AVaVOusz2Mfst0cnAyV7SuY/0CmrmS7S5XQbRsk5cHjhk=
ftp.dreamdata.io ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBGBFkxOWRqLeWzGD5xhkIlheQ9Kg3Z6fehdJ1RUYrHXzISrhr0NaoAWL9ivJMQjazCi1ouWhRV3wAMhxVvo7Ga4=
ftp.dreamdata.io ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDQEtBMtsoTrJYrHL23oxpoYxclEsC8KCLU336xh3Uzk"""

try:
    with open(REQUIREMENTS_FILE, 'r') as f:
        requirements = f.read().splitlines()

        for requirement in requirements:
            try:
                importlib.metadata.version(requirement.split('==')[0])
            except importlib.metadata.PackageNotFoundError:
                print(f"Installing requirement: {requirement}")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', REQUIREMENTS_FILE])
            except importlib.metadata.VersionConflict as e:
                print(f"Version conflict: {e}")
                sys.exit(1)

except subprocess.CalledProcessError as e:
    print(f"Failed to install requirements: {e}")
    sys.exit(1)


def prompt_bool(prompt):
    response = input(prompt).strip().lower()
    return response == 'y' or response == 'yes'


def is_supported_file_type(filename):
    return filename.endswith(('.csv', '.jsonl', '.ndjson', '.parquet'))


def upload_file(sftp, local_path, remote_path):
    print(f"Uploading file: {local_path}")
    sftp.put(local_path, remote_path)
    print(f"File {local_path} uploaded successfully.")


def upload(sftp, local_dir, remote_dir, no_prompt):
    for root, dirs, files in os.walk(local_dir):
        for d in dirs:
            if not no_prompt and not prompt_bool(f"You will upload all files in {os.path.join(root, d)}. Continue? (y/[n])"):
                dirs.remove(d)
        for file in files:
            local_path = os.path.join(root, file)
            remote_path = os.path.join(remote_dir, os.path.relpath(local_path, local_dir))
            if is_supported_file_type(local_path):
                upload_file(sftp, local_path, remote_path)
                print(f"Uploading file: {local_path} to {remote_path}")


def start_ssh(host, username, password):
    ssh = paramiko.SSHClient()
    with tempfile.NamedTemporaryFile(mode='w') as temp_known_hosts:
        temp_known_hosts.write()
        temp_known_hosts.flush()
        ssh.load_system_host_keys(temp_known_hosts.name)
    ssh.connect(host, username=username, password=password, look_for_keys=False, allow_agent=False)
    return ssh


def main():
    parser = argparse.ArgumentParser(description='Upload your CRM data to Dreamdata via SFTP.', usage='''python main.py -username <username> <path> [<path> ...]''')
    parser.add_argument('-username', required=True, help='SFTP server username')
    parser.add_argument('--no-prompt', default=False, help='Do not prompt for confirmation before uploading files')
    parser.add_argument('paths', nargs='*', help='Path to a directory or file to upload')
    args = parser.parse_args()

    password = getpass.getpass(f'Enter your password for {args.username}: ')

    host = 'ftp.dreamdata.io'
    ssh = start_ssh(host, args.username, password)
    sftp = ssh.open_sftp()

    if not args.paths:
        print("No paths specified. Aborting.")
        return

    for path in args.paths:
        if os.path.isdir(path):
            upload(sftp, path, path, args.no_prompt)
        elif os.path.isfile(path) and is_supported_file_type(path):
            upload_file(sftp, path, path)

    try:
        sftp.close()
        ssh.close()
    except Exception as e:
        print(f"Error closing connection: {e}")
        sys.exit(1)

    print("All files uploaded successfully.")


if __name__ == '__main__':
    main()
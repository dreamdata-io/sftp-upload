import os
import paramiko
import argparse
import getpass

def prompt_bool(prompt):
    response = input(prompt).strip().lower()
    return response == 'y' or response == 'yes'


def prompt_password(prompt):
    return getpass.getpass(prompt)


def is_supported_file_type(file):
    return file.endswith(('.csv', '.jsonl', '.ndjson', '.parquet'))


def upload_file(sftp, local_path, remote_path):
    print(f"Uploading file: {local_path}")
    sftp.put(local_path, remote_path)
    print(f"File {local_path} uploaded successfully.")


def upload_dir(sftp, local_dir, remote_dir, no_prompt):
    if not no_prompt and not prompt_bool(f"{local_dir} is a directory.\nDo you want to upload the entire content of this directory? (y/[n]): "):
        print(f"Skipping directory: {local_dir}")
        return
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            remote_path = os.path.join(remote_dir, os.path.relpath(local_path, local_dir))
            if is_supported_file_type(local_path):
                upload_file(sftp, local_path, remote_path)
                print(f"Uploading file: {local_path} to {remote_path}")


def start_ssh(host, username, password):
    ssh = paramiko.SSHClient()
    ssh.load_host_keys('known_hosts')
    ssh.connect(host, username=username, password=password, look_for_keys=False, allow_agent=False)
    return ssh


def main():
    parser = argparse.ArgumentParser(description='Upload your CRM data to Dreamdata via SFTP.', usage='''python main.py -username <username> <path> [<path> ...]''')
    parser.add_argument('-username', required=True, help='SFTP server username')
    parser.add_argument('paths', nargs='*', help='Path to a directory or file to upload')
    args = parser.parse_args()

    password = prompt_password('Enter your SFTP server password: ')

    host = 'ftp.dreamdata.io'
    ssh = start_ssh(host, args.username, password)
    sftp = ssh.open_sftp()

    if not args.paths:
        print("No paths specified. Aborting.")
        return

    for path in args.paths:
        if os.path.isdir(path):
            upload_dir(sftp, path, path, args.no_prompt)
        elif os.path.isfile(path) and is_supported_file_type(path):
            upload_file(sftp, path, path)

    try:
        sftp.close()
        ssh.close()
    except Exception as e:
        print(f"Error closing connection: {e}")

    print("All files uploaded successfully.")


if __name__ == '__main__':
    main()
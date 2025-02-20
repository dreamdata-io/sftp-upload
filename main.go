package main

import (
	"bufio"
	"flag"
	"fmt"
	"github.com/pkg/sftp"
	"golang.org/x/crypto/ssh"
	"golang.org/x/crypto/ssh/knownhosts"
	"golang.org/x/term"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const (
	host = "ftp.dreamdata.io"
	port = 22

	knownHosts = `ftp.dreamdata.io ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDQQtl6pUnabMzYU/dmBlCmZ3ef8grqCDjnuWZBzevR9wiIbi6mWZhTLyRAlCTaB8EiLiBTeyGGRWXvQXSiXYoC7CpIu6x0u26XZIL6kOBt9qRo2DjIfMZuLOar191Zcj1WnANrzFrjw6cxBsNOS6E7hjzCfKqPU2b/ldLGBptm2C7gMUQSULaNzPLOqfhAC2TW5a+Ah9nLyZvxJL7+7fL3u76hIOS0uJqN4nsqncC4ql14GWr+zA2wltRVoYywAHqrDQqkfC/IDeURQzpzjb1WW+5vt51mVye+ULwmJxQXredo4X4AAdTNm8zyxnxZvKR7SbBfDlpxo3a3GF8Ohvc6wkBp8OnLdJexIw+ejtDZZiqWX4qqtOjUAS61a6u2wjgjTX7PpI2t4KVoZ09rLDkvDRu3bTKuj6FZ6qY7zq96Uo7W1guAEEgKr5NfgY3zcxxmFFL+SR5Yj+v06vPiA6AVaVOusz2Mfst0cnAyV7SuY/0CmrmS7S5XQbRsk5cHjhk=
ftp.dreamdata.io ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBGBFkxOWRqLeWzGD5xhkIlheQ9Kg3Z6fehdJ1RUYrHXzISrhr0NaoAWL9ivJMQjazCi1ouWhRV3wAMhxVvo7Ga4=
ftp.dreamdata.io ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDQEtBMtsoTrJYrHL23oxpoYxclEsC8KCLU336xh3Uzk`
)

var (
	username   string
	password   string
	help       bool
	paths      []string
	noPrompt   bool
	sftpClient *sftp.Client
	sshClient  *ssh.Client
	err        error
)

func init() {
	flag.Usage = func() {
		fmt.Println(`Usage: ./upload -username <username> <path> [<path> ...]

Upload your CRM data to Dreamdata via SFTP. You can specify one or more files and directories to upload. 

Flags:
  username  SFTP server username (required)
  password  SFTP server password (required)

Positional arguments:
  <path>  Path to a directory or file to upload`)
		os.Exit(0)
	}
	// Define command-line flags
	flag.StringVar(&username, "username", "", "SFTP server username")
	flag.BoolVar(&noPrompt, "no-prompt", false, "Skip all prompts")
	flag.BoolVar(&help, "help", false, "Show help")
	flag.Parse()

	if help || username == "" {
		if username == "" {
			fmt.Println("Error: username and password are required")
			fmt.Println()
		}
		flag.Usage()
		os.Exit(1)
	}

	// Get positional arguments
	paths = flag.Args()
	if len(paths) == 0 {
		fmt.Println("No files or directories specified.")
		os.Exit(1)
	}

	password = promptPassword(fmt.Sprintf("Enter your password for %s: ", username))
}

func main() {
	// Establish SSH connection
	sshConfig := &ssh.ClientConfig{
		User: username,
		Auth: []ssh.AuthMethod{
			ssh.Password(password),
		},
		HostKeyCallback:   loadHostKeys(),
		HostKeyAlgorithms: []string{"ssh-ed25519"},
		Timeout:           30 * time.Second,
	}

	sshClient, err = ssh.Dial("tcp", fmt.Sprintf("%s:%d", host, port), sshConfig)
	if err != nil {
		panic(fmt.Sprintf("Failed to dial SSH: %v", err))
	}
	defer sshClient.Close()

	// Create SFTP client
	sftpClient, err = sftp.NewClient(sshClient)
	if err != nil {
		panic(fmt.Sprintf("Failed to create SFTP client: %v", err))
	}
	defer sftpClient.Close()

	for _, root := range paths {
		err = filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}

			// Create directories on the remote server
			if info.IsDir() {
				if !promptBool(fmt.Sprintf("You will upload all files in %s. Continue? (y/[n]): ", path)) {
					return filepath.SkipDir
				}
				if err := sftpClient.MkdirAll(path); err != nil {
					return fmt.Errorf("failed to create directory %s: %v", path, err)
				}
				fmt.Println(fmt.Sprintf("Directory %s created successfully.", path))
				return nil
			}

			// Only upload supported files
			if isSupportedFileType(path) {
				return uploadFile(path)
			}
			return nil
		})

		if err != nil {
			fmt.Printf("failed to upload files %s: %v", root, err)
			os.Exit(1)
		}
	}
	fmt.Println("All files uploaded successfully.")
}

func promptBool(prompt string) bool {
	if noPrompt {
		return true
	}
	fmt.Print(prompt)
	response, _ := bufio.NewReader(os.Stdin).ReadString('\n')
	response = strings.ToLower(strings.TrimSpace(response))
	return response == "y" || response == "yes"
}

func promptPassword(prompt string) string {
	fmt.Print(prompt)
	bytePassword, _ := term.ReadPassword(int(os.Stdin.Fd()))
	fmt.Println()
	return string(bytePassword)
}

func loadHostKeys() ssh.HostKeyCallback {
	// Create a temporary file
	tmpFile, err := os.CreateTemp("", "*")
	if err != nil {
		fmt.Println("Error creating temp hosts file:", err)
		os.Exit(1)
	}
	defer os.Remove(tmpFile.Name()) // Clean up the file afterward

	// Write the in-memory known_hosts data to the temporary file
	if _, err := tmpFile.Write([]byte(knownHosts)); err != nil {
		fmt.Println("Error writing to temp hosts file:", err)
		os.Exit(1)
	}
	tmpFile.Close()

	callback, err := knownhosts.New(tmpFile.Name())
	if err != nil {
		fmt.Println("Failed to load known hosts:", err)
		os.Exit(1)
	}

	return callback
}

func uploadFile(path string) error {
	fmt.Println("Uploading file:", path)
	srcFile, err := os.Open(path)
	if err != nil {
		return fmt.Errorf("failed to open file %s: %v", path, err)
	}
	defer srcFile.Close()

	dstFile, err := sftpClient.Create(path)
	if err != nil {
		return fmt.Errorf("failed to create file %s: %v", path, err)
	}
	defer dstFile.Close()

	if _, err := dstFile.ReadFrom(srcFile); err != nil {
		return fmt.Errorf("failed to copy file content to %s: %v", path, err)
	}

	fmt.Printf("File %s uploaded successfully.\n", path)
	return nil
}

func isSupportedFileType(file string) bool {
	return strings.HasSuffix(file, ".csv") || strings.HasSuffix(file, ".jsonl") || strings.HasSuffix(file, ".ndjson") || strings.HasSuffix(file, ".parquet")
}

import os
import csv
import random
import string

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_csv_file(file_path, num_columns, min_size_mb, max_size_mb):
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        headers = [f'Column{i+1}' for i in range(num_columns)]
        writer.writerow(headers)

        file_size = random.randint(min_size_mb, max_size_mb) * 1024 * 1024
        while os.path.getsize(file_path) < file_size:
            row = [generate_random_string(10) for _ in range(num_columns)]
            writer.writerow(row)

def create_nested_directories(base_dir, depth, num_columns, min_size_mb, max_size_mb):
    for i in range(random.randint(1, 3)):
        if depth == 0 or random.randint(0,1) == 1:
            file_name = f'file_{i+1}.csv'
            file_path = os.path.join(base_dir, file_name)
            generate_csv_file(file_path, num_columns, min_size_mb, max_size_mb)
        else:
            sub_dir = os.path.join(base_dir, f'dir_{i+1}')
            os.makedirs(sub_dir, exist_ok=True)
            create_nested_directories(sub_dir, depth - 1, num_columns, min_size_mb, max_size_mb)

if __name__ == '__main__':
    base_dir = 'example_data'
    os.makedirs(base_dir, exist_ok=True)
    create_nested_directories(base_dir, 2, 10, 40, 150)
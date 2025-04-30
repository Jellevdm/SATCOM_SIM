import csv

def read_csv(file_path, delimiter=';'):
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=delimiter)
        data = [row for row in reader]
    return data



output_data = [["Time", "Channel B", "Channel D"]] # Initialize with header

number_of_files = 230  # Number of pico files to read

folder_name = 'BER and trimming/pico'  # Folder name where the files are located

for i in range(number_of_files):  # 0-tot
    csv_file_path = f'{folder_name}/pico_{i+1:03}.csv'  # Format i+1 as a zero-padded 3-digit number
    csv_data = read_csv(csv_file_path)

    for row in csv_data[3::10000]:  # Start from the 4th row and take every 100th row
        row = [value.replace(',', '.') if isinstance(value, str) else value for value in row]  # Replace commas with dots
        row[0] = str(i) + row[0]  # Add i to the first value in each row
        row[0] = str(float(row[0]) / 1000)  # Divide the first column by 1000
        output_data.append(row)


# Writing rows to a new CSV file
output_file_path = 'BER and trimming/pico_total.csv'  # Replace with your desired output file path

with open(output_file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerows(output_data)

print(f"Data written to {output_file_path}")

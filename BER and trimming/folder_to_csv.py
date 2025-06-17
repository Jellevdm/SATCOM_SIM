import csv
import os

def read_csv(file_path, delimiter=';'):
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=delimiter)
            data = [row for row in reader]
        return data

def convert(folderpath, filename, new_csv_filename):

    with open(new_csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerow(["t", "B", "D"])

        number_of_files = len([f for f in os.listdir(folderpath) if f.startswith(f'{filename}_') and f.endswith('.csv')])
        for i in range(number_of_files):  # 0-tot
            csv_file_path = f'{folderpath}/{filename}_{i + 1:04}.csv'  # Format i+1 as a zero-padded 3-digit number
            csv_data = read_csv(csv_file_path)
            print(f"Saving {csv_file_path}")

            for row in csv_data[3::int(10000000/100000)]:  # retrieve data such that the sampling frequency is 100 kHz
                row = [value.replace(',', '.') if isinstance(value, str) else value for value in row]  # Replace commas with dots
                row[0] = float(i) + float(row[0]) + 5  # Add i to the first value in each row
                row[0] = str(float(row[0]) / 1000)  # Divide the first column by 1000
                writer.writerow(row)


def convert_loop():
    for folder in os.listdir("FinalPicoTest"):
        folderpath = f"FinalPicoTest/{folder}"
        filename = folder
        new_csv_filename = f"BER and trimming/Pico_one_csv/One_{filename}.csv"
        # if folder == "04_30-testing-std(0)-mean(0.1)":
        #      filename = "04_30-testing-std(0)-mean(0"
        print(f"converting{filename}")
        convert(folderpath, filename, new_csv_filename)



def fix_timestamps():
    for file in os.listdir("BER and trimming/Pico_one_csv"):
        filename = f"BER and trimming/Pico_one_csv/{file}"
        print(filename)

        with open(filename, mode='r', newline='', encoding='utf-8') as infile:
            reader = list(csv.reader(infile, delimiter=','))
        header, rows = reader[0], reader[1:]
        for idx, row in enumerate(rows):
            row[0] = f"{(idx + 1) * 0.00001:.5f}"
        with open(filename, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, delimiter=',')
            writer.writerow(header)
            writer.writerows(rows)

def append_bits():
    for file in os.listdir("BER and trimming/Pico_one_csv"):
        filename = f"BER and trimming/Pico_one_csv/{file}"
        print(filename)

        with open(filename, mode='r', newline='', encoding='utf-8') as infile:
            reader = list(csv.reader(infile, delimiter=','))
        header, rows = reader[0], reader[1:]

        # Add new columns to header
        header = ["t", "B", "D", "sent", "received"]

        for row in rows:
            del row[3:]
            # Ensure row has at least 3 columns
            # print(row)
            b_val = float(row[1]) if len(row) > 1 else 0.0
            d_val = float(row[2]) if len(row) > 2 else 0.0
            row.append("1" if b_val > 0.4 else "0")
            row.append("1" if d_val > 0.4 else "0")
            # print(row)

        with open(filename, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, delimiter=',')
            writer.writerow(header)
            writer.writerows(rows)


def append_error_bit():
    for file in os.listdir("BER and trimming/Pico_one_csv"):
        filename = f"BER and trimming/Pico_one_csv/{file}"
        print(filename)

        with open(filename, mode='r', newline='', encoding='utf-8') as infile:
            reader = list(csv.reader(infile, delimiter=','))
        header, rows = reader[0], reader[1:]

        # Add new columns to header
        header = ["t", "B", "D", "sent", "received", "XOR"]

        for row in rows:
            del row[5:]
            # Ensure row has at least 3 columns
            # print(row)
            sent_bit = int(row[3])
            received_bit = int(row[4])
            if sent_bit == received_bit:
                error_bit = 0
            else:
                error_bit = 1
            row.append(str(error_bit))
            # print(row)

        with open(filename, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, delimiter=',')
            writer.writerow(header)
            writer.writerows(rows)

            


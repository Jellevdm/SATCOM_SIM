import csv

# Function to convert signal to bit sequence
def signal_to_bits(signal):
    # Convert signal to bit: 1 if non-zero, 0 if zero or absent
    try:
        return 1 if float(signal) >= 1  else 0
    except ValueError:
        # Handle noise or invalid values by treating them as 0
        return 0

# Read the CSV file and extract the bit sequence from the second column
bit_sequences = []
csv_file_path = 'pico_total_trimmed.csv'  # Replace with the actual path to your CSV file

with open(csv_file_path, mode='r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # Skip the header row if it exists
    for row in csv_reader:
        signal_sent = row[1]  # Assuming the second column is at index 1
        bit_sequence = signal_to_bits(signal_sent)
        bit_sequences.append(bit_sequence)

print(bit_sequences[0:100])  # Print the first 10 bits for verification
print(len(bit_sequences))
print(bit_sequences.count(1)/len(bit_sequences)) # Percentage of 1s in the bit sequence
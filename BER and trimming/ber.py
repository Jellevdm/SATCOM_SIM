import csv

# Function to convert signal to bit sequence
def signal_to_bits(signal):
    # Convert signal to bit: 1 if non-zero, 0 if zero or absent
    try:
        return 1 if float(signal) >= 0.1  else 0  #SET THRESHOLD
    except ValueError:
        # Handle noise or invalid values by treating them as 0
        print(f"Invalid signal value: {signal}. Treating as 0.")
        return 0

# Read the CSV file and extract the bit sequence from the second column
bits_sent = []
bits_received = []
csv_file_path = 'BER and trimming/pico_total_trimmed.csv'  # Replace with the actual path to your CSV file

with open(csv_file_path, mode='r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # Skip the header row if it exists
    for row in csv_reader:
        signal_sent = row[1]  # Assuming the second column is at index 1
        signal_received = row[2]
        bit_sequence_sent = signal_to_bits(signal_sent)
        bit_sequence_received = signal_to_bits(signal_received)
        bits_sent.append(bit_sequence_sent)
        bits_received.append(bit_sequence_received)

count = 0

for i in range(len(bits_sent)):
    if bits_sent[i] != bits_received[i]:
        # If the bits are different, increment the count
        count += 1
        print(f"Error at index {i}: Sent {bits_sent[i]}, Received {bits_received[i]}")


print("Number of errors: ", count)  # Print the number of errors
print("Bit Error Rate (BER): ", count/len(bits_sent)*100, " %")  # Print the Bit Error Rate (BER)

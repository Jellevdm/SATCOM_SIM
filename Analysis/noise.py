import csv
import statistics


filename = 'pico_noise.csv'

# Import data from noise csv file
with open(filename, mode='r') as file:
    reader = csv.reader(file)
    next(reader)  # Skip the header row
    data = [row[2] for row in reader]
    data = list(map(lambda x: float(x) / 1000, data)) # Convert from mV to V

    std = statistics.stdev(data)


# count how many datapoint are above sigma range
sigma_range = 1 # how many sigmas to consider
above_sigma_range = len([x for x in data if x > sigma_range*std])


print(f"Number of data points above {sigma_range} sigma: {above_sigma_range}")
print(f"In percentage: {above_sigma_range/ len(data) * 100:.6f}%")


print(f"Threshold: {sigma_range*std}")
import pandas as pd
import numpy as np
import csv

header = ["std", "mean", "analysed bits"]
rows = []

def ber(std, mean, ndf=0, threshold=0.4):

    if ndf > 0:
        file = f"trimmed_std({std})-mean({mean})-ndf({ndf}).csv"
    else:
        file = f"trimmed_std({std})-mean({mean}).csv"


    file_path = f'BER and trimming/Pico_one_csv/{file}'  
    data = pd.read_csv(file_path)

    # Ensure the CSV has at least 3 columns
    if data.shape[1] < 3:
        raise ValueError("The CSV file must have at least 3 columns.")


    start = None
    stop = None


    # Extract columns
    x = data.iloc[start:stop, 0]
    y1 = data.iloc[start:stop, 1]
    y2 = data.iloc[start:stop, 2]
    b1 = data.iloc[start:stop, 3]
    b2 = data.iloc[start:stop, 4]
    e = data.iloc[start:stop, 5]


    count = 0
    previous = 0
    counts = []
    bb1 = []
    yy2 = []
    for i in range(len(b1)):
        current = b1[i]
        if current == previous:
            count += 1
        else:
            # print(count)
            counts.append(count)
            if count==47:
                bb1.append(previous)
                yy2.append(np.mean(y2[i-48:i-1]))
            count = 0
        previous = current

    bb2 = []
    for y in yy2:
        if y > threshold:
            bb2.append(1)
        else:
            bb2.append(0)

    ee = []
    for i in range(len(bb1)):
        ee.append(np.bitwise_xor(bb1[i], bb2[i]))

    return bb1, bb2, ee

for std in [0.1, 0.2, 0.3, 0.4, 0.5]:
    for mean in [0, 0.1, 0.2, 0.3, 0.4]:
        THRESHOLD = 0.1
        bb1, bb2, ee = ber(std, mean, threshold=THRESHOLD)

        n_errors = ee.count(1)
        n_correct = ee.count(0)
        total = len(ee)
        ratio = n_errors / total

        print(f"theshold: {THRESHOLD}, std: {std}, mean: {mean} --- {n_errors} errors out of {total} bits, ==== BER: {ratio} ====")

        values = [std, mean, total]
        row = [str(item) for item in values]
        # print(row)
        rows.append(row)


with open("used_bits.csv", mode='w', newline='', encoding='utf-8') as outfile:
    writer = csv.writer(outfile, delimiter=',')
    writer.writerow(header)
    writer.writerows(rows)

import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np



def trim(std, mean, ndf=0):
    if ndf > 0:
        file = f"One_04_30-testing-std({std})-mean({mean})-ndf({ndf}).csv"
    else:
        file = f"One_04_30-testing-std({std})-mean({mean}).csv"



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


    start_index = 0
    for i in range(len(b2)):
        received_bit = b2[i]
        if received_bit > 0.5:
            start_index = i
            break


    elist = []
    for error in e:
        elist.append(error)

    end_index = None
    for i in range(900_000, len(elist)):
        last_1000 = elist[-1000:]
        constant_above = True if last_1000.count(1) == 0 else False
        if constant_above:
            if i%100 == 0:
                # print(f"{elist[i:].count(0)} zeros out of {len(elist[i:])}")
                a = 0
            if abs(elist[i:].count(0) - len(elist[i:])) < 2:
                end_index = i
                break
        else:
            if i%100 == 0:
                # print(f"{elist[i:].count(0)} zeros out of {0.5*len(elist[i:])}")
                a = 0
            if abs(elist[i:].count(0) - 0.5*len(elist[i:])) < 2:
                end_index = i
                break


    trim = "yes"


    if trim == "yes":
        print("trimming")

        x = x[start_index:]
        y1 = y1[start_index:]
        y2 = y2[start_index:]
        b1 = b1[start_index:]
        b2 = b2[start_index:]
        e = e[start_index:]

        if end_index != None:
            x = x[:end_index-start_index]
            y1 = y1[:end_index-start_index]
            y2 = y2[:end_index-start_index]
            b1 = b1[:end_index-start_index]
            b2 = b2[:end_index-start_index]
            e = e[:end_index-start_index]



    count = 0
    previous = 0
    counts = []
    bb1 = []
    yy2 = []
    for i in range(start_index,len(b1)):
        current = b1[i]
        if current == previous:
            count += 1
        else:
            # print(count)
            counts.append(count)
            if count==47:
                bb1.append(previous)
                yy2.append(np.mean(y2[i-48:i-1]))
                # print(np.mean(y2[i-48:i-1]))
            count = 0
        previous = current



    bb2 = []
    for y in yy2:
        if y > 0.4:
            bb2.append(1)
        else:
            bb2.append(0)


    ee = []
    for i in range(start_index,len(bb1)):
        ee.append(np.bitwise_xor(bb1[i], bb2[i]))


    output_data = pd.DataFrame({
        'x': x,
        'y1': y1,
        'y2': y2,
        'b1': b1,
        'b2': b2,
        'e': e
    })
    output_file = f"BER and trimming/Pico_one_csv/trimmed_std({std})-mean({mean}).csv"
    output_data.to_csv(output_file, index=False)
    print(f"Data written to {output_file}")




for std in [0, 0.1, 0.2, 0.3, 0.4, 0.5]:
    for mean in [0, 0.1, 0.2, 0.3, 0.4]:
        trim(std, mean)
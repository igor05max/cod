import csv
import time as tm

PROZ = 1


start = tm.time()


step = 0.25
max_range = 20.0
edges = [round(i * step, 2) for i in range(0, int(max_range / step) + 1)]
intervals = [f"({edges[i]} – {edges[i+1]}]" for i in range(len(edges) - 1)]


counts = {key: 0 for key in intervals}
closed_counts = {key: 0 for key in intervals}

with open("SBER-1.txt", "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter='\t')
    header = next(reader)
    rows = list(reader)


temp_data = rows[0][1].split()[0]
dq = []

for i in range(1, len(rows)):
    prev_row = rows[i - 1]
    row = rows[i]

    try:
        date = row[0].split()[0]
        high = float(row[3])
        low = float(row[4])
        close = float(row[5])
        prev_close = float(prev_row[5])
        prev_date = prev_row[0].split()[0]
    except ValueError:
        continue

    if temp_data != date:
        temp_data = date
        dq.clear()
        continue
    while dq and high >= (dq[-1][0] - dq[-1][1]) * PROZ + dq[-1][1]:
        pc, l, key = dq.pop()
        closed_counts[key] += 1


    if low < prev_close and close < prev_close:
        change = abs((low - prev_close) / prev_close * 100)
        key = ""
        for j in range(len(edges) - 1):
            if edges[j] < change <= edges[j + 1]:
                key = f"({edges[j]} – {edges[j + 1]}]"
                counts[key] += 1
                break
        if not key:
            continue
        dq.append((prev_close, low, key))
        dq.sort(reverse=True)


with open("SBER_1_stats.csv", "w", encoding="utf-8") as out:
    out.write("Интервал,Количество,Закрытые\n")
    for key in intervals:
        count = counts[key]
        closed = closed_counts[key]
        if count > 0:
            out.write(f"{key},{count},{closed}\n")
endd = tm.time()

print(endd - start)

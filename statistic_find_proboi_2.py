import csv

step = 0.25
max_range = 20.0
edges = [round(i * step, 2) for i in range(0, int(max_range / step) + 1)]
intervals = [f"({edges[i]} – {edges[i+1]}]" for i in range(len(edges) - 1)]


counts = {key: 0 for key in intervals}
closed_counts = {key: 0 for key in intervals}

with open("SBER_250115_250411.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)

for i in range(1, len(rows)):
    prev_row = rows[i - 1]
    row = rows[i]

    try:
        date = row[2]
        time = row[3]
        high = float(row[5])
        low = float(row[6])
        close = float(row[7])
        prev_close = float(prev_row[7])
        prev_date = prev_row[2]
    except ValueError:
        continue

    if low < prev_close and high <= prev_close:
        change = abs((low - prev_close) / prev_close * 100)

        for j in range(len(edges) - 1):
            if edges[j] < change <= edges[j + 1]:
                key = f"({edges[j]} – {edges[j + 1]}]"
                counts[key] += 1

                restored = False
                for k in range(i + 1, len(rows)):
                    future_row = rows[k]
                    if future_row[2] != date:
                        break
                    try:
                        future_high = float(future_row[5])
                        future_close = float(future_row[7])
                    except ValueError:
                        continue
                    if future_high >= prev_close or future_close >= prev_close:
                        restored = True
                        break

                if restored:
                    closed_counts[key] += 1
                break

with open("interval_restore_stats.csv", "w", encoding="utf-8") as out:
    out.write("Интервал,Количество,Закрытые\n")
    for key in intervals:
        count = counts[key]
        closed = closed_counts[key]
        if count > 0:
            out.write(f"{key},{count},{closed}\n")

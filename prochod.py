import csv
import time as tm
from datetime import datetime, timedelta

step = 0.25  # процент падения
count_buy = 1

start = tm.time()

money = 1_000_000
qty = 0

lim_buy = []   # лимитные заявки на покупку (активные)
lim_sell = []  # лимитные заявки на продажу (после покупки)
historical = []


date_start = datetime(2025, 1, 1)
date_end = datetime(2025, 7, 1)


with open("historical_data/SBER-1.txt", "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter='\t')
    header = next(reader)
    rows = list(reader)

for i in range(1, len(rows)):
    prev_row = rows[i - 1]
    row = rows[i]

    try:

        date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        if date < date_start or date > date_end:
            continue
        high = float(row[3])
        low = float(row[4])
        close = float(row[5])

        prev_close = float(prev_row[5])
    except ValueError:
        continue

    # Добавляем лимитную заявку на покупку, если цена упала на step%
    price_buy = round(prev_close * (1 - step / 100), 2)
    buy_date = date + timedelta(minutes=1)  # заявка активна только на следующий день

    lim_buy.append({
        "date": buy_date,
        "price": price_buy,
        "count": count_buy,
        "priv_price": prev_close
    })

    # Проверяем исполнение заявок на покупку
    for i2 in reversed(range(len(lim_buy))):
        buy_order = lim_buy[i2]
        if buy_order["date"] == date and low <= buy_order["price"]:
            # заявка исполнилась
            money -= (buy_order["price"] * buy_order["count"])
            qty += buy_order["count"]

            # создаем заявку на продажу по цене close предыдущей свечи
            lim_sell.append({
                "date": date,  # продавать можно только на следующий день
                "price": buy_order["priv_price"],
                "count": buy_order["count"],
                "buy_price": buy_order["price"],
                "buy_date": date
            })

            lim_buy.pop(i2)
        elif buy_order["date"] < date:
            # истек срок действия заявки
            lim_buy.pop(i2)


    # Проверяем исполнение заявок на продажу
    for ii in reversed(range(len(lim_sell))):
        sell_order = lim_sell[ii]

        if sell_order["date"] != date and high >= sell_order["price"]:
            money += sell_order["price"] * sell_order["count"]
            qty -= sell_order["count"]

            historical.append({
                "data_buy": sell_order["buy_date"],
                "price_buy": sell_order["buy_price"],
                "data_sell": date,
                "price_sell": sell_order["price"],
                "count": sell_order["count"]
            })

            lim_sell.pop(ii)


# Выводим результат
with open("SBER_1_stats.csv", "w", encoding="utf-8") as out:
    out.write("дата,кол-во дней,покупка,продажа, \n")
    for lim in historical:
        delta = (lim['data_sell'] - lim['data_buy']).days + 1
        out.write(f"{lim['data_buy']} - {lim['data_sell']},{delta},{lim['price_buy']},{lim['price_sell']},{money}\n")



endd = tm.time()
print(f"Готово за {round(endd - start, 2)} сек")
print(money, qty * close, money+qty*close)
import requests
import pandas as pd
from datetime import datetime, timedelta
from io import StringIO
import os
import time

# === СОЗДАЁМ ПАПКУ ДЛЯ ВЫГРУЗОК ===
output_folder = 'finam_bonds_data'
os.makedirs(output_folder, exist_ok=True)

# === ДЕЛИМ ПЕРИОД ПО 3 МЕСЯЦА ===
def daterange(start_date, end_date, step_months=3):
    current = start_date
    while current < end_date:
        month = current.month - 1 + step_months
        year = current.year + month // 12
        month = month % 12 + 1
        day = min(current.day, 28)  # избежать 31 февраля
        next_date = datetime(year, month, day)
        if next_date > end_date:
            next_date = end_date
        yield current, next_date
        current = next_date + timedelta(days=1)

# === ФУНКЦИЯ СКАЧИВАНИЯ И СОХРАНЕНИЯ ДАННЫХ ===
def download_bond_data(code, em,
                       start=datetime(2024, 7, 1),
                       end=datetime(2025, 7, 1)):

    def download_finam_data(em, code, start_date, end_date):
        base_url = "https://export.finam.ru/export9.out"
        params = {
            "apply": 0,
            "p": 2,
            "e": ".csv",
            "dtf": 2,
            "tmf": 1,
            "MSOR": 0,
            "mstimever": "on",
            "sep": 3,
            "sep2": 1,
            "datf": 1,
            "at": 1,
            "from": start_date.strftime("%d.%m.%Y"),
            "to": end_date.strftime("%d.%m.%Y"),
            "em": em,
            "code": code,
            "f": f"{code}_{start_date.strftime('%y%m%d')}_{end_date.strftime('%y%m%d')}",
            "cn": code,
            "market": "undefined",
            "yf": start_date.year,
            "yt": end_date.year,
            "df": start_date.day,
            "dt": end_date.day,
            "mf": start_date.month - 1,
            "mt": end_date.month - 1,
            "token": "",
        }
        response = requests.get(base_url, params=params)
        if response.status_code == 200 and response.text.strip():
            return response.text
        else:
            print(f"❌ Ошибка загрузки {code}: HTTP {response.status_code}")
            return None

    all_parts = []
    for s, e in daterange(start, end):
        print(f"📥 Загружаем: {code} — {s.strftime('%d.%m.%Y')} — {e.strftime('%d.%m.%Y')}")
        csv_text = download_finam_data(em, code, s, e)
        if csv_text:
            df = pd.read_csv(StringIO(csv_text), sep=';')
            all_parts.append(df)
        time.sleep(0.3)

    if all_parts:
        full_df = pd.concat(all_parts, ignore_index=True)
        output_path = os.path.join(output_folder, f"{code}.csv")
        full_df.to_csv(output_path, index=False)
        print(f"✅ Данные для {code} сохранены: {output_path}")
    else:
        print(f"⚠️ Данных для {code} не найдено.")

download_bond_data(code="SU26221RMFS09", em=474454)

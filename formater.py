import pandas as pd
from datetime import datetime

# Загрузка исходного CSV
input_file = "data/RU000A107RZ0_250401_250602.csv"   # замените на путь к вашему файлу
output_file = "data/RU000A107RZ0_250401_250602_f.csv"


# Читаем файл, пропуская заголовок, если он есть
df = pd.read_csv(input_file, skiprows=1, header=None, names=[
    "ticker", "per", "date", "time", "open", "high", "low", "close", "volume"
])

# Убираем пробелы и добавляем ведущие нули, если нужно
df["date"] = df["date"].astype(str).str.zfill(6)
df["time"] = df["time"].astype(str).str.zfill(6)

# Формируем datetime
def to_datetime(row):
    try:
        return datetime.strptime(row["date"] + row["time"], "%y%m%d%H%M%S")
    except Exception as e:
        print(f"Ошибка в строке: {row['date']} {row['time']} -> {e}")
        return None

df["datetime"] = df.apply(to_datetime, axis=1)

# Удаляем строки с ошибками в дате
df = df.dropna(subset=["datetime"])

# Сортируем по времени (по желанию)
df = df.sort_values("datetime")

# Формируем финальный датафрейм с нужным порядком столбцов
final_df = df[["datetime", "open", "high", "low", "close", "volume"]]

# Сохраняем в нужном формате
final_df.to_csv(output_file, index=False)

print(f"✅ Готово! Результат сохранён в {output_file}")

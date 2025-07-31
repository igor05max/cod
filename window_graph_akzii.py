import sys
import time as tm
import os
import pandas as pd
import mplfinance as mpf
from PyQt5.QtWidgets import (
    QStatusBar,
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QDateEdit, QPushButton, QTextEdit,
    QDoubleSpinBox, QComboBox, QMessageBox
)
from PyQt5.QtCore import QDate
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
import matplotlib.pyplot as plt


class DropAnalyzer(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Свечной график и анализ падений")
        self.setGeometry(100, 100, 1400, 800)

        self.data_folder = "data"  # Папка с файлами
        self.current_file = ""
        self.df = pd.DataFrame()
        self.counts = {}
        self.closed_counts = {}
        self.details_by_interval = {}
        self.analyzed_df = pd.DataFrame()

        # Значения по умолчанию
        self.step = 0.25
        self.max_range = 20.0
        edges_default = [round(i * self.step, 2) for i in range(0, int(self.max_range / self.step) + 1)]
        self.default_intervals = [f"{edges_default[i]} {edges_default[i + 1]}" for i in range(len(edges_default) - 1)]
        self.intervals = []
        self.edges = []

        self.init_ui()
        self.setStatusBar(QStatusBar())


    def load_data(self, path):
        df = pd.read_csv(path, delimiter='\t')
        df.columns = [col.strip() for col in df.columns]
        df['Datetime'] = pd.to_datetime(df[df.columns[0]])
        df['Open'] = pd.to_numeric(df[df.columns[2]], errors='coerce')
        df['High'] = pd.to_numeric(df[df.columns[3]], errors='coerce')
        df['Low'] = pd.to_numeric(df[df.columns[4]], errors='coerce')
        df['Close'] = pd.to_numeric(df[df.columns[5]], errors='coerce')
        df = df.dropna()
        df.set_index('Datetime', inplace=True)
        return df[['Open', 'High', 'Low', 'Close']]

    def init_ui(self):
        main_layout = QHBoxLayout()
        layout = QVBoxLayout()

        controls = QHBoxLayout()

        # === Выбор файла ===
        controls.addWidget(QLabel("Файл:"))
        self.file_selector = QComboBox()
        self.populate_file_list()
        self.file_selector.currentIndexChanged.connect(self.on_file_selected)
        controls.addWidget(self.file_selector)

        # === Дата с ===
        controls.addWidget(QLabel("С:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        controls.addWidget(self.date_from)

        # === Дата по ===
        controls.addWidget(QLabel("По:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        controls.addWidget(self.date_to)

        # === Интервалы ===
        controls.addWidget(QLabel("Фильтр падения (разница в %):"))
        self.interval_combo = QComboBox()
        controls.addWidget(self.interval_combo)

        # === PROZ ===
        controls.addWidget(QLabel("PROZ (в долях, от 0 до 1):"))
        self.proz_input = QDoubleSpinBox()
        self.proz_input.setValue(1.0)
        self.proz_input.setSingleStep(0.01)
        self.proz_input.setMinimum(0.0)
        self.proz_input.setMaximum(1.0)
        controls.addWidget(self.proz_input)

        # === Кнопки ===
        self.analyze_button = QPushButton("Анализировать")
        self.analyze_button.clicked.connect(self.run_analysis)
        controls.addWidget(self.analyze_button)

        self.plot_button = QPushButton("Обновить график")
        self.plot_button.clicked.connect(self.plot_graph)
        controls.addWidget(self.plot_button)

        layout.addLayout(controls)

        # === Текстовый вывод ===
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output, stretch=1)

        # === График ===
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, stretch=2)

        # === Правая панель: интервалы ===
        sidebar = QVBoxLayout()
        sidebar.addWidget(QLabel("Интервалы (min max на строку):"))
        self.interval_editor = QTextEdit()
        self.interval_editor.setPlainText("\n".join(self.default_intervals))
        sidebar.addWidget(self.interval_editor)

        # === Общий Layout ===
        main_layout.addLayout(layout, stretch=4)
        main_layout.addLayout(sidebar, stretch=1)

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        self.interval_combo.currentIndexChanged.connect(self.update_output)

    def populate_file_list(self):
        self.file_selector.clear()
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        files = [f for f in os.listdir(self.data_folder) if f.endswith(".txt")]
        self.file_selector.addItems(files)
        if files:
            self.on_file_selected(0)

    def on_file_selected(self, index):
        filename = self.file_selector.currentText()
        if filename:
            path = os.path.join(self.data_folder, filename)
            self.df = self.load_data(path)
            self.current_file = filename
            if not self.df.empty:
                start_date = self.df.index.min().strftime('%Y-%m-%d')
                end_date = self.df.index.max().strftime('%Y-%m-%d')
                self.statusBar().showMessage(f"Данные в файле: с {start_date} по {end_date}")
            else:
                self.statusBar().showMessage(f"Файл: {filename} | Нет данных")


    def run_analysis(self):

        # self.message.clear()
        PROZ = self.proz_input.value()
        self.output.clear()

        self.counts = {}
        self.closed_counts = {i: {} for i in range(1, 6)}
        self.not_closed_count = {}
        self.edges = []
        self.intervals = []

        # Чтение интервалов
        interval_lines = self.interval_editor.toPlainText().splitlines()
        for line in interval_lines:
            try:
                left, right = map(float, line.strip().split())
                if left < right:
                    self.edges.append(left)
                    self.edges.append(right)
            except:
                continue

        self.edges = sorted(set(self.edges))
        self.intervals = [f"({self.edges[i]} – {self.edges[i+1]}]" for i in range(len(self.edges) - 1)]
        # self.message = {key: [] for key in self.intervals}
        self.counts = {key: 0 for key in self.intervals}
        self.closed_counts = {i: {key: 0 for key in self.intervals} for i in range(1, 6)}
        self.not_closed_count = {key: 0 for key in self.intervals}

        self.interval_combo.clear()
        self.interval_combo.addItems(self.intervals)

        # фильтрация по дате
        from_date = self.date_from.date().toPyDate()
        to_date = self.date_to.date().toPyDate()
        df = self.df[(self.df.index.date >= from_date) & (self.df.index.date <= to_date)].copy()
        self.analyzed_df = df.copy()

        if df.empty:
            self.output.setText("Нет данных в выбранном диапазоне.")
            return

        rows = df.reset_index().values.tolist()
        if not rows:
            self.output.setText("Нет данных для анализа.")
            return

        dq = []
        temp_data = rows[0][0].date()

        for i in range(1, len(rows)):
            prev_row = rows[i - 1]
            row = rows[i]

            try:
                date = row[0].date()
                high = float(row[2])
                low = float(row[3])
                close = float(row[4])
                prev_close = float(prev_row[4])
                prev_date = prev_row[0].date()
                time_data = row[0].time()
            except:
                continue

            # Удаление старых (не восстановленных)
            if temp_data != date:
                for idx in reversed(range(len(dq))):
                    pc, l, key, day, time = dq[idx]
                    if (date - day).days > 4:
                        dq.pop(idx)
                        self.not_closed_count[key] += 1
                        # self.message[key].append(
                        #     f"– не восстановилось {day} {time}, с {pc:.2f} до {l:.2f}"
                        # )
                temp_data = date

            # Проверка на восстановление
            for idx in reversed(range(len(dq))):
                pc, l, key, day, time = dq[idx]
                recovery_level = (pc - l) * PROZ + l
                if high >= recovery_level:
                    dq.pop(idx)
                    delta_days = (date - day).days + 1
                    if delta_days in self.closed_counts:
                        self.closed_counts[delta_days][key] += 1
                        # self.message[key].append(
                        #     f"📉 {day} {time} падение с {pc:.2f} до {l:.2f}, восстановилось {date} {time_data} (цена: {high:.2f})"
                        # )

            # Новое падение
            if low < prev_close and close < prev_close and prev_date == temp_data:
                change = abs((low - prev_close) / prev_close * 100)
                key = ""
                for j in range(len(self.edges) - 1):
                    if self.edges[j] < change <= self.edges[j + 1]:
                        key = f"({self.edges[j]} – {self.edges[j + 1]}]"
                        break
                if key:
                    self.counts[key] += 1
                    dq.append((prev_close, low, key, date, time_data))
                    dq.sort(reverse=True)

        self.update_output()



    def update_output(self):

        self.output.clear()
        if not self.df.empty:
            start_date = self.df.index.min().strftime('%Y-%m-%d')
            end_date = self.df.index.max().strftime('%Y-%m-%d')
            self.output.append(f"📅 Данные в файле: с {start_date} по {end_date}\n")



        self.output.append("📊 Сводка по всем интервалам:\n")
        self.output.append("Интервал       Количество  Закрытые 1  Закрытые 2  Закрытые 3  Закрытые 4  Закрытые 5  Не закрытые")

        for key in self.intervals:
            count = self.counts.get(key, 0)
            c1 = self.closed_counts[1].get(key, 0)
            c2 = self.closed_counts[2].get(key, 0)
            c3 = self.closed_counts[3].get(key, 0)
            c4 = self.closed_counts[4].get(key, 0)
            c5 = self.closed_counts[5].get(key, 0)
            nc = self.not_closed_count.get(key, 0)

            if count > 0:
                self.output.append(f"{key:<15} {count:<11} {c1:<10} {c2:<10} {c3:<10} {c4:<10} {c5:<10} {nc}")
        selected = self.interval_combo.currentText()
        self.output.append(f"\n📋 Детали по интервалу {selected}:\n")
        # for msg in self.message.get(selected, []):
        #     self.output.append(msg)


    def plot_graph(self):
        if self.analyzed_df.empty:
            QMessageBox.warning(self, "Нет данных", "Сначала выполните анализ.")
            return

        self.figure.clf()
        ax = self.figure.add_subplot(111)
        mpf.plot(
            self.analyzed_df,
            type='candle',
            ax=ax,
            style='charles',
            datetime_format='%Y-%m-%d %H:%M',
            xrotation=45
        )
        self.figure.subplots_adjust(bottom=0.25)
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DropAnalyzer()
    window.show()
    sys.exit(app.exec_())

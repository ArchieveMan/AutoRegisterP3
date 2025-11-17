import random, os, datetime, json
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QShortcut, QRegularExpressionValidator, QFont
from PyQt6.QtWidgets import QApplication,QMainWindow
from PyQt6.QtCore import QRegularExpression, Qt

folder_path = r"C:\Users\Arhivskaner\Desktop\scan"
# folder_path = r"E:"

class RightClickButton(QtWidgets.QPushButton):
    def __init__(self, *args, toggle_callback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.toggle_callback = toggle_callback
        self.click_counter = 0
        self.click_timer = QtCore.QTimer()
        self.click_timer.setInterval(300)
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.reset_counter)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            self.click_counter += 1
            if not self.click_timer.isActive():
                self.click_timer.start()
            if self.click_counter == 2:
                self.reset_counter()
                if self.toggle_callback:
                    self.toggle_callback()
        else:
            super().mousePressEvent(event)

    def reset_counter(self):
        self.click_counter = 0


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow") # узнать почему не отображается 
        MainWindow.resize(560, 650)            # узнать почему не отображается 

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.mode_daily_res_show = False  # False: show fake, True: show real

        # --- Дата (тексты)
        self.frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(10, 10, 120, 90))
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")

        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName("verticalLayout")

        self.start_date_label = QtWidgets.QLabel(parent=self.frame)
        self.start_date_label.setObjectName("start_date_label")
        self.verticalLayout.addWidget(self.start_date_label)

        self.end_date_label = QtWidgets.QLabel(parent=self.frame)
        self.end_date_label.setObjectName("end_date_label")
        self.verticalLayout.addWidget(self.end_date_label)

        # --- Дата (виджеты)
        self.frame_2 = QtWidgets.QFrame(parent=self.centralwidget)
        self.frame_2.setGeometry(QtCore.QRect(130, 10, 120, 90))
        self.frame_2.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_2.setObjectName("frame_2")

        self.start_dateEdit = QtWidgets.QDateEdit(parent=self.frame_2)
        self.start_dateEdit.setGeometry(QtCore.QRect(10, 10, 90, 30))
        self.start_dateEdit.setObjectName("start_dateEdit")
        self.start_dateEdit.setCalendarPopup(True)

        self.end_dateEdit = QtWidgets.QDateEdit(parent=self.frame_2)
        self.end_dateEdit.setGeometry(QtCore.QRect(10, 50, 90, 30))
        self.end_dateEdit.setObjectName("end_dateEdit")
        self.end_dateEdit.setCalendarPopup(True)

        self.start_dateEdit.dateChanged.connect(self.load_and_display_json_data)
        self.end_dateEdit.dateChanged.connect(self.load_and_display_json_data)
        # --- Фейковые результаты
        self.fake_results_textEdit = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.fake_results_textEdit.setGeometry(QtCore.QRect(10, 100, 540, 300))
        self.fake_results_textEdit.setObjectName("fake_results_textEdit")

        self.fake_daily_counter_btn = RightClickButton(
            parent=self.centralwidget,
            toggle_callback=self.toggle_mode
        )
        self.fake_daily_counter_btn.setGeometry(QtCore.QRect(270, 10, 280, 40))
        self.fake_daily_counter_btn.setObjectName("fake_daily_counter_btn")

        self.fake_daily_results_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.fake_daily_results_label.setGeometry(QtCore.QRect(270, 60, 280, 40))
        self.fake_daily_results_label.setObjectName("fake_daily_results_label")

        self.period_fake_results_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.period_fake_results_label.setGeometry(QtCore.QRect(10, 410, 540, 40))
        self.period_fake_results_label.setObjectName("period_fake_results_label")

        # --- Реальные результаты
        self.real_results_textEdit = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.real_results_textEdit.setGeometry(QtCore.QRect(270, 100, 280, 300))
        self.real_results_textEdit.setObjectName("real_results_textEdit")
        self.real_results_textEdit.hide()

        self.real_daily_counter_btn = RightClickButton(
            parent=self.centralwidget,
            toggle_callback=self.toggle_mode
        )
        self.real_daily_counter_btn.setGeometry(QtCore.QRect(270, 10, 280, 40))
        self.real_daily_counter_btn.setObjectName("real_daily_counter_btn")
        self.real_daily_counter_btn.hide()
        self.real_daily_counter_btn.clicked.connect(self.real_daily_count)

        self.real_daily_results_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.real_daily_results_label.setGeometry(QtCore.QRect(270, 60, 280, 40))
        self.real_daily_results_label.setObjectName("real_daily_results_label")
        self.real_daily_results_label.hide()

        self.period_real_results_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.period_real_results_label.setGeometry(QtCore.QRect(270, 410, 280, 40))
        self.period_real_results_label.setObjectName("period_real_results_label")
        self.period_real_results_label.hide()

        # --- Сохранение и ввод
        self.save_results = QtWidgets.QPushButton(parent=self.centralwidget)
        self.save_results.setGeometry(QtCore.QRect(270, 460, 280, 60))
        self.save_results.setObjectName("save_results")
        self.save_results.clicked.connect(self.save_fake_result)

        self.input_daily_results_lineEdit = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.input_daily_results_lineEdit.setGeometry(QtCore.QRect(180, 460, 80, 60))
        self.input_daily_results_lineEdit.setObjectName("input_daily_results_lineEdit")

        self.text_for_daily_resutls = QtWidgets.QLabel(parent=self.centralwidget)
        self.text_for_daily_resutls.setGeometry(QtCore.QRect(10, 460, 160, 60))
        self.text_for_daily_resutls.setObjectName("text_for_daily_resutls")

        self.duplicated_results_textEdit = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.duplicated_results_textEdit.setGeometry(QtCore.QRect(10, 540, 541, 101))
        self.duplicated_results_textEdit.setObjectName("duplicated_results_textEdit")


        MainWindow.setCentralWidget(self.centralwidget) # узнать почему не отображается 
        regex = QRegularExpression("^[1-9][0-9]{0,2}$")
        validator = QRegularExpressionValidator(regex)
        self.input_daily_results_lineEdit.setValidator(validator)
        self.input_daily_results_lineEdit.setStyleSheet("""
            QLineEdit {
            font-size: 20pt;
            qproperty-alignment: 'AlignCenter';
            }
        """)
        # ложные и реальные начальные кол-во файлов 
        # дата начала будет 17.11.2025
        self.real_starter_result = 8163
        self.fake_starter_result = 8510
        
        # Shortcut Ctrl+W для показа/скрытия real period
        self.shortcut_toggle_real = QShortcut(QtGui.QKeySequence("Ctrl+W"), MainWindow)
        self.shortcut_toggle_real.activated.connect(self.toggle_real_period_visibility)

        # Shortcut Ctrl+S для сохранения real результата
        self.shortcut_save_real = QShortcut(QtGui.QKeySequence("Ctrl+S"), MainWindow)
        self.shortcut_save_real.activated.connect(self.save_real_result)

        # Генерация по кнопке
        self.fake_daily_counter_btn.clicked.connect(self.fake_daily_generate)
        self.fake_daily_counter_btn.clicked.connect(self.fake_daily_count_from_json)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # Даты по умолчанию и флаги
        self.set_default_dates()
        self.update_daily_mode()
        self.real_period_visible = False
    

        # Антиспам кнопки
        self.fake_button_enabled = True
        self.fake_button_timer = QtCore.QTimer()
        self.fake_button_timer.setSingleShot(True)
        self.fake_button_timer.setInterval(15000)
        self.fake_button_timer.timeout.connect(self.enable_fake_button)
        # Поиск дубликатов
        self.duplicate_finder()
        # показ данных файлов из json за период
        self.load_and_display_json_data()
        
    def fake_daily_generate(self):
        if not self.fake_button_enabled:
            return

        self.fake_button_enabled = False
        self.fake_button_timer.start()

        value = random.randint(40, 80)
        self.fake_daily_results_label.setText(f"Результат за сегодня: {value}")
        self.input_daily_results_lineEdit.setText(str(value))

    def enable_fake_button(self):
        self.fake_button_enabled = True

    def toggle_mode(self):
        self.mode_daily_res_show = not self.mode_daily_res_show
        self.update_daily_mode()

    def update_daily_mode(self):
        if self.mode_daily_res_show:
            self.real_daily_counter_btn.show()
            self.real_daily_results_label.show()
            self.fake_daily_counter_btn.hide()
            self.fake_daily_results_label.hide()
        else:
            self.fake_daily_counter_btn.show()
            self.fake_daily_results_label.show()
            self.real_daily_counter_btn.hide()
            self.real_daily_results_label.hide()

    def toggle_real_period_visibility(self):
        self.real_period_visible = not self.real_period_visible
        self.real_results_textEdit.setVisible(self.real_period_visible)
        self.period_real_results_label.setVisible(self.real_period_visible)

    def set_default_dates(self):
        minimum_start = QtCore.QDate(2025, 11, 17)
        self.start_dateEdit.setMinimumDate(minimum_start)
        self.start_dateEdit.setDate(minimum_start)

        today = QtCore.QDate.currentDate()
        self.end_dateEdit.setDate(today)
        self.end_dateEdit.setMaximumDate(QtCore.QDate.currentDate())

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))  # узнать почему не отображается 
        self.start_date_label.setText(_translate("MainWindow", "Начальная Дата"))
        self.end_date_label.setText(_translate("MainWindow", "Конечная Дата"))
        self.fake_daily_counter_btn.setText(_translate("MainWindow", "Кол-во за сегодня"))
        self.fake_daily_results_label.setText(_translate("MainWindow", "Результат за сегодня"))
        self.period_fake_results_label.setText(_translate("MainWindow", "Фейковые результаты за период"))
        self.real_daily_counter_btn.setText(_translate("MainWindow", "Кол-во за сегодня (real)"))
        self.real_daily_results_label.setText(_translate("MainWindow", "Результат за сегодня (real)"))
        self.period_real_results_label.setText(_translate("MainWindow", "Реальные результаты за период"))
        self.save_results.setText(_translate("MainWindow", "Сохранить результаты"))
        self.text_for_daily_resutls.setText(_translate("MainWindow", "Результаты за сегодня ===>"))

    def real_daily_count(self):
        count = 0

        start_date = self.start_dateEdit.date().toPyDate()
        end_date = self.end_dateEdit.date().toPyDate()

        # Если выбрана одна и та же дата
        if start_date == end_date:
            target_date = start_date
        else:
            # иначе оставляем поведение "сегодня"
            target_date = datetime.date.today()

        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                if filename.lower().endswith("_001.pdf"):
                    file_path = os.path.join(root, filename)

                    # Получаем дату создания файла
                    file_date = datetime.date.fromtimestamp(os.path.getctime(file_path))

                    if file_date == target_date:
                        count += 1

        self.real_daily_results_label.setText(
            f"Результат за {target_date.strftime('%d.%m.%Y')}: {count}"
        )    
    def duplicate_finder(self):
        duplicates = []
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                if not filename.lower().endswith("_001.pdf"):
                    full_path = os.path.join(root, filename)
                    duplicates.append(full_path)

        if duplicates:
           self.duplicated_results_textEdit.setPlainText("\n".join(duplicates))
        else:
            self.duplicated_results_textEdit.setPlainText(" ")

    def load_and_display_json_data(self):
        try:
            with open("fake.json", "r", encoding="utf-8") as f:
                fake_data = json.load(f)
        except FileNotFoundError:
            fake_data = {}

        try:
            with open("real.json", "r", encoding="utf-8") as f:
                real_data = json.load(f)
        except FileNotFoundError:
            real_data = {}

        # Обновление textEdit'ов
        fake_text = self.calculate_cumulative_fake(fake_data)
        real_text = self.calculate_cumulative_real(real_data)

        self.fake_results_textEdit.setPlainText(fake_text)
        self.real_results_textEdit.setPlainText(real_text)
        self.update_fake_period_summary(fake_data)
        self.update_real_period_summary(real_data)

    def calculate_cumulative_fake(self, data_dict):
        cumulative = self.fake_starter_result
        result_lines = []

        start_date = self.start_dateEdit.date().toPyDate()
        end_date = self.end_dateEdit.date().toPyDate()

        for single_date in self.daterange(start_date, end_date):
            date_str = single_date.strftime("%d.%m.%Y")
            value = data_dict.get(date_str)
            if value is not None:
                cumulative += int(value)
                result_lines.append(f"{date_str}: {value}  \\ {cumulative}")

        return "\n".join(result_lines)

    def calculate_cumulative_real(self, data_dict):
        cumulative = self.real_starter_result
        result_lines = []

        start_date = self.start_dateEdit.date().toPyDate()
        end_date = self.end_dateEdit.date().toPyDate()

        for single_date in self.daterange(start_date, end_date):
            date_str = single_date.strftime("%d.%m.%Y")
            value = data_dict.get(date_str)
            if value is not None:
                cumulative += int(value)
                result_lines.append(f"{date_str}: {value}  \\ {cumulative}")

        return "\n".join(result_lines)

    def daterange(self, start_date, end_date):
        for n in range((end_date - start_date).days + 1):
            yield start_date + datetime.timedelta(n)

    def update_fake_period_summary(self, data_dict):
        start_date = self.start_dateEdit.date().toPyDate()
        end_date = self.end_dateEdit.date().toPyDate()

        total = 0
        for single_date in self.daterange(start_date, end_date):
            date_str = single_date.strftime("%d.%m.%Y")
            value = data_dict.get(date_str)
            if value is not None:
                total += int(value)

        self.period_fake_results_label.setText(
            f"с {start_date.strftime('%d.%m.%Y')} до {end_date.strftime('%d.%m.%Y')} сделано {total} файлов"
        )

    def update_real_period_summary(self, data_dict):
        start_date = self.start_dateEdit.date().toPyDate()
        end_date = self.end_dateEdit.date().toPyDate()

        total = 0
        for single_date in self.daterange(start_date, end_date):
            date_str = single_date.strftime("%d.%m.%Y")
            value = data_dict.get(date_str)
            if value is not None:
                total += int(value)

        self.period_real_results_label.setText(
            f"с {start_date.strftime('%d.%m.%Y')} до {end_date.strftime('%d.%m.%Y')} сделано {total} файлов"
        )

    def save_fake_result(self):
        today = datetime.date.today()
        today_str = today.strftime("%d.%m.%Y")
        value_str = self.input_daily_results_lineEdit.text().strip()

        if not value_str.isdigit():
            QtWidgets.QMessageBox.warning(None, "Ошибка", "Введите корректное числовое значение.")
            return

        value = int(value_str)

        # Загрузка текущего json
        try:
            with open("fake.json", "r", encoding="utf-8") as f:
                fake_data = json.load(f)
        except FileNotFoundError:
            fake_data = {}

        if today_str in fake_data:
            QtWidgets.QMessageBox.information(None, "Информация", f"Данные за {today_str} уже сохранены.")
            return

        # Подтверждение
        confirm = QtWidgets.QMessageBox.question(
            None,
            "Подтверждение",
            f"Сохранить результат {value} за {today_str}?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # Сохраняем
        fake_data[today_str] = value
        with open("fake.json", "w", encoding="utf-8") as f:
            json.dump(fake_data, f, ensure_ascii=False, indent=4)

        # Обновить отображение
        self.load_and_display_json_data()

    def fake_daily_count_from_json(self):
        start_date = self.start_dateEdit.date().toPyDate()
        end_date = self.end_dateEdit.date().toPyDate()

        # Проверяем, что даты совпадают
        if start_date != end_date:
            return  # Ничего не делаем, если выбран период

        target_date_str = start_date.strftime("%d.%m.%Y")

        # Загружаем данные из fake.json
        try:
            with open("fake.json", "r", encoding="utf-8") as f:
                fake_data = json.load(f)
        except FileNotFoundError:
            fake_data = {}

        value = fake_data.get(target_date_str)

        if value is not None:
            self.fake_daily_results_label.setText(
                f"Результат за {target_date_str}: {value}"
            )
        else:
            self.fake_daily_results_label.setText(
                f"Нет данных за {target_date_str}"
            )

    def save_real_result(self):
        today = datetime.date.today()
        today_str = today.strftime("%d.%m.%Y")

        # Берем текущий текст из real_daily_results_label
        label_text = self.real_daily_results_label.text().strip()

        # Проверяем, что там есть число
        if ":" not in label_text:
            QtWidgets.QMessageBox.warning(None, "Ошибка", "Нет результата для сохранения.")
            return

        try:
            value = int(label_text.split(":")[-1].strip())
        except ValueError:
            QtWidgets.QMessageBox.warning(None, "Ошибка", "Некорректный результат.")
            return

        # Загружаем текущие real.json
        try:
            with open("real.json", "r", encoding="utf-8") as f:
                real_data = json.load(f)
        except FileNotFoundError:
            real_data = {}

        if today_str in real_data:
            QtWidgets.QMessageBox.information(None, "Информация", f"Данные за {today_str} уже сохранены.")
            return

        # Подтверждение
        confirm = QtWidgets.QMessageBox.question(
            None,
            "Подтверждение",
            f"Сохранить результат {value} за {today_str}?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # Сохраняем
        real_data[today_str] = value
        with open("real.json", "w", encoding="utf-8") as f:
            json.dump(real_data, f, ensure_ascii=False, indent=4)
        # def pdf_deleter()
        # Обновить отображение
        self.load_and_display_json_data()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
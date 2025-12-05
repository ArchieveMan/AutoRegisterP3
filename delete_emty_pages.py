import os
import shutil
import numpy as np
from pdf2image import convert_from_path

# === НАСТРОЙКИ ===
base_folder = r"C:\Users\Arhivskaner\Desktop\Обработка скана\Резервный\1-18"
poppler_path = r"C:\Program Files\poppler-25.07.0\Library\bin"

small_file_size_kb = 100       # порог маленького файла
white_thresh_small = 0.90      # если меньше 100 КБ
white_thresh_large = 0.98      # если больше 100 КБ
dpi = 100                      # DPI при конвертации страниц
home_number = "18"
# === ФУНКЦИИ ===
def calculate_white_ratio(pdf_path):
    """Вычисляет процент белых пикселей на первой странице PDF"""
    try:
        pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
        img = np.array(pages[0].convert("RGB")) / 255.0
        white_mask = (img[:, :, 0] > 0.95) & (img[:, :, 1] > 0.95) & (img[:, :, 2] > 0.95)
        return np.mean(white_mask)
    except Exception as e:
        print(f"⚠️ Ошибка при анализе {pdf_path}: {e}")
        return 0.0

def process_flat(flat_number):
    """Обрабатывает одну квартиру"""
    folder_name = f"1мкрАкбулак{home_number}д{flat_number}кв_001"
    folder_path = os.path.join(base_folder, folder_name)

    if not os.path.exists(folder_path):
        print(f"⏭ Папка {folder_name} не найдена, пропускаем...\n")
        return

    print(f"\n=== Обработка квартиры №{flat_number} ===")

    deleted_folder = os.path.join(folder_path, "удаленные")
    os.makedirs(deleted_folder, exist_ok=True)

    for file_name in os.listdir(folder_path):
        if not file_name.lower().endswith(".pdf"):
            continue

        file_path = os.path.join(folder_path, file_name)
        file_size_kb = os.path.getsize(file_path) / 1024.0
        white_ratio = calculate_white_ratio(file_path)

        print(f"{file_name}: {file_size_kb:.1f} КБ, {white_ratio*100:.2f}% белого")

        # Условия "удаления" (перемещения)
        try:
            if (file_size_kb < small_file_size_kb and white_ratio > white_thresh_small) or \
               (file_size_kb >= small_file_size_kb and white_ratio > white_thresh_large):
                shutil.move(file_path, os.path.join(deleted_folder, file_name))
                print(f"👉 Перемещено в {deleted_folder}\n")
            else:
                print("✅ Оставлено\n")
        except Exception as e:
            print(f"⚠️ Ошибка при обработке {file_name}: {e}\n")

    print(f"✅ Квартира №{flat_number} завершена.\n")


# === ГЛАВНЫЙ ЦИКЛ ===
for flat_number in range(1, 121):  # от 1 до 120 включительно
    try:
        process_flat(flat_number)
    except Exception as e:
        print(f"❌ Ошибка при обработке квартиры {flat_number}: {e}")
        continue

print("🎉 Все квартиры обработаны! Проверяй папки 'удаленные'.")

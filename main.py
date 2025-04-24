# 1.4.8 
# добавлена статистика 
# изменена система ввода адреса


import re
import shutil
import PyPDF2
from pathlib import Path
from collections import defaultdict, Counter
from send2trash import send2trash


# === КОНФИГУРАЦИЯ ===
MODE = "test"  #"prod"

if MODE == "":
    STATS_FILE = Path(r"C:\Users\Arhivskaner\Desktop\Akbulak_stats.txt")
    BASE_ROOT = Path(r"C:\Users\Arhivskaner\Desktop\1Мкр Сжатый\1-1")
else:
    STATS_FILE = Path(r"C:\Users\Arhivskaner\Desktop\TEST_statistic.txt")
    BASE_ROOT = Path(r"C:\Users\Arhivskaner\Desktop\1Мкр Сжатый\для эксперементов\test")

flat_number = int(input("Введите номер квартиры: "))
flat_id = f"1мкрАкбулак1д{flat_number}кв"
BASE_DIR = BASE_ROOT / f"{flat_id}_001.pdf"

removed_unneeded_count = 0 
# Папка для результата
OUTPUT_DIR = BASE_DIR / "обработанный"
OUTPUT_DIR.mkdir(exist_ok=True)

def normalize_filename(name):
    return re.sub(r' \(\d+\)', '', name)

# Проверка, была ли уже статистика
record_stats = True
if STATS_FILE.exists():
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        if flat_id in f.read():
            print(f"⚠️ Статистика уже существует для: {flat_id}. Новая запись не будет добавлена.")
            record_stats = False

# Группируем PDF-файлы
grouped_files = defaultdict(list)

for file in BASE_DIR.glob("*.pdf"):
    base_name = normalize_filename(file.stem)

    if base_name.strip() == "-":
        print(f"🚮 Удалён ненужный файл (для статистики): {file.name}")
        send2trash(str(file))
        removed_unneeded_count += 1
        continue

    grouped_files[base_name].append(file)

# Объединяем или переносим файлы
for base_name, files in grouped_files.items():
    if len(files) == 1:
        single_file = files[0]
        destination = OUTPUT_DIR / single_file.name
        shutil.copy2(single_file, destination)
        send2trash(str(single_file)) 
        print(f"Перемещён без объединения: {single_file.name}")
    else:
        merger = PyPDF2.PdfMerger()
        for pdf_path in sorted(files):
            merger.append(str(pdf_path))
        output_file = OUTPUT_DIR / f"{base_name}.pdf"
        merger.write(str(output_file))
        merger.close()
        for pdf_path in files:
            send2trash(str(pdf_path))
        print(f"Объединено: {base_name} → {output_file.name}")

print("✅ Готово! Все PDF-файлы обработаны.")

# === Запись статистики ===
if record_stats:
    local_counter = Counter()
    for base_name, files in grouped_files.items():
        if base_name.strip() == "-":
            continue
        local_counter[base_name] += len(files)

    total_docs = sum(local_counter.values())

    with open(STATS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{flat_id} всего документов: {total_docs}\n")
        for name, count in local_counter.items():
            percent = round(count / total_docs * 100)
            f.write(f"  - {name}: {count} ({percent}%)\n")
        
        if removed_unneeded_count > 0:
            f.write(f"Удалённых ненужных файлов: {removed_unneeded_count}\n")

        f.write("===\n")

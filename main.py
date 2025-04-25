# 1.5.0 
# Добавлен защита от опечаток 
# Добавлен список уникальных названий в json файл 

# Есть лишний код или часть нужно исправить
# нужно добавить цвета или выдиляемость к обрабатывающим текстам и вопросам при показе в терминале

import json
import os
import shutil
import PyPDF2
from pathlib import Path
from collections import defaultdict, Counter
from send2trash import send2trash
import re

# === КОНФИГУРАЦИЯ ===
MODE = "test"  # "work"

if MODE == "work":
    STATS_FILE = Path(r"C:\Users\Arhivskaner\Desktop\Akbulak_stats.txt")
    BASE_ROOT = Path(r"C:\Users\Arhivskaner\Desktop\1Мкр Сжатый\1-1")
else:
    STATS_FILE = Path(r"C:\Users\Arhivskaner\Desktop\TEST_statistic.txt")
    BASE_ROOT = Path(r"C:\Users\Arhivskaner\Desktop\1Мкр Сжатый\для эксперементов\test")

flat_number = int(input("Введите номер квартиры: "))
flat_id = f"1мкрАкбулак1д{flat_number}кв"
BASE_DIR = BASE_ROOT / f"{flat_id}_001.pdf"

removed_unneeded_count = 0
OUTPUT_DIR = BASE_DIR / "обработанный"
OUTPUT_DIR.mkdir(exist_ok=True)

NAMES_MAP_FILE = "names_map.json"

if os.path.exists(NAMES_MAP_FILE):
    with open(NAMES_MAP_FILE, "r", encoding="utf-8") as f:
        name_map = json.load(f)
else:
    name_map = {}

def add_new_name(new_name):
    new_id = max(name_map.values(), key=lambda x: x['id'])['id'] + 1 if name_map else 1
    name_map[new_name] = {
        "id": new_id,
        "label": new_name,
        "aliases": []
    }
    with open(NAMES_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(name_map, f, ensure_ascii=False, indent=4)
    print(f"🔑 Новое название '{new_name}' добавлено в список!")

record_stats = True
if STATS_FILE.exists():
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        if flat_id in f.read():
            print(f"⚠️ Статистика уже существует для: {flat_id}. Новая запись не будет добавлена.")
            record_stats = False

def normalize_filename(name):
    return re.sub(r' \(\d+\)', '', name)

grouped_files = defaultdict(list)
skipped_names = []

for file in BASE_DIR.glob("*.pdf"):
    base_name = normalize_filename(file.stem)
    if base_name.strip() == "-":
        print(f"🚮 Удалён ненужный файл (для статистики): {file.name}")
        send2trash(str(file))
        removed_unneeded_count += 1
        continue
    grouped_files[base_name].append(file)

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

    if base_name not in name_map:
        print(f"Найдено новое название: {base_name}")
        response = input("Добавить его в список уникальных имен (если тут опечатка или альтернативное имя выберите 'n')? (y/n): ").strip().lower()

        if response == 'y':
            add_new_name(base_name)
        else:
            print(f"Название '{base_name}' определено как опечатка или альтернативное имя.")
            while True:
                choice = input("Хотите указать ID оригинального названия сейчас (y), пропустить (s), или добавить как уникальное (a)? ").strip().lower()

                if choice == 'y':
                    try:
                        original_id = int(input("Укажите id оригинального названия: ").strip())
                        if original_id in [data["id"] for data in name_map.values()]:
                            for name, data in name_map.items():
                                if data["id"] == original_id:
                                    data.setdefault("aliases", []).append(base_name)
                                    print(f"✅ '{base_name}' добавлено как альтернативное к '{data['label']}' (ID {original_id})")
                                    break
                            break
                        else:
                            print("❌ ID не найден. Повторите ввод.")
                    except ValueError:
                        print("❌ Введите целое число.")

                elif choice == 'a':
                    add_new_name(base_name)
                    break
                elif choice == 's':
                    print(f"⏭️ Название '{base_name}' пропущено для повторной обработки.")
                    skipped_names.append(base_name)
                    break
                else:
                    print("Введите 'y', 'a' или 's'.")

# === Повторная обработка пропущенных названий ===
if skipped_names:
    print("\n📌 Вы ранее пропустили следующие названия:")
    for skipped in skipped_names:
        print(f" - {skipped}")
    print("Хотите сейчас их обработать?")

    for skipped in skipped_names:
        print(f"\n🔁 Название: {skipped}")
        while True:
            choice = input("Указать ID оригинала (y), добавить как уникальное (a), пропустить снова (s): ").strip().lower()
            if choice == 'y':
                try:
                    original_id = int(input("Укажите id оригинального названия: ").strip())
                    if original_id in [data["id"] for data in name_map.values()]:
                        for name, data in name_map.items():
                            if data["id"] == original_id:
                                data.setdefault("aliases", []).append(skipped)
                                print(f"✅ '{skipped}' добавлено как альтернативное к '{data['label']}' (ID {original_id})")
                                break
                        break
                    else:
                        print("❌ ID не найден.")
                except ValueError:
                    print("❌ Введите целое число.")
            elif choice == 'a':
                add_new_name(skipped)
                break
            elif choice == 's':
                print(f"⏭️ Название '{skipped}' снова пропущено.")
                break
            else:
                print("Введите 'y', 'a' или 's'.")

with open(NAMES_MAP_FILE, "w", encoding="utf-8") as f:
    json.dump(name_map, f, ensure_ascii=False, indent=4)

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

print("✅ Готово! Все PDF-файлы обработаны.")

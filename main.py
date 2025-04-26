# v1.5.2 
# Добавлена оформление текста в терминале
# v1.5.1 
# Улучшена система "Защита от опечаток"

import json
import os
import shutil
import PyPDF2
from pathlib import Path
from collections import defaultdict, Counter
from send2trash import send2trash
import re
from colorama import Fore, Style, init

# Инициализация colorama для кроссплатформенной работы
init(autoreset=True)
import logging
from colorama import init, Fore

# Инициализируем colorama
init(autoreset=True)
open("log.txt", "w").close()

# ====================== ЛОГГИРОВАНИЕ ======================
LOG_FILE = "log.txt"

# Настройка логгера
logger = logging.getLogger("AutoRegisterLogger")
logger.setLevel(logging.DEBUG)

# Формат логов
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Лог в файл
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Лог в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Добавляем обработчики
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# =================== ЛОГГИРОВАНИЕ КОНЕЦ ===================

# ========================== КОНФИГУРАЦИЯ ===========================
MODE = "test"  # "work"

if MODE == "work":
    STATS_FILE = Path(r"C:\Users\Arhivskaner\Desktop\Akbulak_stats.txt")
    BASE_ROOT = Path(r"C:\Users\Arhivskaner\Desktop\1Мкр Сжатый\1-1")
else:
    STATS_FILE = Path(r"C:\Users\ladsp\Desktop\AutoRegisterDocs\TEST_stats.txt")
    BASE_ROOT = Path(r"C:\Users\ladsp\Desktop\AutoRegisterDocs\test")

flat_number = int(input("Введите номер квартиры: "))
flat_id = f"1мкрАкбулак1д{flat_number}кв"
BASE_DIR = BASE_ROOT / f"{flat_id}_001.pdf"

removed_unneeded_count = 0
OUTPUT_DIR = BASE_DIR / "обработанный"
OUTPUT_DIR.mkdir(exist_ok=True)

NAMES_MAP_FILE = "names_map.json"
# ======================== Конфигурация окончена =========================

# ======================= РАБОТА С КАРТОЙ ИМЁН ========================
logger.info(Fore.CYAN + "📚 Работа с картой имен...")
def build_alias_map(name_map):
    alias_to_main = {}
    for main_name, data in name_map.items():
        aliases = data.get("aliases", [])
        for alias in aliases:
            if alias in alias_to_main:
                logger.info(Fore.YELLOW + f"⚠️ Предупреждение: альтернативное имя '{alias}' уже связано с '{alias_to_main[alias]}'.")
            alias_to_main[alias] = main_name
    return alias_to_main

def add_new_name(new_name):
    new_id = max(name_map.values(), key=lambda x: x['id'])['id'] + 1 if name_map else 1
    name_map[new_name] = {
        "id": new_id,
        "label": new_name,
        "aliases": []
    }
    with open(NAMES_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(name_map, f, ensure_ascii=False, indent=4)
    logger.info(Fore.GREEN + f"🔑 Новое название '{new_name}' добавлено в список!")

if os.path.exists(NAMES_MAP_FILE):
    with open(NAMES_MAP_FILE, "r", encoding="utf-8") as f:
        name_map = json.load(f)
else:
    name_map = {}

alias_to_main = build_alias_map(name_map)
# ====================== Работа с картой имён окончена ======================


# ========================= РАБОТА С PDF-ФАЙЛАМИ =========================
logger.info(Fore.CYAN + "📄 Работа с PDF-файлами...")
def normalize_filename(name):
    return re.sub(r' \(\d+\)', '', name)

grouped_files = defaultdict(list)
skipped_names = []

for file in BASE_DIR.glob("*.pdf"):
    base_name = normalize_filename(file.stem)
    if base_name in alias_to_main:
        real_name = alias_to_main[base_name]
        logger.info(Fore.YELLOW + f"🔄 Найдено альтернативное имя '{base_name}', заменено на '{real_name}'")
        base_name = real_name
    if base_name.strip() == "-":
        logger.info(Fore.RED + f"🚮 Удалён ненужный файл (для статистики): {file.name}")
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
        logger.info(Fore.GREEN + f"🟩 Перемещён без объединения: {single_file.name}")
    else:
        merger = PyPDF2.PdfMerger()
        for pdf_path in sorted(files):
            merger.append(str(pdf_path))
        output_file = OUTPUT_DIR / f"{base_name}.pdf"
        merger.write(str(output_file))
        merger.close()
        for pdf_path in files:
            send2trash(str(pdf_path))
        logger.info(Fore.GREEN + f"🟨 Объединено: {base_name} → {output_file.name}")
# ======================= Работа с PDF-файлами окончена =======================


# ======================== РАБОТА С НОВЫМИ ИМЕНАМИ ========================
logger.info(Fore.CYAN + "🆕 Работа с новыми именами...")
if base_name not in name_map:
    logger.info(Fore.YELLOW + f"🔴➡️ Найдено новое название: {base_name}")
    response = input("Добавить его в список уникальных имен (если тут опечатка или альтернативное имя выберите 'n')? (y/n): ").strip().lower()

    if response == 'y':
        add_new_name(base_name)
    else:
        logger.info(Fore.RED + f"❗ Название '{base_name}' определено как опечатка или альтернативное имя.")
        while True:
            choice = input("Хотите указать ID оригинального названия сейчас (y), пропустить (s), или добавить как уникальное (a)? ").strip().lower()

            if choice == 'y':
                try:
                    original_id = int(input("Укажите id оригинального названия: ").strip())
                    if original_id in [data["id"] for data in name_map.values()]:
                        for name, data in name_map.items():
                            if data["id"] == original_id:
                                data.setdefault("aliases", []).append(base_name)
                                logger.info(Fore.GREEN + f"✅ '{base_name}' добавлено как альтернативное к '{data['label']}' (ID {original_id})")
                                break
                        break
                    else:
                        logger.info(Fore.RED + "❌ ID не найден. Повторите ввод.")
                except ValueError:
                    logger.info(Fore.RED + "❌ Введите целое число.")

            elif choice == 'a':
                add_new_name(base_name)
                break
            elif choice == 's':
                logger.info(Fore.YELLOW + f"⏭️ Название '{base_name}' пропущено для повторной обработки.")
                skipped_names.append(base_name)
                break
            else:
                print("Введите 'y', 'a' или 's'.")
# ===================== Работа с новыми именами окончена ======================


# ======================== ПОВТОРНАЯ ОБРАБОТКА ИМЁН ========================
logger.info(Fore.CYAN + "♻️ Повторная обработка имён...")
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
                                logger.info(Fore.GREEN + f"✅ '{skipped}' добавлено как альтернативное к '{data['label']}' (ID {original_id})")
                                break
                        break
                    else:
                        logger.info(Fore.RED + "❌ ID не найден.")
                except ValueError:
                    logger.info(Fore.RED + "❌ Введите целое число.")
            elif choice == 'a':
                add_new_name(skipped)
                break
            elif choice == 's':
                logger.info(Fore.YELLOW + f"⏭️ Название '{skipped}' снова пропущено.")
                break
            else:
                print("Введите 'y', 'a' или 's'.")
# ====================== Повторная обработка имён окончена ======================
logger.info(Fore.GREEN + "🎯 Обработка завершена успешно! Все PDF-файлы обработаны.")
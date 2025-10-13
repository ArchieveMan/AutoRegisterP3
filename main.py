# v1.5.9 

# добавлена функция разеделение на 20 страниц за 1 файл 

import json
import os
import shutil
import PyPDF2
from pathlib import Path
from collections import defaultdict, Counter
from send2trash import send2trash
import re
from colorama import Fore, Style, init # type: ignore
import logging

# Инициализация colorama для кроссплатформенной работы
init(autoreset=True)
open("log.txt", "w").close()

# ====================== ЛОГГИРОВАНИЕ ======================
LOG_FILE = "log.txt"
logger = logging.getLogger("AutoRegisterLogger")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
# =================== ЛОГГИРОВАНИЕ КОНЕЦ ===================

# ========================== КОНФИГУРАЦИЯ ===========================
MODE = "work"  
if MODE == "work":
    BASE_ROOT = Path(r"C:\Users\Arhivskaner\Desktop\1Мкр Сжатый\Test")
else:
    BASE_ROOT = Path(r"C:\Users\ladsp\Desktop\AutoRegisterDocs\test")

flat_number = int(input("Введите номер квартиры: "))
flat_id = f"1мкрАкбулак7д{flat_number}кв_001"  
BASE_DIR = BASE_ROOT / flat_id

if not BASE_DIR.exists():
    logger.error(Fore.RED + f"❌ Указанный адрес не существует: {BASE_DIR}")
    exit(1)

OUTPUT_DIR = BASE_DIR / "обработанный"
NAMES_MAP_FILE = "names_map.json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
# ======================== Конфигурация окончена =========================

# ======================= РАБОТА С КАРТОЙ ИМЁН ========================
logger.info(Fore.CYAN + "📚📚📚 Работа с картой имен...")
def build_alias_map(name_map):
    alias_to_main = {}
    for main_name, data in name_map.items():
        for alias in data.get("aliases", []):
            alias_to_main[alias] = main_name
    return alias_to_main

def add_new_name(new_name):
    new_id = max((x['id'] for x in name_map.values()), default=0) + 1
    name_map[new_name] = {"id": new_id, "label": new_name, "aliases": []}
    with open(NAMES_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(name_map, f, ensure_ascii=False, indent=4)
    logger.info(Fore.GREEN + f"🔑🔑🔑 Новое название '{new_name}' добавлено в список!")

def save_name_map():
    with open(NAMES_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(name_map, f, ensure_ascii=False, indent=4)

if os.path.exists(NAMES_MAP_FILE):
    with open(NAMES_MAP_FILE, "r", encoding="utf-8") as f:
        name_map = json.load(f)
else:
    name_map = {}

alias_to_main = build_alias_map(name_map)
# ====================== Работа с картой имён окончена ======================

# ========================= РАБОТА С PDF-ФАЙЛАМИ =========================
MAX_PAGES = 20 

logger.info(Fore.CYAN + "📄📄📄 Работа с PDF-файлами...")
def normalize_filename(name):
    return re.sub(r' \(\d+\)', '', name)

grouped_files = defaultdict(list)
skipped_names = []

for file in BASE_DIR.glob("*.pdf"):
    if file.parent == OUTPUT_DIR:
        continue

    base_name = normalize_filename(file.stem)
    if base_name.strip() == "-":
        logger.info(Fore.RED + f"🚮🚮🚮 Удалён ненужный файл (для статистики): {file.name}")
        send2trash(str(file))
        continue

    if base_name in alias_to_main:
        real_name = alias_to_main[base_name]
        logger.info(Fore.YELLOW + f"🔄🔄🔄 Найдено альтернативное имя '{base_name}', заменено на '{real_name}'")
        base_name = real_name

    grouped_files[base_name].append(file)

for base_name, files in grouped_files.items():
    if base_name not in name_map:
        logger.info(Fore.YELLOW + f"⛔️⛔️⛔️➞️ Найдено новое название: {base_name}")
        response = input("Добавить его в список уникальных имен (y/n)? ").strip().lower()
        if response in ['y','н']:
            add_new_name(base_name)
        else:
            logger.info(Fore.RED + f"❗❗❗ Название '{base_name}' определено как ошибочное или альтернативное.")
            while True:
                choice = input("Указать ID оригинала (y), пропустить (s), добавить как уникальное (a)? ").strip().lower()
                if choice in  ['y','н']:
                    try:
                        original_id = int(input("Укажите id: ").strip())
                        found = False
                        for name, data in name_map.items():
                            if data["id"] == original_id:
                                data.setdefault("aliases", []).append(base_name)
                                save_name_map()
                                alias_to_main = build_alias_map(name_map)
                                base_name = alias_to_main.get(base_name, base_name)
                                logger.info(Fore.GREEN + f"✅✅✅ '{base_name}' добавлено как альтернативное к '{data['label']}'")
                                found = True
                                break
                        if found:
                            break
                        else:
                            logger.info(Fore.RED + "❌❌❌ ID не найден.")
                    except ValueError:
                        logger.info(Fore.RED + "❌❌❌ Введите целое число.")
                elif choice in ['a','ф']:
                    add_new_name(base_name)
                    break
                elif choice in ['s','ы']:
                    logger.info(Fore.YELLOW + f"⏭️⏭️⏭️ '{base_name}' пропущен.")
                    skipped_names.append(base_name)
                    break
                else:
                    print("Введите 'y', 'a' или 's'.")

    if base_name in alias_to_main:
        base_name = alias_to_main[base_name]

    if len(files) == 1:
        single = files[0]
        dest = OUTPUT_DIR / f"{base_name}.pdf"
        shutil.copy2(single, dest)
        send2trash(str(single))
        logger.info(Fore.GREEN + f"🗹 Перемещён: {single.name} → {dest.name}")
        continue

    part = 1
    current_pages = 0
    merger = PyPDF2.PdfMerger()
    used_files = []  # <--- добавляем список для последующего удаления

    for pdf_path in sorted(files):
        reader = PyPDF2.PdfReader(pdf_path)
        pages = len(reader.pages)

        # Проверка превышения лимита страниц
        if current_pages + pages > MAX_PAGES:
            output = OUTPUT_DIR / f"{base_name}_part{part}.pdf"
            merger.write(str(output))
            merger.close()
            logger.info(Fore.YELLOW + f"📄 Создан файл: {output.name} ({current_pages} стр.)")

            # ✅ Удаляем только после закрытия merger — файл больше не занят
            for f in used_files:
                try:
                    send2trash(str(f))
                except PermissionError:
                    logger.warning(Fore.RED + f"⚠️ Не удалось удалить (занят): {f.name}")
            used_files.clear()

            # Начинаем новый кусок
            part += 1
            current_pages = 0
            merger = PyPDF2.PdfMerger()

        merger.append(str(pdf_path))
        current_pages += pages
        used_files.append(pdf_path)

    # Финальный кусок
    if current_pages > 0:
        suffix = f"_part{part}" if part > 1 else ""
        output = OUTPUT_DIR / f"{base_name}{suffix}.pdf"
        merger.write(str(output))
        merger.close()

        # ✅ Удаляем оставшиеся файлы
        for f in used_files:
            try:
                send2trash(str(f))
            except PermissionError:
                logger.warning(Fore.RED + f"⚠️ Не удалось удалить (занят): {f.name}")

        logger.info(Fore.GREEN + f"✅ Финальный файл: {output.name} ({current_pages} стр.)")
# ======================= Работа с PDF-файлами окончена =======================

# ======================== ПОВТОРНАЯ ОБРАБОТКА ИМЁН ========================
logger.info(Fore.CYAN + "♻️♻️♻️ Повторная обработка имён...")
if skipped_names:
    print("\n📌📌📌 Вы ранее пропустили следующие названия:")
    for skipped in skipped_names:
        print(f" - {skipped}")
    for skipped in skipped_names:
        print(f"\n🔁🔁🔁 Название: {skipped}")
        while True:
            choice = input("Указать ID оригинала (y), добавить как уникальное (a), пропустить снова (s): ").strip().lower()
            if choice in ['y','н']:
                try:
                    original_id = int(input("Укажите id оригинального названия: ").strip())
                    found = False
                    for name, data in name_map.items():
                        if data["id"] == original_id:
                            data.setdefault("aliases", []).append(skipped)
                            save_name_map()
                            logger.info(Fore.GREEN + f"✅✅✅ '{skipped}' добавлено как альтернативное к '{data['label']}' (ID {original_id})")
                            found = True
                            break
                    if found:
                        break
                    else:
                        logger.info(Fore.RED + "❌❌❌ ID не найден.")
                except ValueError:
                    logger.info(Fore.RED + "❌❌❌ Введите целое число.")
            elif choice in ['a','ф']:
                add_new_name(skipped)
                break
            elif choice in ['s','ы']:
                logger.info(Fore.YELLOW + f"⏭️⏭️⏭️ Название '{skipped}' снова пропущено.")
                break
            else:
                print("Введите 'y', 'a' или 's'.")
# ======================== ПОВТОРНАЯ ОБРАБОТКА ИМЁН КОНЕЦ ====================

# ======================== ПРОВЕРКА РАЗМЕРА PDF ========================
logger.info(Fore.CYAN + "📏📏📏 Проверка размеров PDF файлов 📏📏📏\n")

MAX_SIZE_KB = 13000

for pdf_file in OUTPUT_DIR.glob("*.pdf"):
    size_kb = os.path.getsize(pdf_file) // 1024
    if size_kb > MAX_SIZE_KB:
        logger.error(Fore.RED + f"⚠️ ⚠️ ⚠️  Файл '{pdf_file.name}' превышает {MAX_SIZE_KB} Кб! ({size_kb} Кб) ⚠️ ⚠️ ⚠️ \n")
# ======================== ПРОВЕРКА РАЗМЕРА PDF КОНЕЦ ========================

# ====================== Повторная обработка имён окончена ======================
logger.info(Fore.GREEN + "🌟 Обработка завершена успешно! Все PDF-файлы обработаны.")
logger.info(Fore.CYAN + f"==============================={flat_number}===============================")

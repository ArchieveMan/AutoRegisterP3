import json
import os
import shutil
import PyPDF2
from pathlib import Path
from collections import defaultdict
from send2trash import send2trash
import re
from colorama import Fore, init # type: ignore
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

# путь где проводится объединение страниц
BASE_ROOT = Path(r"C:\Users\Arhivskaner\Desktop\Обработка скана\Test")

# лимит страниц на 1 файл
MAX_PAGES = 20

#  порог предупреждения максимального размера для одного файла
MAX_SIZE_KB = 14000 

# файл с картой имён
NAMES_MAP_FILE = "names_map.json"

# Режим работы (massive - для всех квартир одного дома, single - для одной квартиры который укажите в терминале)
MODE = 'massive'
# MODE = 'single' 

# НАСТРОЙКИ АДРЕСА 
area_name = "1мкрАкбулак"            # <====  Название района
home_number = "18"                   # <====  Номер дома
# ========================== ВЫБОР РЕЖИМА ===========================
def process_flat(flat_number: int):
    """
    Выполняет обработку одной квартиры (вынесено в отдельную функцию)
    """
    flat_id = f"{area_name}{home_number}д{flat_number}кв_001"
    base_dir = BASE_ROOT / flat_id

    if not base_dir.exists():
        logger.warning(Fore.RED + f"⏭️ Квартира {flat_number} пропущена — путь не найден: {base_dir}")
        return None  # Пропуск, если папка отсутствует

    logger.info(Fore.CYAN + f"🏠 Обработка квартиры №{flat_number}")
    output_dir = base_dir / "обработанный"
    output_dir.mkdir(parents=True, exist_ok=True)
    return base_dir, output_dir, flat_number

# ------------------ выбор режима ------------------
if MODE == 'single':
    finish_text = "Еденичная"
    flat_number = int(input("Введите номер квартиры: "))
    flat_id = f"{area_name}{home_number}д{flat_number}кв_001"
    BASE_DIR = BASE_ROOT / flat_id
    OUTPUT_DIR = BASE_DIR / "обработанный"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    flats_to_process = [flat_number]

elif MODE == 'massive':
    finish_text = "Массовая"
    flats_to_process = [i for i in range(1, 121) if (BASE_ROOT / f"{area_name}{home_number}д{i}кв_001").exists()]
    logger.info(Fore.CYAN + f"🔍 Найдено {len(flats_to_process)} квартир(ы) для обработки: {flats_to_process}")
    if not flats_to_process:
        logger.error(Fore.RED + "❌ Не найдено ни одной квартиры для обработки!")
        exit(1)

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
skipped_list = []
try:
    # ===================== ОБРАБОТКА ВСЕХ КВАРТИР =====================
    for flat_number in flats_to_process:
        skipped_global = defaultdict(list)
        result = process_flat(flat_number)
        if not result:
            continue
        BASE_DIR, OUTPUT_DIR, flat_number = result

        # ========================= РАБОТА С PDF-ФАЙЛАМИ =========================
        logger.info(Fore.CYAN + f"📄📄📄 Работа с PDF-файлами... ({flat_number})")

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
                logger.info(Fore.YELLOW + f"⛔️ Найдено новое название: {base_name}")
                response = input("Добавить (y/н), указать ID (число) или пропустить (s/ы): ").strip().lower()

                # --- добавить как уникальное ---
                if response in ['y', 'н']:
                    add_new_name(base_name)

                # --- указать ID ---
                elif response.isdigit():
                    original_id = int(response)
                    found = False
                    for name, data in name_map.items():
                        if data["id"] == original_id:
                            data.setdefault("aliases", []).append(base_name)
                            save_name_map()
                            alias_to_main = build_alias_map(name_map)
                            base_name = alias_to_main.get(base_name, base_name)
                            logger.info(Fore.GREEN + f"✅ '{base_name}' добавлено как альтернативное к '{data['label']}' (ID {original_id})")
                            found = True
                            break
                    if not found:
                        logger.error(Fore.RED + f"❌ ID {original_id} не найден в карте имён.")

                # --- пропустить ---
                elif response in ['s', 'ы']:
                    flat_id = f"{area_name}{home_number}д{flat_number}кв_001"
                    logger.info(Fore.RED + f"⏭ '{base_name}' пропущен (из {flat_id})")
                    skipped_list.append(f"'{base_name}' пропущен (из {flat_id})")
                    continue
                # --- некорректный ввод ---
                else:
                    logger.warning(Fore.RED + f"⚠️ Неверный ввод. Используйте 'y', 's' или число (ID). Пропуск по умолчанию.")
                    flat_id = f"{area_name}{home_number}д{flat_number}кв_001"
                    skipped_global[flat_id].append(base_name)

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
            used_files = []

            for pdf_path in sorted(files):
                reader = PyPDF2.PdfReader(pdf_path)
                pages = len(reader.pages)

                if current_pages + pages > MAX_PAGES:
                    output = OUTPUT_DIR / f"{base_name}_part{part}.pdf"
                    merger.write(str(output))
                    merger.close()
                    logger.info(Fore.YELLOW + f"📄 Создан файл: {output.name} ({current_pages} стр.)")

                    for f in used_files:
                        try:
                            send2trash(str(f))
                        except PermissionError:
                            logger.warning(Fore.RED + f"⚠️ Не удалось удалить (занят): {f.name}")
                    used_files.clear()

                    part += 1
                    current_pages = 0
                    merger = PyPDF2.PdfMerger()

                merger.append(str(pdf_path))
                current_pages += pages
                used_files.append(pdf_path)

            if current_pages > 0:
                suffix = f"_part{part}" if part > 1 else ""
                output = OUTPUT_DIR / f"{base_name}{suffix}.pdf"
                merger.write(str(output))
                merger.close()

                for f in used_files:
                    try:
                        send2trash(str(f))
                    except PermissionError:
                        logger.warning(Fore.RED + f"⚠️ Не удалось удалить (занят): {f.name}")

                logger.info(Fore.GREEN + f"✅ Финальный файл: {output.name} ({current_pages} стр.)")

        # ======================== ПРОВЕРКА РАЗМЕРА PDF ========================
        logger.info(Fore.CYAN + "📏 Проверка размеров PDF файлов 📏\n")

        for pdf_file in OUTPUT_DIR.glob("*.pdf"):
            size_kb = os.path.getsize(pdf_file) // 1024
            if size_kb > MAX_SIZE_KB:
                logger.error(Fore.RED + f"⚠️ Файл '{pdf_file.name}' превышает {MAX_SIZE_KB} Кб! ({size_kb} Кб)\n")

        logger.info(Fore.GREEN + f"🌟 Квартира №{flat_number} обработана успешно.")
        logger.info(Fore.CYAN + f"==============================={flat_number}===============================")

    # ===================== ВСЕ КВАРТИРЫ ОБРАБОТАНЫ =====================
    logger.info(Fore.GREEN + f"🌟 {finish_text} обработка завершена успешно!")

except KeyboardInterrupt:
    logger.error(Fore.RED + "\n🛑 Операция прервана пользователем (Ctrl + C).")
    logger.info(Fore.CYAN + "💾 Все промежуточные данные сохранены.")
    exit(0)

# ==================== ОТЧЁТ О ПРОПУЩЕННЫХ ИМЁНАХ ====================
if skipped_list:
    logger.info(Fore.RED + "\n🚨🚨🚨 Итог: пропущенные имена 🚨🚨🚨")
    for line in skipped_list:
        logger.info(Fore.RED + f"📂 {line}")
else:
    logger.info(Fore.GREEN + "✅ Все имена обработаны без пропусков!")
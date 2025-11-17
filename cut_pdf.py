import shutil
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
# from main import area_name, home_number

# SOURCE_DIR = Path(r"C:\Users\Arhivskaner\Desktop\scan") / area_name / f"{area_name} {home_number} Дом"

# ==== ПУТИ ====
SOURCE_DIR = Path(r"C:\Users\Arhivskaner\Desktop\scan\1мкрАкбулак\1мкрАкбулак 15 Дом")
TEMP_COPY_DIR = Path(r"C:\Users\Arhivskaner\Desktop\scan\_temp_copy")
OUTPUT_DIR = Path(r"C:\Users\Arhivskaner\Desktop\Обработка скана\Резервный")

# ==== ПОДГОТОВКА ====
if TEMP_COPY_DIR.exists():
    shutil.rmtree(TEMP_COPY_DIR)
shutil.copytree(SOURCE_DIR, TEMP_COPY_DIR)  # копируем всю папку целиком

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("📂 Копия исходных данных создана.")
print("📄 Начинаем разделение PDF-файлов...\n")

# ==== ОБРАБОТКА PDF ====
for pdf_file in TEMP_COPY_DIR.rglob("*.pdf"):
    try:
        file_stem = pdf_file.stem
        parent_dir = OUTPUT_DIR / file_stem
        parent_dir.mkdir(parents=True, exist_ok=True)

        reader = PdfReader(str(pdf_file))
        total_pages = len(reader.pages)

        for i, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)
            output_path = parent_dir / f"{file_stem}_page_{i}.pdf"
            with open(output_path, "wb") as f_out:
                writer.write(f_out)

        print(f"✅ {pdf_file.name} → разделён на {total_pages} страниц")

    except Exception as e:
        print(f"❌ Ошибка при обработке {pdf_file.name}: {e}")

print("\n🎉 Готово! Все разделённые файлы находятся в:")
print(OUTPUT_DIR)



import re
import json
import csv
from pathlib import Path

import cv2
import pytesseract


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "sample_documents" / "sample_invoice.png"

OUTPUT_JSON = BASE_DIR / "extracted_invoice.json"
OUTPUT_CSV = BASE_DIR / "extracted_invoice.csv"

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def clean_amount(value):
    """Normalize an OCR-extracted monetary amount."""
    if not value:
        return None

    value = value.replace(",", "").replace(" ", "").strip()

    match = re.search(r"\d+(?:\.\d{1,2})?", value)
    if not match:
        return None

    return float(match.group())


def find_match(pattern, text, group=1):
    """Return a regex match or None."""
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(group).strip() if match else None


def normalize_text(text):
    """Normalize whitespace while retaining readable OCR text."""
    return re.sub(r"[ \t]+", " ", text).strip()


# ============================================================
# 3. LOAD THE INVOICE IMAGE
# ============================================================

if not Path(TESSERACT_PATH).is_file():
    raise FileNotFoundError(
        "Tesseract was not found at:\n"
        f"{TESSERACT_PATH}\n"
        "Check the installation path."
    )

if not IMAGE_PATH.is_file():
    raise FileNotFoundError(
        "Sample invoice image was not found at:\n"
        f"{IMAGE_PATH}\n"
        "Make sure sample_invoice.png is inside sample_documents."
    )

image = cv2.imread(str(IMAGE_PATH))

if image is None:
    raise ValueError("OpenCV could not read the invoice image.")

print("Invoice image loaded successfully.")


# ============================================================
# 4. OCR THE FULL INVOICE
# ============================================================

full_text = pytesseract.image_to_string(
    image,
    config="--psm 6"
)

text = normalize_text(full_text)

# Keep non-empty OCR lines for field and item extraction.
lines = [
    normalize_text(line)
    for line in full_text.splitlines()
    if normalize_text(line)
]

print("\n========== OCR TEXT ==========")
print(full_text)
print("======== END OCR TEXT ========\n")


# ============================================================
# 5. OCR THE INVOICE HEADER SEPARATELY
# ============================================================

height, width = image.shape[:2]

# Crop the upper-right header area, where invoice details appear.
x1 = int(width * 0.58)
x2 = int(width * 0.98)
y1 = int(height * 0.04)
y2 = int(height * 0.25)

header_crop = image[y1:y2, x1:x2]

header_text = ""

if header_crop.size > 0:
    enlarged = cv2.resize(
        header_crop,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)

    _, thresholded = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    header_text = pytesseract.image_to_string(
        thresholded,
        config="--psm 6"
    )

print("========== HEADER OCR ==========")
print(header_text)
print("======== END HEADER OCR ========\n")


# ============================================================
# 6. EXTRACT INVOICE FIELDS
# ============================================================

combined_text = full_text + "\n" + header_text

# Invoice number: search both full text and the enlarged header.
invoice_number = find_match(
    r"\b([A-Z]{1,5}\s*\d{6,12}\s*-\s*\d{1,5})\b",
    combined_text
)

if invoice_number:
    invoice_number = re.sub(r"\s+", "", invoice_number)

# Invoice date.
invoice_date = find_match(
    r"Invoice\s*Date\s*:?\s*(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})",
    combined_text
)

# Customer name: find the text immediately after BILL TO.
customer_name = None

for index, line in enumerate(lines):
    if re.search(r"\bBILL\s*TO\b", line, re.IGNORECASE):
        # The customer name can be on the same line or the next line.
        same_line = re.split(
            r"BILL\s*TO",
            line,
            flags=re.IGNORECASE
        )[-1].strip()

        if same_line and not re.search(
            r"PAYMENT|DETAILS",
            same_line,
            re.IGNORECASE
        ):
            customer_name = same_line
        elif index + 1 < len(lines):
            customer_name = lines[index + 1]

        break

if customer_name:
    # Remove payment details if OCR merged two columns together.
    customer_name = re.split(
        r"\s+(?:PAYMENT\s+DETAILS|Payment\s+Method)\b",
        customer_name,
        flags=re.IGNORECASE
    )[0].strip()

# Payment method.
payment_method = find_match(
    r"Payment\s*Method\s*:?\s*([A-Za-z]+)",
    combined_text
)

# Monetary totals.
subtotal_raw = find_match(
    r"Subtotal\s*[:=]?\s*₹?\s*([\d,]+\.\d{2})",
    combined_text
)

cgst_raw = find_match(
    r"CGST\s*\(?\s*\d+(?:\.\d+)?\s*%?\s*\)?"
    r"\s*[:=]?\s*₹?\s*([\d,]+\.\d{2})",
    combined_text
)

sgst_raw = find_match(
    r"SGST\s*\(?\s*\d+(?:\.\d+)?\s*%?\s*\)?"
    r"\s*[:=]?\s*₹?\s*([\d,]+\.\d{2})",
    combined_text
)

grand_total_raw = find_match(
    r"Grand\s*Total\s*[:=]?\s*₹?\s*([\d,]+\.\d{2})",
    combined_text
)

invoice = {
    "invoice_number": invoice_number,
    "invoice_date": invoice_date,
    "customer_name": customer_name,
    "payment_method": payment_method,
    "subtotal": clean_amount(subtotal_raw),
    "cgst": clean_amount(cgst_raw),
    "sgst": clean_amount(sgst_raw),
    "grand_total": clean_amount(grand_total_raw)
}


# ============================================================
# 7. EXTRACT LINE ITEMS
# ============================================================

items = []

# Match item rows containing description, quantity,
# unit price, and line total.
# OCR may omit serial numbers or merge some columns, so
# unmatched rows are not silently treated as valid items.

item_pattern = re.compile(
    r"^\s*\d*\s*[\).]?\s*"
    r"([A-Za-z][A-Za-z ()-]+?)\s+"
    r"(\d{1,2})\s+"
    r"([\d,]+\.\d{2})\s+"
    r"([\d,]+\.\d{2})\s*$"
)

for line in lines:
    match = item_pattern.match(line)

    if match:
        description = match.group(1).strip()
        quantity = int(match.group(2))
        unit_price = clean_amount(match.group(3))
        line_total = clean_amount(match.group(4))

        items.append({
            "description": description,
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": line_total
        })


# ============================================================
# 8. SAVE JSON OUTPUT
# ============================================================

result = {
    "invoice": invoice,
    "items": items,
    "ocr_text": full_text
}

with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
    json.dump(result, file, indent=4, ensure_ascii=False)


# ============================================================
# 9. SAVE CSV OUTPUTS
# ============================================================

# Invoice summary CSV.
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=invoice.keys())
    writer.writeheader()
    writer.writerow(invoice)

# Separate CSV for individual items.
ITEMS_CSV = BASE_DIR / "extracted_items.csv"

with open(ITEMS_CSV, "w", newline="", encoding="utf-8-sig") as file:
    item_fields = [
        "description",
        "quantity",
        "unit_price",
        "line_total"
    ]

    writer = csv.DictWriter(file, fieldnames=item_fields)
    writer.writeheader()
    writer.writerows(items)


# ============================================================
# 10. DISPLAY RESULTS
# ============================================================

print("\n========== EXTRACTED INVOICE ==========")

for key, value in invoice.items():
    print(f"{key}: {value}")

print("\n========== EXTRACTED LINE ITEMS ==========")

if items:
    for item in items:
        print(item)
else:
    print("No line items matched the current extraction pattern.")
    print("The OCR text is available in the JSON file for review.")

print("\n========== OUTPUT FILES ==========")
print(f"Invoice JSON : {OUTPUT_JSON}")
print(f"Invoice CSV  : {OUTPUT_CSV}")
print(f"Items CSV    : {ITEMS_CSV}")

missing_fields = [
    field for field, value in invoice.items()
    if value is None
]

if missing_fields:
    print("\nFields needing review:", ", ".join(missing_fields))
else:
    print("\nAll configured invoice fields were extracted.")

print("\nProcessing finished.")

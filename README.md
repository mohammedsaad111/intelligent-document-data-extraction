# Intelligent Document Data Extraction System

A Python-based document processing project that extracts structured information from invoice images using Optical Character Recognition (OCR).

## Project Overview

This project processes an invoice image, extracts its text, identifies important invoice fields and line items, and exports the results into JSON and CSV files.

It was developed as a personal project to practise Python, OCR, image processing, regular expressions, and structured data handling.

## Features

- Extract text from invoice images using Tesseract OCR
- Detect invoice number, date, customer name, and payment method
- Extract subtotal, CGST, SGST, and grand total
- Identify invoice line items, quantities, unit prices, and totals
- Export invoice information to JSON
- Export invoice summaries and line items to separate CSV files
- Display extracted results and missing fields in the terminal

## Technology Stack

- Python
- OpenCV
- Tesseract OCR
- pytesseract
- Regular expressions
- JSON and CSV

## Project Structure

```text
intelligent-document-data-extraction/
├── sample_documents/
│   └── sample_invoice.png
├── main.py
├── README.md
├── requirements.txt
└── .gitignore
```

The JSON and CSV output files are generated when the program runs and are intentionally excluded from Git.

## Requirements

- Python 3.10 or later
- Tesseract OCR installed on your system
- Python packages listed in `requirements.txt`

## Installation and Usage

### 1. Clone the repository

```bash
git clone https://github.com/mohammedsaad111/intelligent-document-data-extraction.git
cd intelligent-document-data-extraction
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Tesseract OCR

Install Tesseract OCR. If it is installed in a different location from the path configured in `main.py`, update the executable path in that file.

### 5. Run the project

The sample invoice is available at `sample_documents/sample_invoice.png`.

Run:

```bash
python main.py
```

## Output Files

| File | Description |
|---|---|
| `extracted_invoice.json` | Invoice fields, line items, and OCR text |
| `extracted_invoice.csv` | Invoice-level data in tabular format |
| `extracted_items.csv` | Extracted items, quantities, prices, and totals |

These files are created when the program runs.

## Limitations

OCR accuracy depends on image quality, text alignment, and invoice layout. The current extraction rules are designed for the sample invoice format and may require adjustments for different templates.

Extracted data should be verified before being used for accounting or other business purposes.

## Future Improvements

- Support for multiple invoice layouts
- Better image preprocessing and OCR accuracy
- More robust field and line-item detection
- Validation of extracted amounts and totals
- A simple user interface for uploading documents

## Author

**Mohammed Saad**

Personal project developed to build practical experience in Python, OCR, and document data extraction.

import pathlib, subprocess, json, base64, sys

def ocr_image(path: pathlib.Path) -> str:
    """Run Tesseract OCR on an image file and return extracted text.
    Requires tesseract to be installed in the sandbox.
    """
    result = subprocess.run(
        ["tesseract", str(path), "stdout", "-l", "eng"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.stdout.strip()

def parse_file(path_str: str):
    p = pathlib.Path(path_str)
    if not p.exists():
        return {"error": f"File not found: {path_str}"}
    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf"}:
        text = ocr_image(p)
        return {"type": "ocr", "content": text}
    if p.suffix.lower() in {".csv", ".tsv"}:
        import csv
        with p.open(newline="") as f:
            rows = list(csv.DictReader(f))
        return {"type": "table", "rows": rows}
    return {"error": f"Unsupported file type: {p.suffix}"}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: parse_file.py <path>"}))
        sys.exit(1)
    out = parse_file(sys.argv[1])
    print(json.dumps(out, ensure_ascii=False, indent=2))

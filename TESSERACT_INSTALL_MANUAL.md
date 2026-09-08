# TESSERACT INSTALL — MANUAL STEPS
**Why this exists:** Silent install was attempted (you approved "do all") but failed — Inno Setup requires elevation or a different flag set. Downloaded installer is staged at `~/AppData/Local/Temp/tesseract-stage/tesseract-installer.exe` for manual run.

## What was done
1. ✅ Downloaded UB-Mannheim Tesseract 5.4.0.20240606 (48 MB, SHA256 `c885fff6998e0608ba4bb8ab51436e1c6775c2bafc2559a19b423e18678b60c9`)
2. ✅ Staged at `C:\Users\mobil\AppData\Local\Temp\tesseract-stage\tesseract-installer.exe`
3. ❌ Silent install (`/S` flag) ran cleanly with exit 0 but produced no install — Inno Setup didn't unpack

## What you need to do (manual)

### Option A — Right-click installer and "Run as administrator"
1. Open File Explorer
2. Navigate to `C:\Users\mobil\AppData\Local\Temp\tesseract-stage\`
3. Right-click `tesseract-installer.exe` → "Run as administrator"
4. Click through the GUI (it's a standard Next-Next-Finish installer)
5. Install to default `C:\Program Files\Tesseract-OCR\`

### Option B — Use chocolatey (faster if you have it)
```bash
choco install tesseract --version=5.4.0
```

### Option C — winget
```bash
winget install UB-Mannheim.TesseractForWindows
```

## After install

### Add to PATH (one of these methods)

**PowerShell (admin):**
```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\Tesseract-OCR", "Machine")
```

**GUI:** Win+R → `sysdm.cpl` → Advanced → Environment Variables → Path → Edit → New → `C:\Program Files\Tesseract-OCR\`

### Verify
```bash
tesseract --version
# Expected: tesseract 5.4.0.20240606
```

### Test from Python
```bash
cd "C:/Users/mobil/orca/projects/my 1st"
.venv312/Scripts/python.exe -c "import pytesseract; from PIL import Image; print(pytesseract.image_to_string('test.png'))"
```

## What this enables

- AADE Greek tax OCR workflow (`aade_ocr_engine.py`)
- General OCR (pytesseract stack already in venv312)
- PDF scanning (pdf2image already installed)
- Hermes skills: ocr-and-documents, pdf

## If install fails

Try **Option C** (winget) first — it usually works without admin elevation on modern Windows:

```bash
winget install UB-Mannheim.TesseractForWindows --accept-package-agreements
```

If winget is blocked by the organization, contact IT for the install — Tesseract is a benign utility used in many legitimate contexts (PDF scanning, document digitization, accessibility).
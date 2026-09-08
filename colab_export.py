# colab_export.py - Run INSIDE Google Colab to export your trained model
# ----------------------------------------------------------------------
# This script packages your fine-tuned model and downloads it locally.
# Paste it into a Colab cell and run it.
# ----------------------------------------------------------------------

import os, shutil, subprocess

# === Configuration ===
MODEL_PATH = "meta-llama/Llama-3.2-3B-Instruct"
EXPORT_DIR = "/content/drive/MyDrive/trained_models/test-model"
DRIVE_PATH = "/content/drive/MyDrive/trained_models"

# === Mount Google Drive ===
from google.colab import drive
drive.mount('/content/drive')

# === Create export directory ===
os.makedirs(EXPORT_DIR, exist_ok=True)
print(f"Exporting model to {EXPORT_DIR}...")

# === Copy model files (adjust source as needed) ===
# Option A: Local fine-tuned checkpoint
# shutil.copytree(MODEL_PATH, EXPORT_DIR, dirs_exist_ok=True)

# Option B: Push to HuggingFace Hub (recommended)
# from huggingface_hub import HfApi
# api = HfApi()
# api.create_repo("", exist_ok=True, private=True)
# api.upload_folder(folder_path=MODEL_PATH, repo_id="")

# Option C: Download from Colab to local machine
from google.colab import files

# Zip the model
shutil.make_archive('/content/model_export', 'zip', MODEL_PATH)
print("Model zipped. Starting download...")

# Trigger browser download
files.download('/content/model_export.zip')
print("Done! Move the zip to your local machine and unzip into models/")
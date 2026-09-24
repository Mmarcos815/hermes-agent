#!/usr/bin/env python3
"""
BIONIC CAPTCHA SOLVER v1.0
FREE CAPTCHA solving — no API keys, no costs.
Uses Whisper (speech-to-text) + Tesseract (OCR).
FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL PURPOSES ONLY
"""
import os
import sys
import json
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

# ── AUDIO CAPTCHA SOLVER ─────────────────────────────────────────────────
class AudioCaptchaSolver:
    """Solve audio CAPTCHAs using Whisper speech recognition."""
    
    def __init__(self):
        self.available = False
        self.whisper_path = None
        self._check_whisper()
    
    def _check_whisper(self):
        """Check if Whisper is available."""
        # Check for whisper.cpp (lightweight C++ implementation)
        result = subprocess.run(["which", "whisper"], capture_output=True, text=True)
        if result.returncode == 0:
            self.whisper_path = result.stdout.strip()
            self.available = True
            return
        
        # Check for Python whisper
        try:
            import whisper
            self.available = True
        except ImportError:
            pass
    
    def solve(self, audio_path: str) -> Optional[str]:
        """Solve audio CAPTCHA."""
        if not self.available:
            return None
        
        # Method 1: whisper.cpp (fast, lightweight)
        if self.whisper_path:
            return self._solve_whisper_cpp(audio_path)
        
        # Method 2: Python whisper
        return self._solve_whisper_python(audio_path)
    
    def _solve_whisper_cpp(self, audio_path: str) -> Optional[str]:
        """Use whisper.cpp for fast solving."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
                output_path = f.name
            
            subprocess.run([
                self.whisper_path,
                "-f", audio_path,
                "-otxt",
                "-of", output_path,
            ], capture_output=True, timeout=30)
            
            if Path(output_path).exists():
                with open(output_path) as f:
                    text = f.read().strip()
                os.unlink(output_path)
                return text
        except:
            pass
        return None
    
    def _solve_whisper_python(self, audio_path: str) -> Optional[str]:
        """Use Python Whisper."""
        try:
            import whisper
            model = whisper.load_model("tiny")  # Small model, fast
            result = model.transcribe(audio_path)
            return result["text"].strip()
        except:
            return None

# ── IMAGE CAPTCHA SOLVER ─────────────────────────────────────────────────
class ImageCaptchaSolver:
    """Solve image CAPTCHAs using Tesseract OCR."""
    
    def __init__(self):
        self.available = False
        self._check_tesseract()
    
    def _check_tesseract(self):
        """Check if Tesseract is installed."""
        result = subprocess.run(["which", "tesseract"], capture_output=True, text=True)
        if result.returncode == 0:
            self.available = True
    
    def solve(self, image_path: str) -> Optional[str]:
        """Solve image CAPTCHA."""
        if not self.available:
            return None
        
        try:
            # Run Tesseract OCR
            result = subprocess.run([
                "tesseract",
                image_path,
                "stdout",
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None

# ── RECAPTCHA BYPASS ────────────────────────────────────────────────────
class ReCaptchaBypass:
    """Bypass reCAPTCHA using audio challenge method."""
    
    def __init__(self):
        self.audio_solver = AudioCaptchaSolver()
    
    def get_audio_challenge(self, site_key: str, page_url: str) -> Optional[str]:
        """
        Get reCAPTCHA audio challenge.
        
        1. Navigate to page with reCAPTCHA
        2. Click audio challenge button
        3. Download audio file
        4. Solve with Whisper
        5. Enter solution
        """
        # This requires browser automation
        # Implementation depends on Playwright/Selenium
        pass
    
    def solve_audio_challenge(self, audio_url: str) -> Optional[str]:
        """Solve reCAPTCHA audio challenge."""
        if not self.audio_solver.available:
            return None
        
        # Download audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            audio_path = f.name
        
        try:
            resp = requests.get(audio_url, timeout=10)
            with open(audio_path, "wb") as f:
                f.write(resp.content)
            
            # Solve
            return self.audio_solver.solve(audio_path)
        finally:
            if Path(audio_path).exists():
                os.unlink(audio_path)

# ── HCAPTCHA BYPASS ──────────────────────────────────────────────────────
class HCaptchaBypass:
    """Bypass hCaptcha using free methods."""
    
    def __init__(self):
        self.image_solver = ImageCaptchaSolver()
    
    def solve_image_challenge(self, images: list, question: str) -> Optional[list]:
        """
        Solve hCaptcha image challenge.
        
        hCaptcha shows 9 images and asks to click matching ones.
        Uses image recognition to identify correct images.
        """
        # This requires image recognition AI
        # For free, we'd need to use a local model
        pass

# ── CAPTCHA MANAGER ───────────────────────────────────────────────────────
class CaptchaManager:
    """Manages all CAPTCHA solving methods."""
    
    def __init__(self):
        self.audio_solver = AudioCaptchaSolver()
        self.image_solver = ImageCaptchaSolver()
        self.recaptcha = ReCaptchaBypass()
        self.hcaptcha = HCaptchaBypass()
        self.stats = {"attempts": 0, "solved": 0, "failed": 0}
    
    def solve_audio(self, audio_path: str) -> Optional[str]:
        """Solve audio CAPTCHA."""
        self.stats["attempts"] += 1
        result = self.audio_solver.solve(audio_path)
        if result:
            self.stats["solved"] += 1
        else:
            self.stats["failed"] += 1
        return result
    
    def solve_image(self, image_path: str) -> Optional[str]:
        """Solve image CAPTCHA."""
        self.stats["attempts"] += 1
        result = self.image_solver.solve(image_path)
        if result:
            self.stats["solved"] += 1
        else:
            self.stats["failed"] += 1
        return result
    
    def get_stats(self):
        return self.stats

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bionic_captcha.py audio|image|stats")
        print("  audio <file> - Solve audio CAPTCHA")
        print("  image <file> - Solve image CAPTCHA")
        print("  stats - Show solving statistics")
        sys.exit(1)
    
    cmd = sys.argv[1]
    manager = CaptchaManager()
    
    if cmd == "audio":
        if len(sys.argv) < 3:
            print("Usage: python bionic_captcha.py audio <file>")
            sys.exit(1)
        result = manager.solve_audio(sys.argv[2])
        print(f"Result: {result}")
    
    elif cmd == "image":
        if len(sys.argv) < 3:
            print("Usage: python bionic_captcha.py image <file>")
            sys.exit(1)
        result = manager.solve_image(sys.argv[2])
        print(f"Result: {result}")
    
    elif cmd == "stats":
        print(json.dumps(manager.get_stats(), indent=2))
    
    else:
        print("Unknown command")

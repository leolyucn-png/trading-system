#!/opt/homebrew/bin/python3
"""
Image OCR - 图片文字识别

用法:
    python ocr.py <image_path> [--lang chi_sim+eng]

支持中英文混合识别，适用于股票持仓截图、K线图等。
"""

import sys
import os

try:
    from PIL import Image
except ImportError:
    Image = None

def ocr_image(image_path: str, lang: str = "chi_sim+eng") -> str:
    """
    Extract text from image using Tesseract OCR.

    Args:
        image_path: Path to image file (jpg, png, etc.)
        lang: Tesseract language pack(s), e.g. "chi_sim+eng"

    Returns:
        Extracted text string
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    import pytesseract

    if Image:
        img = Image.open(image_path)
    else:
        # Use tesseract directly with file path
        import subprocess
        result = subprocess.run(
            ["tesseract", image_path, "stdout", "-l", lang],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()

    text = pytesseract.image_to_string(img, lang=lang)
    return text.strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ocr.py <image_path> [--lang chi_sim+eng]", file=sys.stderr)
        sys.exit(1)

    image_file = sys.argv[1]
    lang = "chi_sim+eng"
    if "--lang" in sys.argv:
        idx = sys.argv.index("--lang")
        if idx + 1 < len(sys.argv):
            lang = sys.argv[idx + 1]

    try:
        result = ocr_image(image_file, lang)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

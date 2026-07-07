---
name: image-ocr
description: "提取图片中的文字信息，支持中英文。用于阅读持仓截图、K线图标注、新闻截图等。依赖tesseract + chi_sim中文包。"
---

# Image OCR

从图片中提取文字，用于读取股票持仓截图、交易记录图片、新闻截图等。

## 依赖

- `tesseract` 5.5.2（已安装）
- `pytesseract` 0.3.13（已安装）
- 中文包：`chi_sim`（已安装）

## 使用

```python
from skills.image-ocr.scripts.ocr import ocr_image

text = ocr_image("/path/to/image.jpg", lang="chi_sim+eng")
print(text)
```

## 适用场景

- 读取东方财富/同花顺持仓截图
- 提取K线图上的数字标注
- 读取新闻/公告截图
- 识别交易确认页面

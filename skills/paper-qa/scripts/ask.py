#!/usr/bin/env python3
"""Paper-QA Lite: 论文PDF问答（使用LinoAPI Claude）"""
import sys, os

# 使用venv的Python 3.14
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/.venv-py314/lib/python3.14/site-packages"))

from openai import OpenAI
import PyPDF2
import re

OPENAI_BASE = "https://linoapi.com.cn/v1"
OPENAI_KEY = "sk-V5uPp0GjfbbePSW6o6jjDHXRn4IqzIwrDPAtihPvU5lzMcw7"
MODEL = "claude-sonnet-4-20250514"
MAX_CHUNK = 4000

def extract_text(path):
    """从PDF/TXT/MD提取文本"""
    ext = os.path.splitext(path)[1].lower()
    if ext == '.pdf':
        text = ""
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    elif ext in ['.txt', '.md']:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    elif ext == '.docx':
        # 简单处理docx
        try:
            from docx import Document
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        except:
            return f"[不支持直接读取docx，请在Word中另存为PDF后重试]"
    else:
        return f"[不支持格式: {ext}]"

def ask(pdf_path, question):
    if not os.path.exists(pdf_path):
        return f"❌ 文件不存在: {pdf_path}"
    
    text = extract_text(pdf_path)
    if len(text) < 50:
        return f"❌ 文本过短或无内容"
    
    # 截断到最大token
    text = text[:15000]
    
    client = OpenAI(api_key=OPENAI_KEY, base_url=OPENAI_BASE)
    
    system_prompt = f"""你是学术论文分析助手。基于以下论文文本回答问题。
如果文本中没有相关信息，请明确说明找不到。

论文文本:
{text[:MAX_CHUNK*3]}"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=1000,
            temperature=0.1
        )
        return f"📄 {os.path.basename(pdf_path)}\n❓ {question}\n\n{resp.choices[0].message.content}"
    except Exception as e:
        return f"❌ LinoAPI错误: {str(e)}"

def summarize(path):
    return ask(path, "请用中文总结这篇论文的核心论点、研究方法和主要发现（300字以内）。格式：\n【核心论点】\n【研究方法】\n【主要发现】")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 ask.py <PDF路径> \"<问题>\"")
        print("  python3 ask.py summary <PDF路径>")
        sys.exit(1)
    
    if sys.argv[1] == "summary" and len(sys.argv) >= 3:
        print(summarize(" ".join(sys.argv[2:])))
    elif len(sys.argv) >= 3:
        pdf = sys.argv[1]
        question = " ".join(sys.argv[2:])
        print(ask(pdf, question))
    else:
        print("❌ 参数不足。输入: python3 ask.py <PDF路径> \"<问题>\"")

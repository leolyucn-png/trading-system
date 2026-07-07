---
name: voice-transcriber
description: "转写Telegram语音消息为文字，使用本地 faster-whisper 模型，支持中英文。依赖 /tmp/whisper_venv 虚拟环境。"
---

# Voice Transcriber

将Telegram语音附件（ogg/opus/mp3/wav）转写为文字。使用本地`faster-whisper`模型（base，CPU int8），无需联网API。

## 依赖

```bash
# 虚拟环境 (已安装)
/tmp/whisper_venv/bin/python3

# 转写脚本
skills/voice-transcriber/scripts/transcribe.py
```

## 使用

```python
from skills.voice-transcriber.scripts.transcribe import transcribe_audio

text = transcribe_audio("/path/to/audio.ogg", language="zh")
print(text)
```

## 工作流程

1. 收到 Telegram 语音消息 → `media://inbound/<uuid>.ogg` 文件
2. 调用 `transcribe_audio()` 转写
3. 返回文字结果

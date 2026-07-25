#!/usr/bin/env python3
"""
Supervision demo: 黑神话悟空 (Black Myth: Wukong) 图片分析
用 YOLOv8 做目标检测 + Supervision 做标注
"""
import sys
import os

# 抑制 torch 内部 deprecation warning
os.environ["PYTHONWARNINGS"] = "ignore"
import warnings
warnings.filterwarnings("ignore")

import cv2
import supervision as sv
from ultralytics import YOLO

IMAGE_PATH = "/Users/lyu/.openclaw/workspace/test_wukong.jpg"
OUTPUT_PATH = "/Users/lyu/.openclaw/workspace/test_wukong_annotated.jpg"

print("=" * 60)
print("🦁 Supervision 跑起来了！")
print("=" * 60)

# ---- 1. 加载模型 ----
print("\n📦 加载 YOLOv8n (轻量版)...")
model = YOLO("yolov8n.pt")  # COCO 预训练，轻量
print("   ✅ 模型加载完成")

# ---- 2. 跑推理 ----
print(f"\n🔍 分析图片: {os.path.basename(IMAGE_PATH)}")
results = model(IMAGE_PATH, verbose=False)[0]

# ---- 3. 用 Supervision 包装结果 ----
detections = sv.Detections.from_ultralytics(results)
print(f"   📊 检测到 {len(detections)} 个目标")

# ---- 4. 标注并保存 ----
# 边界框 + 标签
box_annotator = sv.BoxAnnotator()
label_annotator = sv.LabelAnnotator()

image = cv2.imread(IMAGE_PATH)
annotated = box_annotator.annotate(scene=image.copy(), detections=detections)
annotated = label_annotator.annotate(
    scene=annotated,
    detections=detections,
    labels=[f"{model.names[cls]} {conf:.2f}"
            for cls, conf in zip(detections.class_id, detections.confidence)]
)

cv2.imwrite(OUTPUT_PATH, annotated)
print(f"   💾 标注图已保存: {os.path.basename(OUTPUT_PATH)}")

# ---- 5. 输出检测结果详情 ----
print("\n📋 检测详情:")
print(f"   {'类别':<20} {'置信度':<10} {'坐标 (xyxy)':<40}")
print(f"   {'-'*70}")
for i in range(len(detections)):
    cls_name = model.names[detections.class_id[i]]
    conf = detections.confidence[i]
    xyxy = detections.xyxy[i]
    print(f"   {cls_name:<20} {conf:<10.3f} {str(xyxy):<40}")

# ---- 6. 分类统计 ----
from collections import Counter
class_counts = Counter(model.names[c] for c in detections.class_id)
print(f"\n📊 目标分类统计:")
for cls, count in class_counts.most_common():
    print(f"   · {cls}: {count} 个")

print(f"\n✅ 完成！输出路径: {OUTPUT_PATH}")

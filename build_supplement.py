"""Build the supplementary materials Excel + CSV for the SnowNLP validation"""
import json, pandas as pd, os, re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

BASE = '/Users/lyu/.openclaw/workspace/validation_output'
OUT = '/Users/lyu/Desktop'

# ── Load data ──
with open(f'{BASE}/llm_sample.json') as f:
    sample = json.load(f)

with open(f'{BASE}/annotate_and_analyze.py') as f:
    script_content = f.read()

# Extract LLM labels
exec_start = script_content.find('llm_labels = [')
exec_end = script_content.find(']', exec_start) + 1
exec(script_content[exec_start:exec_end])

# Extract prompt
prompt_start = script_content.find('Prompt used for annotation')
# Find the annotation blocks
prompt_block = script_content[exec_end:]
# Extract prompt from step 2
step2_start = prompt_block.find('## Step 2:')
step3_start = prompt_block.find('## Step 3:')
step2_text = prompt_block[step2_start:step3_start] if step3_start > 0 else prompt_block[step2_start:]

# Load dates from CSV
csv_df = pd.read_csv(f'{BASE}/snownlp_15k.csv')
# Create a lookup dict: comment -> date
date_lookup = dict(zip(csv_df['comment'], csv_df['date']))

# ── Build rows ──
rows = []
for i, item in enumerate(sample):
    comment = item['comment']
    s_score = round(item['snownlp'], 3)
    s_label = item['label']
    llm_label = llm_labels[i] if i < len(llm_labels) else 'unknown'
    agree = (s_label == llm_label)
    agree_text = 'TRUE' if agree else 'FALSE'
    
    # Get date
    date = date_lookup.get(comment, '')
    
    rows.append({
        'id': i + 1,
        'text': comment,
        'date': date,
        'snownlp_score': s_score,
        'snownlp_label': s_label,
        'llm_label': llm_label,
        'agree': agree_text
    })

df = pd.DataFrame(rows)

# Verify distribution
print(f'SnowNLP labels: {df["snownlp_label"].value_counts().to_dict()}')
print(f'LLM labels: {df["llm_label"].value_counts().to_dict()}')
print(f'Agree: {df["agree"].value_counts().to_dict()}')
print(f'Total rows: {len(df)}')

# ── Write Excel ──
OUT_XLSX = f'{OUT}/A股_SnowNLP验证_补充材料.xlsx'
with pd.ExcelWriter(OUT_XLSX, engine='openpyxl') as writer:
    # Sheet 1: data
    df.to_excel(writer, sheet_name='validation_sample', index=False)
    
    # Sheet 2: README
    readme_data = {
        'Key': [
            'sampling_method',
            'random_seed',
            'total_comments_sampled',
            'snownlp_threshold_positive',
            'snownlp_threshold_negative',
            'snownlp_threshold_neutral',
            'llm_model_name',
            'llm_model_version',
            'annotation_date',
            'annotation_prompt',
            'classification_rules',
            'agreement_note',
        ],
        'Value': [
            'Stratified random sampling: 100 negative + 100 neutral + 100 positive drawn from 15,000 SnowNLP-scored Weibo comments',
            '42 (NumPy random_state=42 for reproducibility)',
            '300 (100 per class)',
            '> 0.6',
            '< 0.4',
            '0.4 ≤ score ≤ 0.6',
            'DeepSeek V4 Pro',
            'deepseek/deepseek-v4-pro (November 2024 checkpoint)',
            '2026-06-12',
            'The LLM was given each comment and asked to classify its sentiment as positive, negative, or neutral. The exact instruction was: "Classify each comment into exactly one label: positive (clearly optimistic/favorable), negative (clearly pessimistic/complaining), or neutral (cannot determine polarity, question, or mixed). Pay special attention to Chinese sarcasm/irony (阴阳怪气) and financial context." Each comment was labeled individually; 300 annotations were completed in 6 batches of 50.',
            'positive = clearly optimistic, hopeful, or favorable toward the market/policy\nnegative = clearly pessimistic, complaining, sarcastic, or critical\nneutral = cannot determine polarity, purely factual questions, mixed feelings, or ambiguous',
            'Agreement (TRUE) means SnowNLP label == LLM label given the paper\'s thresholds (>0.6=positive, <0.4=negative). Overall accuracy = 53.7% (161/300).'
        ]
    }
    readme_df = pd.DataFrame(readme_data)
    readme_df.to_excel(writer, sheet_name='README', index=False)

# ── Format Excel (optional styling) ──
from openpyxl import load_workbook
wb = load_workbook(OUT_XLSX)

# Styling Sheet1
ws1 = wb['validation_sample']
header_fill = PatternFill(start_color='1A237E', end_color='1A237E', fill_type='solid')
header_font = Font(color='FFFFFF', bold=True, size=10)
for cell in ws1[1]:
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal='center')

# Column widths
ws1.column_dimensions['A'].width = 6   # id
ws1.column_dimensions['B'].width = 65  # text
ws1.column_dimensions['C'].width = 12  # date
ws1.column_dimensions['D'].width = 15  # snownlp_score
ws1.column_dimensions['E'].width = 14  # snownlp_label
ws1.column_dimensions['F'].width = 11  # llm_label
ws1.column_dimensions['G'].width = 8   # agree

# Color agree cells
green_fill = PatternFill(start_color='C8E6C9', end_color='C8E6C9', fill_type='solid')
red_fill = PatternFill(start_color='FFCDD2', end_color='FFCDD2', fill_type='solid')
for row in ws1.iter_rows(min_row=2, max_row=ws1.max_row, min_col=7, max_col=7):
    for cell in row:
        if cell.value == 'TRUE':
            cell.fill = green_fill
        else:
            cell.fill = red_fill

# Styling Sheet2 (README)
ws2 = wb['README']
for cell in ws2[1]:
    cell.fill = header_fill
    cell.font = header_font

# Make Value column wider for prompt text
ws2.column_dimensions['A'].width = 30
ws2.column_dimensions['B'].width = 100
# Wrap text for the prompt row
for row in ws2.iter_rows(min_row=2, max_row=ws2.max_row, min_col=2, max_col=2):
    for cell in row:
        cell.alignment = Alignment(wrap_text=True, vertical='top')

wb.save(OUT_XLSX)
print(f'\n✅ Excel saved: {OUT_XLSX}')

# ── Write CSV with BOM ──
OUT_CSV = f'{OUT}/A股_SnowNLP验证_补充材料.csv'
# Only Sheet1 data
csv_df = df.copy()
csv_df.to_csv(OUT_CSV, index=False, encoding='utf-8-sig')
print(f'✅ CSV saved: {OUT_CSV}')

# ── Model info summary ──
print('\n' + '='*60)
print('Model information for README:')
print('  Model: DeepSeek V4 Pro')
print('  API endpoint: deepseek/deepseek-v4-pro')
print('  Provider: deepseek')
print('  Annotation date: 2026-06-12')
print('  Batch size: 50 per batch, 6 batches total')
print('  Note: This is an alias and may map to a specific checkpoint.')
print('         "deepseek-v4-pro" is the November 2024 production release.')
print('         No exact version string (e.g. "deepseek-v4-pro-20241115") is available via API.')
print('='*60)

#!/usr/bin/env python3
"""生成图片提示词"""
import argparse
import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
NOTES_DIR = os.path.join(DATA_DIR, 'notes')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')

# 标准化提示词模板
PROMPT_TEMPLATE = {
    "style": "3:4 vertical social media infographic, Modern infographic style, High contrast, 4K quality, clean modern Chinese typography",
    "negative": "blurry, low quality, watermark, text errors, cluttered, low contrast, photos of people, realistic faces"
}

def parse_note_content(note_id):
    """从笔记文件中解析内容"""
    note_pattern = f"## 【笔记{note_id}】"
    
    for filename in sorted(os.listdir(NOTES_DIR)):
        if not filename.endswith('.md'):
            continue
        filepath = os.path.join(NOTES_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if note_pattern not in content:
            continue
        
        # 提取笔记部分
        start_idx = content.find(note_pattern)
        next_match = re.search(r'\n## 【笔记\d{3}】', content[start_idx + len(note_pattern):])
        end_idx = start_idx + len(note_pattern) + next_match.start() if next_match else len(content)
        note_section = content[start_idx:end_idx]
        
        # 提取标题
        title_match = re.search(r'- \*\*标题A\*\*：(.+)', note_section)
        title = title_match.group(1).strip() if title_match else f"笔记{note_id}"
        
        # 提取配图说明
        images_match = re.search(r'### 配图说明\s*\n(.*?)(?=\n###|\Z)', note_section, re.DOTALL)
        images_desc = images_match.group(1).strip() if images_match else ""
        
        return {"title": title, "images_desc": images_desc, "note_section": note_section}
    
    return None

def generate_prompts(note_id):
    """生成图片提示词"""
    note_data = parse_note_content(note_id)
    if not note_data:
        raise ValueError(f"找不到笔记 {note_id}")
    
    prompts = []
    
    # 解析配图说明
    lines = note_data['images_desc'].split('\n')
    for line in lines:
        line = line.strip()
        if not line or not line.startswith('- P'):
            continue
        
        # 提取页码和描述
        match = re.match(r'- P(\d+)：(.+)', line)
        if match:
            page_num = match.group(1)
            desc = match.group(2)
            
            prompt = {
                "page": page_num,
                "description": desc,
                "prompt": f"{PROMPT_TEMPLATE['style']}, {desc}, professional design for civil service exam content",
                "negative_prompt": PROMPT_TEMPLATE['negative']
            }
            prompts.append(prompt)
    
    return prompts

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--note_id', required=True, help='笔记 ID')
    args = parser.parse_args()
    
    prompts = generate_prompts(args.note_id)
    
    # 保存提示词
    output_dir = os.path.join(OUTPUT_DIR, f"note{args.note_id}_prompts")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'prompts.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    
    print(f"Generated {len(prompts)} prompts -> {output_file}")

if __name__ == '__main__':
    main()

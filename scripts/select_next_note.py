#!/usr/bin/env python3
"""选择下一篇未使用的笔记"""
import json
import os
import re
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
NOTES_DIR = os.path.join(DATA_DIR, 'notes')
LOG_FILE = os.path.join(DATA_DIR, 'usage_log.json')

def get_used_notes():
    """获取已使用的笔记列表"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('used_notes', []))
    return set()

def get_all_note_ids():
    """从笔记文件中提取所有笔记 ID"""
    note_ids = []
    for filename in sorted(os.listdir(NOTES_DIR)):
        if not filename.endswith('.md'):
            continue
        filepath = os.path.join(NOTES_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # 匹配 ## 【笔记XXX】 格式
        matches = re.findall(r'## 【笔记(\d{3})】', content)
        note_ids.extend(matches)
    return sorted(note_ids)

def select_next_note():
    """选择下一篇未使用的笔记"""
    used = get_used_notes()
    all_ids = get_all_note_ids()
    
    for note_id in all_ids:
        if note_id not in used:
            return note_id
    
    return None

if __name__ == '__main__':
    next_note = select_next_note()
    if next_note:
        print(next_note)
        sys.exit(0)
    else:
        print("ERROR: 没有可用的笔记了", file=sys.stderr)
        sys.exit(1)

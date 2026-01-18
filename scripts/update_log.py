#!/usr/bin/env python3
"""更新执行日志"""
import argparse
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
LOG_FILE = os.path.join(DATA_DIR, 'usage_log.json')

def update_log(note_id):
    """将笔记 ID 添加到已使用列表"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"used_notes": [], "total_available": 100}
    
    if note_id not in data['used_notes']:
        data['used_notes'].append(note_id)
        data['used_notes'].sort()
    
    data['last_updated'] = datetime.now().isoformat()
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 已更新日志: 笔记 {note_id} 标记为已使用")
    print(f"  已使用: {len(data['used_notes'])}/{data['total_available']}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--note_id', required=True, help='笔记 ID')
    args = parser.parse_args()
    
    update_log(args.note_id)

if __name__ == '__main__':
    main()

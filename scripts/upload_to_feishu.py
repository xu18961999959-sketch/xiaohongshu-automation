#!/usr/bin/env python3
"""上传笔记内容和图片到飞书多维表格"""
import argparse
import glob
import json
import os
import re
import requests

# 从环境变量读取配置
APP_ID = os.environ.get('FEISHU_APP_ID')
APP_SECRET = os.environ.get('FEISHU_APP_SECRET')
APP_TOKEN = os.environ.get('FEISHU_APP_TOKEN')
TABLE_ID = os.environ.get('FEISHU_TABLE_ID')

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
NOTES_DIR = os.path.join(DATA_DIR, 'notes')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')

def get_tenant_access_token():
    """获取飞书 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 200 and resp.json().get("code") == 0:
        return resp.json()["tenant_access_token"]
    raise Exception(f"获取 token 失败: {resp.text}")

def parse_note_content(note_id):
    """解析笔记内容"""
    note_pattern = f"## 【笔记{note_id}】"
    
    for filename in sorted(os.listdir(NOTES_DIR)):
        if not filename.endswith('.md'):
            continue
        filepath = os.path.join(NOTES_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if note_pattern not in content:
            continue
        
        start_idx = content.find(note_pattern)
        next_match = re.search(r'\n## 【笔记\d{3}】', content[start_idx + len(note_pattern):])
        end_idx = start_idx + len(note_pattern) + next_match.start() if next_match else len(content)
        note_section = content[start_idx:end_idx]
        
        # 提取标题
        title_match = re.search(r'- \*\*标题A\*\*：(.+)', note_section)
        title = title_match.group(1).strip() if title_match else f"笔记{note_id}"
        
        # 提取正文
        content_match = re.search(r'### 正文内容\s*\n(.*?)\n### 配图说明', note_section, re.DOTALL)
        main_content = content_match.group(1).strip() if content_match else ""
        
        # 提取话题标签
        tags_match = re.search(r'### 话题标签\s*\n```\s*\n(.+?)\n```', note_section, re.DOTALL)
        if tags_match:
            tags_str = tags_match.group(1).strip()
            tags = [t.strip() for t in tags_str.split('#') if t.strip()]
        else:
            tags = []
        
        return {"title": title, "content": main_content, "tags": tags}
    
    return None

def upload_images(access_token, note_id):
    """上传图片到飞书"""
    images_dir = os.path.join(OUTPUT_DIR, f"note{note_id}_images")
    if not os.path.exists(images_dir):
        print(f"警告: 图片目录不存在 {images_dir}")
        return []
    
    image_files = sorted(glob.glob(os.path.join(images_dir, "p*.png")))
    files_tokens = []
    
    for img_path in image_files:
        img_name = os.path.basename(img_path)
        size = os.path.getsize(img_path)
        
        url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        with open(img_path, 'rb') as f:
            files = {'file': (img_name, f)}
            data = {
                'file_name': img_name,
                'parent_type': 'bitable_image',
                'parent_node': APP_TOKEN,
                'size': str(size)
            }
            resp = requests.post(url, headers=headers, files=files, data=data)
            
            if resp.status_code == 200 and resp.json().get('code') == 0:
                file_token = resp.json()['data']['file_token']
                files_tokens.append({"file_token": file_token})
                print(f"  ✓ 上传 {img_name}")
            else:
                print(f"  ✗ 上传失败 {img_name}: {resp.text}")
    
    return files_tokens

def create_or_update_record(access_token, note_id, note_data, files_tokens):
    """创建或更新飞书记录"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # 搜索现有记录
    search_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/search"
    payload = {
        "filter": {
            "conjunction": "and",
            "conditions": [{"field_name": "笔记ID", "operator": "is", "value": [note_id]}]
        }
    }
    
    resp = requests.post(search_url, headers=headers, json=payload)
    items = resp.json().get('data', {}).get('items', [])
    
    fields = {
        "笔记ID": note_id,
        "笔记标题": note_data["title"],
        "笔记内容": note_data["content"],
        "笔记话题": note_data["tags"],
        "生成的配图(附件)": files_tokens,
        "笔记图片链接": f"已上传 {len(files_tokens)} 张图片至附件"
    }
    
    if items:
        # 更新现有记录
        record_id = items[0]['record_id']
        update_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
        resp = requests.put(update_url, headers=headers, json={"fields": fields})
        print(f"✓ 更新记录 {record_id}")
    else:
        # 创建新记录
        create_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
        resp = requests.post(create_url, headers=headers, json={"fields": fields})
        record_id = resp.json().get('data', {}).get('record', {}).get('record_id')
        print(f"✓ 创建记录 {record_id}")
    
    return resp.json()

def main():
    # 验证环境变量
    required_vars = ['FEISHU_APP_ID', 'FEISHU_APP_SECRET', 'FEISHU_APP_TOKEN', 'FEISHU_TABLE_ID']
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        print(f"错误: 缺少环境变量 {missing}")
        exit(1)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--note_id', required=True, help='笔记 ID')
    args = parser.parse_args()
    
    note_id = args.note_id
    print(f"处理笔记 {note_id}...")
    
    # 解析笔记内容
    note_data = parse_note_content(note_id)
    if not note_data:
        print(f"错误: 找不到笔记 {note_id}")
        exit(1)
    
    print(f"  标题: {note_data['title'][:40]}...")
    
    # 获取 token
    access_token = get_tenant_access_token()
    
    # 上传图片
    print("上传图片...")
    files_tokens = upload_images(access_token, note_id)
    
    # 创建/更新记录
    print("更新飞书记录...")
    result = create_or_update_record(access_token, note_id, note_data, files_tokens)
    
    if result.get('code') == 0:
        print("✓ 完成!")
    else:
        print(f"✗ 失败: {result}")
        exit(1)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""使用 AllAPI (gemini-3-pro-image-preview) 生成图片"""
import argparse
import base64
import json
import os
import time
from pathlib import Path

import requests

OUTPUT_DIR = Path(__file__).parent.parent / "output"

# AllAPI 配置
ALLAPI_BASE_URL = "https://allapi.store"
MODEL_NAME = "gemini-3-pro-image-preview"


def generate_image(api_key: str, prompt: str, output_path: str, max_retries: int = 3) -> bool:
    """使用 AllAPI Gemini 模型生成图片"""
    
    endpoint = f"{ALLAPI_BASE_URL}/v1beta/models/{MODEL_NAME}:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["image"],
            "imageConfig": {
                "aspectRatio": "3:4"  # 竖版社交媒体图片
            }
        }
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                
                # 提取 base64 图片数据
                if "candidates" in data and data["candidates"]:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "inline_data" in part:
                                image_data = part["inline_data"]["data"]
                                image_bytes = base64.b64decode(image_data)
                                
                                with open(output_path, 'wb') as f:
                                    f.write(image_bytes)
                                
                                print(f"  ✓ 保存图片: {output_path}")
                                return True
                
                print(f"  ✗ 响应中未找到图片数据")
                print(f"  响应: {json.dumps(data, ensure_ascii=False)[:200]}...")
                
            else:
                error_msg = response.text[:200] if response.text else str(response.status_code)
                print(f"  ✗ 尝试 {attempt + 1}/{max_retries} 失败: HTTP {response.status_code}")
                print(f"     {error_msg}")
                
        except Exception as e:
            print(f"  ✗ 尝试 {attempt + 1}/{max_retries} 失败: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(3)
    
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--note_id', required=True, help='笔记 ID')
    args = parser.parse_args()
    
    # 检查 API Key
    api_key = os.environ.get("ALLAPI_API_KEY")
    if not api_key:
        print("错误: 缺少 ALLAPI_API_KEY 环境变量")
        exit(1)
    
    note_id = args.note_id
    prompts_file = OUTPUT_DIR / f"note{note_id}_prompts" / "prompts.json"
    images_dir = OUTPUT_DIR / f"note{note_id}_images"
    
    if not prompts_file.exists():
        print(f"错误: 找不到提示词文件 {prompts_file}")
        exit(1)
    
    images_dir.mkdir(parents=True, exist_ok=True)
    
    with open(prompts_file, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    
    print(f"开始生成 {len(prompts)} 张图片 (使用 AllAPI {MODEL_NAME})...")
    
    success_count = 0
    for i, prompt_data in enumerate(prompts, 1):
        page = prompt_data.get('page', str(i))
        prompt = prompt_data.get('prompt', '')
        output_path = str(images_dir / f"p{page}.png")
        
        print(f"[{i}/{len(prompts)}] 生成 P{page}...")
        
        if generate_image(api_key, prompt, output_path):
            success_count += 1
        else:
            print(f"  ✗ 跳过 P{page}")
        
        # 添加延迟避免 API 限制
        if i < len(prompts):
            time.sleep(2)
    
    print(f"\n完成: 成功生成 {success_count}/{len(prompts)} 张图片")
    
    # 如果成功生成超过一半，也算成功
    if success_count == 0:
        exit(1)


if __name__ == '__main__':
    main()

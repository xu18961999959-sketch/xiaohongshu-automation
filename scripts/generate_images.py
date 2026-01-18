#!/usr/bin/env python3
"""使用 Replicate API 生成图片"""
import argparse
import json
import os
import requests
import time

try:
    import replicate
except ImportError:
    print("请安装 replicate: pip install replicate")
    exit(1)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')

def generate_image(prompt, output_path, max_retries=3):
    """使用 Replicate Flux 模型生成图片"""
    for attempt in range(max_retries):
        try:
            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": prompt,
                    "aspect_ratio": "3:4",
                    "num_outputs": 1,
                    "output_format": "png"
                }
            )
            
            # 下载图片
            if output and len(output) > 0:
                img_url = output[0]
                response = requests.get(img_url)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"  ✓ 保存图片: {output_path}")
                return True
                
        except Exception as e:
            print(f"  ✗ 尝试 {attempt + 1}/{max_retries} 失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--note_id', required=True, help='笔记 ID')
    args = parser.parse_args()
    
    note_id = args.note_id
    prompts_file = os.path.join(OUTPUT_DIR, f"note{note_id}_prompts", "prompts.json")
    images_dir = os.path.join(OUTPUT_DIR, f"note{note_id}_images")
    
    if not os.path.exists(prompts_file):
        print(f"错误: 找不到提示词文件 {prompts_file}")
        exit(1)
    
    os.makedirs(images_dir, exist_ok=True)
    
    with open(prompts_file, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    
    print(f"开始生成 {len(prompts)} 张图片...")
    
    success_count = 0
    for i, prompt_data in enumerate(prompts, 1):
        page = prompt_data.get('page', str(i))
        prompt = prompt_data.get('prompt', '')
        output_path = os.path.join(images_dir, f"p{page}.png")
        
        print(f"[{i}/{len(prompts)}] 生成 P{page}...")
        
        if generate_image(prompt, output_path):
            success_count += 1
        else:
            print(f"  ✗ 跳过 P{page}")
    
    print(f"\n完成: 成功生成 {success_count}/{len(prompts)} 张图片")
    
    if success_count < len(prompts):
        exit(1)

if __name__ == '__main__':
    main()

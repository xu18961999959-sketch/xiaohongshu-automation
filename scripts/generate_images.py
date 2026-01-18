#!/usr/bin/env python3
"""使用 Gemini API (Imagen) 生成图片"""
import argparse
import json
import os
import time
from pathlib import Path

try:
    import google.generativeai as genai
    from google.generativeai import types
except ImportError:
    print("请安装 google-generativeai: pip install google-generativeai")
    exit(1)

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def generate_image(prompt: str, output_path: str, max_retries: int = 3) -> bool:
    """使用 Gemini Imagen 模型生成图片"""
    
    # 配置 API
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("  ✗ 缺少 GOOGLE_API_KEY 环境变量")
        return False
    
    genai.configure(api_key=api_key)
    
    for attempt in range(max_retries):
        try:
            # 使用 Imagen 3 模型生成图片
            imagen = genai.ImageGenerationModel("imagen-3.0-generate-002")
            
            result = imagen.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="3:4",  # 竖版
                safety_filter_level="block_only_high",
                person_generation="allow_adult",
            )
            
            if result.images:
                # 保存第一张图片
                image = result.images[0]
                image._pil_image.save(output_path)
                print(f"  ✓ 保存图片: {output_path}")
                return True
            else:
                print(f"  ✗ 未生成图片")
                
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
    prompts_file = OUTPUT_DIR / f"note{note_id}_prompts" / "prompts.json"
    images_dir = OUTPUT_DIR / f"note{note_id}_images"
    
    if not prompts_file.exists():
        print(f"错误: 找不到提示词文件 {prompts_file}")
        exit(1)
    
    images_dir.mkdir(parents=True, exist_ok=True)
    
    with open(prompts_file, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    
    print(f"开始生成 {len(prompts)} 张图片...")
    
    success_count = 0
    for i, prompt_data in enumerate(prompts, 1):
        page = prompt_data.get('page', str(i))
        prompt = prompt_data.get('prompt', '')
        output_path = str(images_dir / f"p{page}.png")
        
        print(f"[{i}/{len(prompts)}] 生成 P{page}...")
        
        if generate_image(prompt, output_path):
            success_count += 1
        else:
            print(f"  ✗ 跳过 P{page}")
        
        # 添加延迟避免 API 限制
        if i < len(prompts):
            time.sleep(1)
    
    print(f"\n完成: 成功生成 {success_count}/{len(prompts)} 张图片")
    
    if success_count < len(prompts):
        exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Font Preview Script - Shows how fonts look with exact captionGen.py settings
This mimics the exact caption creation process without needing video files.
"""

import os
import sys
from PIL import Image, ImageFont, ImageDraw
import argparse

def create_caption_preview(font_path, text="Sample Caption Text", font_size=110, border_size=8):
    """
    Create a caption preview using the exact same settings as captionGen.py
    """
    try:
        # Load font
        font = ImageFont.truetype(font_path, font_size)
        print(f"✓ Loaded font: {os.path.basename(font_path)}")
        
        # Calculate text dimensions (same as captionGen.py)
        try:
            text_bbox = font.getbbox(text)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
        except AttributeError:
            # Fallback for older PIL versions
            text_width, text_height = font.getsize(text)
        
        # Calculate image dimensions (same as captionGen.py)
        caption_height_base = 120  # Same as in captionGen.py
        increased_size = (text_width + border_size * 2, caption_height_base + border_size * 2 + font_size // 2)
        
        print(f"Text dimensions: {text_width:.1f} x {text_height:.1f}")
        print(f"Image dimensions: {increased_size[0]} x {increased_size[1]}")
        
        # Create image with transparent background (same as captionGen.py)
        img = Image.new('RGBA', increased_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate text position (same as captionGen.py)
        position = ((increased_size[0] - text_width) // 2, (increased_size[1] - text_height) // 2)
        
        # Draw border (same as captionGen.py)
        for x_offset in range(-border_size, border_size + 1):
            for y_offset in range(-border_size, border_size + 1):
                draw.text((position[0] + x_offset, position[1] + y_offset), text, font=font, fill=(0, 0, 0, 255))
        
        # Draw main text (same as captionGen.py)
        draw.text(position, text, font=font, fill=(255, 255, 255, 255))
        
        # Save the preview
        output_filename = f"caption_preview_{os.path.splitext(os.path.basename(font_path))[0]}.png"
        img.save(output_filename)
        print(f"✓ Saved preview: {output_filename}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def create_multiple_samples(font_path, font_size=110):
    """
    Create multiple caption samples with different text lengths
    """
    sample_texts = [
        "an gero ed",
        "incompatible",
        "Hello World",
        "This is a test",
        "SUPERCALIFRAGILISTIC",
        "1234567890",
        "!@#$%^&*()",
    ]
    
    print(f"\nCreating multiple caption samples...")
    
    for i, text in enumerate(sample_texts):
        output_filename = f"caption_sample_{i+1}_{os.path.splitext(os.path.basename(font_path))[0]}.png"
        
        try:
            # Load font
            font = ImageFont.truetype(font_path, font_size)
            
            # Calculate dimensions
            try:
                text_bbox = font.getbbox(text)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
            except AttributeError:
                text_width, text_height = font.getsize(text)
            
            # Same settings as captionGen.py
            caption_height_base = 120
            border_size = 8
            increased_size = (text_width + border_size * 2, caption_height_base + border_size * 2 + font_size // 2)
            
            # Create image
            img = Image.new('RGBA', increased_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Position text
            position = ((increased_size[0] - text_width) // 2, (increased_size[1] - text_height) // 2)
            
            # Draw border and text
            for x_offset in range(-border_size, border_size + 1):
                for y_offset in range(-border_size, border_size + 1):
                    draw.text((position[0] + x_offset, position[1] + y_offset), text, font=font, fill=(0, 0, 0, 255))
            
            draw.text(position, text, font=font, fill=(255, 255, 255, 255))
            
            # Save
            img.save(output_filename)
            print(f"  ✓ {text:<25} → {output_filename}")
            
        except Exception as e:
            print(f"  ✗ {text:<25} → Error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Preview fonts with exact captionGen.py settings')
    parser.add_argument('font', type=str, help='Font file path to test')
    parser.add_argument('--text', type=str, default='Sample Caption Text', help='Custom text to display')
    parser.add_argument('--size', type=int, default=110, help='Font size (default: 110)')
    parser.add_argument('--samples', action='store_true', help='Create multiple sample captions')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.font):
        print(f"Font file not found: {args.font}")
        return
    
    print("Font Preview with captionGen.py Settings")
    print("=" * 50)
    print(f"Font: {args.font}")
    print(f"Font size: {args.size}")
    print(f"Text: {args.text}")
    print(f"Border size: 8 (reduced from 15)")
    print(f"Background: Transparent")
    print(f"Text color: White")
    print(f"Border color: Black")
    print()
    
    # Create single preview
    create_caption_preview(args.font, args.text, args.size)
    
    # Create multiple samples if requested
    if args.samples:
        create_multiple_samples(args.font, args.size)
    
    print(f"\nDone! Check the generated PNG files to see how your font looks.")
    print(f"These use the exact same settings as captionGen.py will use.")

if __name__ == "__main__":
    main()

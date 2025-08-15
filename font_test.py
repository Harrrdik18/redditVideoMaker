#!/usr/bin/env python3
"""
Font Testing Script for Caption Generation
This script tests different fonts and shows how they render without needing video files.
"""

import os
import sys
from PIL import Image, ImageFont, ImageDraw
import argparse

def find_available_fonts():
    """Find available fonts on the system."""
    font_paths = []
    
    # Common font locations
    common_paths = [
        "C:/Windows/Fonts",  # Windows
        "/System/Library/Fonts",  # macOS
        "/Library/Fonts",  # macOS user fonts
        "/usr/share/fonts",  # Linux
        "/usr/local/share/fonts",  # Linux
        "~/.fonts",  # User fonts
    ]
    
    for path in common_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            for file in os.listdir(expanded_path):
                if file.lower().endswith(('.ttf', '.otf', '.ttc')):
                    font_paths.append(os.path.join(expanded_path, file))
    
    return font_paths

def test_font_rendering(font_path, font_size=110, sample_texts=None):
    """Test how a font renders sample text."""
    if sample_texts is None:
        sample_texts = [
            "Hello World",
            "an gero ed",
            "incompatible",
            "This is a test",
            "SUPERCALIFRAGILISTIC",
            "1234567890",
            "!@#$%^&*()",
            "The quick brown fox jumps over the lazy dog",
        ]
    
    try:
        font = ImageFont.truetype(font_path, font_size)
        print(f"✓ Successfully loaded: {os.path.basename(font_path)}")
        
        # Create a test image
        max_width = 0
        total_height = 0
        
        # First pass: measure dimensions
        for text in sample_texts:
            try:
                bbox = font.getbbox(text)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
            except AttributeError:
                # Fallback for older PIL versions
                width, height = font.getsize(text)
            
            max_width = max(max_width, width)
            total_height += height + 20  # Add spacing between lines
        
        # Create image
        img_width = max_width + 40  # Add padding
        img_height = total_height + 40
        img = Image.new('RGB', (img_width, img_height), color='black')
        draw = ImageDraw.Draw(img)
        
        # Second pass: draw text
        y_offset = 20
        for text in sample_texts:
            try:
                bbox = font.getbbox(text)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
            except AttributeError:
                width, height = font.getsize(text)
            
            # Center text horizontally
            x = (img_width - width) // 2
            draw.text((x, y_offset), text, font=font, fill='white')
            y_offset += height + 20
        
        # Save the test image
        output_filename = f"font_test_{os.path.splitext(os.path.basename(font_path))[0]}.png"
        img.save(output_filename)
        print(f"  → Saved test image: {output_filename}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to load {os.path.basename(font_path)}: {e}")
        return False

def test_font_widths(font_path, font_size=110):
    """Test font width measurements for different text."""
    try:
        font = ImageFont.truetype(font_path, font_size)
        print(f"\nFont width measurements for: {os.path.basename(font_path)}")
        print(f"{'='*60}")
        
        test_cases = [
            "an gero ed",
            "incompatible", 
            "an gero ed incompatible",
            "hello world",
            "this is a test",
            "supercalifragilisticexpialidocious",
            "a b c d e f g",
        ]
        
        # Simulate video width (1920 is common HD width)
        video_width = 1920
        max_width = video_width * 0.9  # 90% of video width
        
        for text in test_cases:
            try:
                bbox = font.getbbox(text)
                width = bbox[2] - bbox[0]
            except AttributeError:
                width = font.getsize(text)[0]
            
            fits = "✓" if width <= max_width else "✗"
            ratio = (width / video_width) * 100
            
            print(f"{fits} '{text:<35}' | Width: {width:>6.1f} | {ratio:>5.1f}% of screen")
        
        print(f"\nScreen width: {video_width}px")
        print(f"Max caption width: {max_width:.1f}px (90% of screen)")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to test font widths: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test fonts for caption generation')
    parser.add_argument('--font', type=str, help='Specific font file to test')
    parser.add_argument('--size', type=int, default=110, help='Font size to test (default: 110)')
    parser.add_argument('--list', action='store_true', help='List available fonts')
    parser.add_argument('--test-all', action='store_true', help='Test all available fonts')
    parser.add_argument('--width-test', action='store_true', help='Test font width measurements')
    parser.add_argument('--custom-text', type=str, help='Custom text to test')
    
    args = parser.parse_args()
    
    if args.list:
        print("Available fonts:")
        fonts = find_available_fonts()
        for font in fonts[:20]:  # Show first 20
            print(f"  {font}")
        if len(fonts) > 20:
            print(f"  ... and {len(fonts) - 20} more fonts")
        return
    
    if args.font:
        # Test specific font
        if not os.path.exists(args.font):
            print(f"Font file not found: {args.font}")
            return
        
        print(f"Testing font: {args.font}")
        print(f"Font size: {args.size}")
        
        sample_texts = [args.custom_text] if args.custom_text else None
        test_font_rendering(args.font, args.size, sample_texts)
        
        if args.width_test:
            test_font_widths(args.font, args.size)
    
    elif args.test_all:
        # Test all available fonts
        fonts = find_available_fonts()
        print(f"Found {len(fonts)} fonts. Testing...")
        
        successful = 0
        for font in fonts:
            if test_font_rendering(font, args.size):
                successful += 1
        
        print(f"\nTested {len(fonts)} fonts, {successful} successful")
    
    else:
        # Interactive mode
        print("Font Testing Script")
        print("=" * 50)
        
        fonts = find_available_fonts()
        print(f"Found {len(fonts)} fonts on your system")
        
        if fonts:
            print("\nTo test a specific font:")
            print(f"  python font_test.py --font \"{fonts[0]}\"")
            print(f"  python font_test.py --font \"{fonts[0]}\" --width-test")
            
            print("\nTo test all fonts:")
            print("  python font_test.py --test-all")
            
            print("\nTo list all fonts:")
            print("  python font_test.py --list")
            
            print("\nTo test with custom text:")
            print("  python font_test.py --font \"font.ttf\" --custom-text \"Your text here\"")
        else:
            print("No fonts found. Make sure you have fonts installed on your system.")

if __name__ == "__main__":
    main()

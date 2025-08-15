import os
import sys
import json
import wave
import urllib.request
import zipfile
import logging
import subprocess
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from vosk import Model, KaldiRecognizer, SetLogLevel
import argparse


# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Vosk model download function
# TODO small model can be used "vosk-model-small-en-us-0.15"
def download_vosk_model(model_name="vosk-model-en-us-0.22"):
    model_url = f"https://alphacephei.com/vosk/models/{model_name}.zip"
    model_path = os.path.join(os.path.dirname(__file__), model_name)
    
    if not os.path.exists(model_path):
        logging.info(f"Downloading Vosk model {model_name}...")
        zip_path, _ = urllib.request.urlretrieve(model_url)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(__file__))
        os.remove(zip_path)
        logging.info("Model downloaded and extracted.")
    return model_path

def extract_audio(video_path, audio_path):
    if os.path.exists(audio_path):
        logging.info(f"File '{audio_path}' already exists. Overwriting...")
        os.remove(audio_path)
	
    command = [
        "ffmpeg",
        "-i", video_path,
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", "16000",
        audio_path
    ]
    subprocess.run(command, check=True)
    logging.info(f"Audio extracted to {audio_path}")

def transcribe_audio(audio_path, model_path):
    SetLogLevel(0)
    wf = wave.open(audio_path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        logging.error("Audio file must be WAV format mono PCM.")
        return []

    model = Model(model_path)
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            part_result = json.loads(rec.Result())
            results.append(part_result)
    part_result = json.loads(rec.FinalResult())
    results.append(part_result)

    words = []
    for r in results:
        if 'result' in r:
            words.extend(r['result'])
    
    logging.info(f"Transcribed {len(words)} words")
    return words


def group_words_into_captions(word_timings, video_width, font_size, font_path, max_duration_per_caption=1.5, pause_threshold=0.3, max_text_width_ratio=0.9):
    """
    Groups individual word timings into captions with maximum 2 words per caption,
    ensuring captions fit within the screen width while maintaining natural timing.
    """
    # Load font to measure text width
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        logging.warning(f"Could not load font {font_path}, using default font. Error: {e}")
        font = ImageFont.load_default()
    
    # Calculate maximum allowed text width (90% of video width by default)
    max_text_width = video_width * max_text_width_ratio
    logging.info(f"Video width: {video_width}, Max text width: {max_text_width:.1f} (ratio: {max_text_width_ratio})")
    
    grouped_captions = []
    i = 0
    
    while i < len(word_timings):
        current_caption_words = []
        current_caption_start = word_timings[i]['start']
        current_caption_end = word_timings[i]['end']
        
        # Always start with the first word
        current_caption_words.append(word_timings[i])
        
        # Try to add one more word (max 2 words total)
        if i + 1 < len(word_timings):
            next_word = word_timings[i + 1]
            
            # Check for significant pause (natural break)
            if next_word['start'] - current_caption_end > pause_threshold:
                logging.debug(f"Breaking at word '{next_word['word']}' due to pause ({next_word['start'] - current_caption_end:.2f}s)")
            # Check duration limit
            elif (next_word['end'] - current_caption_start) > max_duration_per_caption:
                logging.debug(f"Breaking at word '{next_word['word']}' due to duration ({(next_word['end'] - current_caption_start):.2f}s)")
            else:
                # Create potential caption text with 2 words
                potential_caption = " ".join([w['word'] for w in current_caption_words] + [next_word['word']])
                
                # Measure actual text width
                try:
                    text_bbox = font.getbbox(potential_caption)
                    text_width = text_bbox[2] - text_bbox[0]
                except AttributeError:
                    # Fallback for older PIL versions
                    text_width = font.getsize(potential_caption)[0]
                
                # Check if text fits on screen
                if text_width <= max_text_width:
                    # Text fits, so add this word
                    current_caption_words.append(next_word)
                    current_caption_end = next_word['end']
                    logging.debug(f"Added word '{next_word['word']}' - combined width: {text_width:.1f}")
                else:
                    logging.debug(f"Breaking at word '{next_word['word']}' - text width {text_width:.1f} exceeds max {max_text_width:.1f}")
        
        # Create the caption from the grouped words
        combined_text = " ".join([w['word'] for w in current_caption_words])
        
        # Log the final caption details
        try:
            final_bbox = font.getbbox(combined_text)
            final_width = final_bbox[2] - final_bbox[0]
        except AttributeError:
            final_width = font.getsize(combined_text)[0]
        
        logging.debug(f"Caption {len(grouped_captions)+1}: '{combined_text}' (width: {final_width:.1f}, duration: {current_caption_end - current_caption_start:.2f}s)")
        
        grouped_captions.append({
            'word': combined_text,
            'start': current_caption_start,
            'end': current_caption_end
        })
        
        # Move index past the words just grouped
        i += len(current_caption_words)
    
    logging.info(f"Grouped {len(word_timings)} words into {len(grouped_captions)} captions (max 2 words per caption).")
    return grouped_captions

def create_text_image(text, size, font_size, color, font_path, bg_color=(0, 0, 0, 0), border_size=8):
    # Increase the size of the image to accommodate the border
    increased_size = (size[0] + border_size * 2, size[1] + border_size * 2 + font_size // 2)
    img = Image.new('RGBA', increased_size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Load the main font
    font = ImageFont.truetype(font_path, font_size)
    
    # Calculate text position
    text_bbox = font.getbbox(text)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((increased_size[0] - text_width) // 2, (increased_size[1] - text_height) // 2)

    # Draw border
    for x_offset in range(-border_size, border_size + 1):
        for y_offset in range(-border_size, border_size + 1):
            draw.text((position[0] + x_offset, position[1] + y_offset), text, font=font, fill=(0, 0, 0, 255))  # Black border

    # Draw main text
    draw.text(position, text, font=font, fill=color)

    return np.array(img)




def create_caption_clips(word_timings, video_width, video_height, font_path):
    caption_clips = []
    font_size = 110  # Increased font size
    caption_height_base = 120 # This is the 'size[1]' passed to create_text_image
    border_size = 8 # From create_text_image
    font_size = 110 # From create_caption_clips
    
    # Calculate the actual rendered height of the caption image
    caption_rendered_height = caption_height_base + (border_size * 2) + (font_size // 2)

    for word in word_timings:
        img_array = create_text_image(word['word'], (video_width, caption_height_base), font_size, (255, 255, 255, 255), font_path)
        clip = ImageClip(img_array, duration=word['end'] - word['start'])
        
        # Calculate y-position to place captions in the vertical center of the screen
        # MoviePy's set_position uses the top-left corner of the clip for positioning.
        y_position = (video_height / 2) - (caption_rendered_height / 2)
        clip = clip.set_position(('center', y_position)).set_start(word['start'])
        
        caption_clips.append(clip)
    
    logging.info(f"Created {len(caption_clips)} caption clips")
    return caption_clips



def main(input_video_path, output_video_path, font_path, comments_start_time=None, output_duration=None, max_text_width_ratio=0.9):
    # Download Vosk model if not present
    model_path = download_vosk_model()

    # Extract audio from video
    audio_path = "temp_audio.wav"
    extract_audio(input_video_path, audio_path)
    
    # Transcribe audio
    word_timings = transcribe_audio(audio_path, model_path)
    
    if not word_timings:
        logging.error("No words were transcribed. Check the audio quality and format.")
        return

    # Filter words to only include those after comments_start_time
    if comments_start_time is not None:
        word_timings = [w for w in word_timings if w['start'] >= comments_start_time]
        logging.info(f"Filtered words to start from {comments_start_time}s, {len(word_timings)} words remain.")

    # Print first 10 transcribed words for debugging
    logging.info(f"First 10 transcribed words: {word_timings[:10]}")

    # Group words into captions dynamically
    video = VideoFileClip(input_video_path) # Load video early to get dimensions
    
    # Group words into captions dynamically
    # Pass video dimensions and font info for dynamic text fitting
    grouped_word_timings = group_words_into_captions(word_timings, video.w, 110, font_path, max_text_width_ratio=max_text_width_ratio) # 110 is font_size from create_caption_clips

    # Create caption clips
    video = VideoFileClip(input_video_path)
    caption_clips = create_caption_clips(grouped_word_timings, video.w, video.h, font_path)
    
    # Overlay captions on video
    final_video = CompositeVideoClip([video] + caption_clips)

    if output_duration is not None:
        final_video = final_video.set_duration(output_duration)
        logging.info(f"Output video duration set to {output_duration} seconds.")

    # Write output video
    final_video.write_videofile(output_video_path,)
    
    # Clean up temporary files
    os.remove(audio_path)
    logging.info("Video processing completed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add captions to video using Vosk and MoviePy.')
    parser.add_argument('input_video', type=str, help='Path to the input video file')
    parser.add_argument('--font', type=str, default='/home/user/RedditVideoMakerBot-master/fonts/Rubik-Black.ttf', help='Path to the font file')
    parser.add_argument('--comments_start', type=float, default=None, help='Time (in seconds) when comments start')
    parser.add_argument('--output_duration', type=float, default=None, help='Desired duration of the output video in seconds')
    parser.add_argument('--max_text_width_ratio', type=float, default=0.9, help='Maximum text width as ratio of video width (0.0-1.0)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging to see caption grouping decisions')
    args = parser.parse_args()

    # Set logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.info("Debug logging enabled - you'll see detailed caption grouping information")

    input_video = args.input_video
    output_video = os.path.splitext(input_video)[0] + "_out.mp4"
    font_path = args.font
    main(input_video, output_video, font_path, comments_start_time=args.comments_start, output_duration=args.output_duration, max_text_width_ratio=args.max_text_width_ratio)




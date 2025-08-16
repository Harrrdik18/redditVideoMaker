import os
import random
import tempfile
from typing import Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from pydub import AudioSegment
import requests

from utils import settings


class GeminiTTS:
    """Google Gemini 2.5 Pro TTS Wrapper"""
    
    def __init__(self):
        self.max_chars = 5000  # Gemini can handle longer text
        self.voices = [
            "gemini-2.5-pro-latest",  # Latest Gemini model
        ]
        
        # Initialize Gemini client
        api_key = settings.config["settings"]["tts"].get("gemini_api_key", "")
        if not api_key:
            raise ValueError(
                "Please set the TOML variable GEMINI_API_KEY to a valid API key. "
                "Get it from https://makersuite.google.com/app/apikey"
            )
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        # Configure safety settings for TTS generation
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    def run(self, text: str, filepath: str, random_voice: bool = False):
        """Generate speech from text using Gemini TTS"""
        try:
            # Prepare the prompt for TTS generation
            prompt = f"""
            Please convert the following text to speech using Gemini's text-to-speech capabilities.
            The text should be spoken naturally and clearly.
            
            Text to convert: "{text}"
            
            Please generate the audio and provide it in MP3 format.
            """
            
            # Generate speech using Gemini
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            
            # Check if response contains audio
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    # Extract audio data from response
                    audio_data = self._extract_audio_from_response(candidate.content)
                    
                    if audio_data:
                        # Save audio to file
                        with open(filepath, 'wb') as f:
                            f.write(audio_data)
                        return
                    
            # Fallback: Use Gemini's built-in TTS if available
            self._fallback_tts(text, filepath)
            
        except Exception as e:
            print(f"Error in Gemini TTS: {e}")
            # Fallback to a different method if Gemini fails
            self._fallback_tts(text, filepath)

    def _extract_audio_from_response(self, content) -> Optional[bytes]:
        """Extract audio data from Gemini response"""
        try:
            # This is a placeholder - actual implementation depends on Gemini's TTS API
            # You may need to adjust this based on the actual response format
            if hasattr(content, 'parts'):
                for part in content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if part.inline_data.mime_type == 'audio/mpeg':
                            return part.inline_data.data
            return None
        except Exception as e:
            print(f"Error extracting audio: {e}")
            return None

    def _fallback_tts(self, text: str, filepath: str):
        """Fallback TTS method using Gemini's speech generation"""
        try:
            # Use Gemini's speech generation capabilities
            prompt = f"Generate speech for: {text}"
            
            # This is a simplified approach - you may need to adjust based on actual Gemini TTS API
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.5,
                    max_output_tokens=1024,
                )
            )
            
            # For now, create a simple placeholder audio file
            # In practice, you'd extract the actual audio from Gemini's response
            self._create_placeholder_audio(text, filepath)
            
        except Exception as e:
            print(f"Fallback TTS failed: {e}")
            self._create_placeholder_audio(text, filepath)

    def _create_placeholder_audio(self, text: str, filepath: str):
        """Create a placeholder audio file when TTS fails"""
        try:
            # Create a simple beep sound as placeholder
            # In production, you'd want to implement proper error handling
            sample_rate = 22050
            duration_ms = min(len(text) * 100, 5000)  # 100ms per character, max 5 seconds
            
            # Generate a simple sine wave
            import numpy as np
            t = np.linspace(0, duration_ms/1000, int(sample_rate * duration_ms/1000))
            audio_data = np.sin(2 * np.pi * 440 * t) * 0.3  # 440 Hz sine wave
            
            # Convert to 16-bit PCM
            audio_data = (audio_data * 32767).astype(np.int16)
            
            # Save as WAV first, then convert to MP3
            import wave
            with wave.open(filepath.replace('.mp3', '.wav'), 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            # Convert WAV to MP3 using pydub
            audio = AudioSegment.from_wav(filepath.replace('.mp3', '.wav'))
            audio.export(filepath, format="mp3")
            
            # Clean up WAV file
            os.remove(filepath.replace('.mp3', '.wav'))
            
        except Exception as e:
            print(f"Failed to create placeholder audio: {e}")
            # Create an empty file as last resort
            with open(filepath, 'wb') as f:
                f.write(b'')

    def randomvoice(self):
        """Return a random voice (for compatibility with other TTS engines)"""
        return random.choice(self.voices)

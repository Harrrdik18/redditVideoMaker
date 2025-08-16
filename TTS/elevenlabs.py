import random

from elevenlabs import save
from elevenlabs.client import ElevenLabs

from utils import settings


class elevenlabs:
    def __init__(self):
        self.max_chars = 2500
        self.client: ElevenLabs = None
        self.current_voice = None  # Cache the current voice for this content piece

    def run(self, text, filepath, random_voice: bool = False):
        if self.client is None:
            self.initialize()
        
        try:
            if random_voice:
                # If we don't have a cached voice yet, get a new random one
                if self.current_voice is None:
                    self.current_voice = self.randomvoice()
                    print(f"Selected new random voice: {self.current_voice}")
                voice = self.current_voice
            else:
                # Use the specified voice from config
                voice = str(settings.config["settings"]["tts"]["elevenlabs_voice_name"]).capitalize()
                # Reset cached voice when not using random
                self.current_voice = None

            print(f"Using ElevenLabs voice: {voice}")
            
            audio = self.client.generate(text=text, voice=voice, model="eleven_multilingual_v1")
            save(audio=audio, filename=filepath)
            
        except Exception as e:
            print(f"Error in ElevenLabs TTS: {e}")
            print("Falling back to default voice 'Bella'")
            
            # Try with default voice as fallback
            try:
                audio = self.client.generate(text=text, voice="Bella", model="eleven_multilingual_v1")
                save(audio=audio, filename=filepath)
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
                raise fallback_error

    def initialize(self):
        api_key = settings.config["settings"]["tts"]["elevenlabs_api_key"]
        
        if not api_key or api_key == "REDACTED" or api_key == "":
            raise ValueError(
                "You didn't set an Elevenlabs API key! Please set the config variable elevenlabs_api_key to a valid API key in your config.toml file."
            )

        try:
            self.client = ElevenLabs(api_key=api_key)
            print("ElevenLabs client initialized successfully")
        except Exception as e:
            print(f"Error initializing ElevenLabs client: {e}")
            raise ValueError(f"Failed to initialize ElevenLabs client: {e}")

    def randomvoice(self):
        if self.client is None:
            self.initialize()
        
        try:
            # Get all voices
            voices_response = self.client.voices.get_all()
            
            # Check if voices exist and have the expected structure
            if not hasattr(voices_response, 'voices') or not voices_response.voices:
                print("Warning: No voices found from ElevenLabs API, using default voice")
                return "Bella"
            
            # Select a random voice
            voice_obj = random.choice(voices_response.voices)
            
            # Try different possible attribute names for voice name
            if hasattr(voice_obj, 'name'):
                return voice_obj.name
            elif hasattr(voice_obj, 'voice_name'):
                return voice_obj.voice_name
            elif hasattr(voice_obj, 'label'):
                return voice_obj.label
            else:
                # Fallback: try to get any string attribute that might be the name
                for attr in dir(voice_obj):
                    if not attr.startswith('_') and isinstance(getattr(voice_obj, attr), str):
                        return getattr(voice_obj, attr)
                            # Last resort: return a default voice name
            return "Bella"
                
        except Exception as e:
            print(f"Warning: Error getting random voice from ElevenLabs: {e}")
            print("Using default voice 'Bella'")
            return "Bella"
    
    def reset_voice_cache(self):
        """Reset the cached voice so the next random voice call will get a new voice"""
        self.current_voice = None
        print("Voice cache reset - next random voice will be different")

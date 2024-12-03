import whisper
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import warnings

#requires openai-whisper and ffmpeg
# Ignore warnings
warnings.filterwarnings("ignore")

# Function to record audio
def record_audio(duration, filename="temp_audio.wav", fs=44100):
    print("Recording... Please speak now.")
    # Record audio for the specified duration
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
    sd.wait()  # Wait until recording is finished
    write(filename, fs, audio)  # Save as WAV file
    print("Recording finished. Audio saved as", filename)

# Main script
if __name__ == "__main__":
    # Specify recording duration
    duration = 10  # Duration in seconds
    
    # Record audio
    record_audio(duration=duration)
    
    # Load Whisper model
    model = whisper.load_model("base")
    
    # Transcribe audio
    print("Transcribing audio...")
    result = model.transcribe("temp_audio.wav")  # Use task="translate" if translation is needed
    
    # Display the transcription
    transcripted_query = result['text']
    print("Transcription:", transcripted_query)

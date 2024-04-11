import os
import pyaudio
import wave
import openai
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import keyboard

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set the OpenAI API key
openai.api_key = OPENAI_API_KEY

def transcribe_audio_from_mic():
	# Set up audio recording parameters
	FORMAT = pyaudio.paInt16
	CHANNELS = 1
	RATE = 16000
	CHUNK = 1024

	# Initialize PyAudio and start recording
	audio = pyaudio.PyAudio()
	stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

	print("Recording... Press Enter to stop.")

	frames = []
	while True:
		data = stream.read(CHUNK)
		frames.append(data)
		if keyboard.is_pressed('enter'):  # Stop recording when Enter key is pressed
			print("Stop recording.")
			break

	# Stop and close the stream and PyAudio
	stream.stop_stream()
	stream.close()
	audio.terminate()

	# Save the recorded frames as a WAV file
	wav_file_path = Path(__file__).parent / "temp_recording.wav"
	with wave.open(str(wav_file_path), 'wb') as wf:
		wf.setnchannels(CHANNELS)
		wf.setsampwidth(audio.get_sample_size(FORMAT))
		wf.setframerate(RATE)
		wf.writeframes(b''.join(frames))

	# Transcribe the audio using OpenAI's Whisper model
	with open(wav_file_path, 'rb') as audio_file:
		transcription_response = openai.audio.transcriptions.create(
			model="whisper-1",
			file=audio_file,
			response_format="text"
		)

	transcription = transcription_response
	print("Transcription response:", transcription)

	return transcription

def get_chatgpt_response(prompt):
	"""Gets a response from ChatGPT"""
	response = openai.chat.completions.create(
		model="gpt-4",
		messages=[
			{"role": "system", "content": "You are a helpful assistant."},
			{"role": "user", "content": prompt},
		],
	)
	return response.choices[0].message.content

def speak_chatgpt_response(chatgpt_response):
	"""Speaks the ChatGPT response using OpenAI's text-to-speech"""
	speech_file_path = Path(__file__).parent / "speech.mp3"
	response = openai.audio.speech.create(
		model="tts-1",
		voice="alloy",
		input=chatgpt_response,
	)
	with open(speech_file_path, "wb") as f:
		f.write(response.content)

	# Play the audio file using ffplay directly in the terminal
	player_process = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", str(speech_file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

	# Check if space is pressed to stop playback, otherwise wait for the audio to finish
	while player_process.poll() is None:
		if keyboard.is_pressed('space'):
			player_process.terminate()
			break

def main_loop():
	while True:
		transcription = transcribe_audio_from_mic()
		if transcription.strip().lower() in ["exit", "exit.", "Exit", "Exit."]:
			print("Exiting...")
			break
		elif transcription:
			chatgpt_response = get_chatgpt_response(transcription)
			print("ChatGPT:", chatgpt_response)
			speak_chatgpt_response(chatgpt_response)

# Main program loop
if __name__ == "__main__":
	main_loop()

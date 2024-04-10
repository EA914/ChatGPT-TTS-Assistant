import os
from pathlib import Path
import openai
import subprocess
import speech_recognition as sr
from dotenv import load_dotenv
import keyboard	

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set the OpenAI API key
openai.api_key = OPENAI_API_KEY

# Initialize the speech recognition engine
recognizer = sr.Recognizer()

def transcribe_audio_from_mic():
	with sr.Microphone() as source:
		print("Speak something:")
		audio = recognizer.listen(source)

	try:
		text = recognizer.recognize_google(audio)
		print("You said:", text)
		return text
	except sr.UnknownValueError:
		print("Could not understand audio")
		return ""
	except sr.RequestError as e:
		print(f"Error from recognition service: {e}")
		return ""

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
	subprocess.Popen(["ffplay", "-nodisp", "-autoexit", str(speech_file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def keyboard_interrupt():
	keyboard.wait('space')
	# Suppress the output of the taskkill command
	with open(os.devnull, 'w') as devnull:
		subprocess.run(["taskkill", "/IM", "ffplay.exe", "/F"], stdout=devnull, stderr=devnull)

# Main program loop
if __name__ == "__main__":
	while True:
		prompt = transcribe_audio_from_mic()
		if prompt.lower() == "exit":
			break
		elif prompt:
			chatgpt_response = get_chatgpt_response(prompt)
			print("ChatGPT:", chatgpt_response)
			speak_chatgpt_response(chatgpt_response)
			keyboard_interrupt()

from google import genai
from gtts import gTTS
import os

def access_file(filename):
    """Reads the content of a file if it exists, otherwise returns an empty string."""
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return file.read()
    return ""  # Return empty string if file doesn't exist
rules = access_file("rules.txt")

print("Rules LLM\n",rules)

client = genai.Client(api_key="AIzaSyAe6UbUZN1msgYnx7J9BtlrJsW8vWogFoY")
while True:
    print("Masukkan Input")
    x = input()
    if "stop" in x.lower():
        print("end program")
        break
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite", contents=rules + x
    )
    mytext = response.text
    language = 'en'
    myobj = gTTS(text=mytext, lang=language, slow=False)
    myobj.save("welcome.mp3")
    os.system("start welcome.mp3")
    print(response.text)
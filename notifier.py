import requests
import json
from model import DatabaseManager, User, Class, ClassRegistration, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from google.cloud import texttospeech
import requests
from requests.auth import HTTPBasicAuth

database_manager = DatabaseManager()


def generate_random_file_name():
    import random
    import string

    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(10))


def speach_text(text):
    # Use the Google Text-to-Speech API to convert text to speech
    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("ja-JP") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP", name="ja-JP-Neural2-B"
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    # The response's audio_content is binary.
    file_name = generate_random_file_name() + ".mp3"
    with open(file_name, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print("Audio content written to file " + file_name)

    # Upload the file to the cloud
    from google.cloud import storage

    storage_client = storage.Client()
    bucket = storage_client.bucket("rakutanprev")
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_name)
    url = blob.public_url
    print(f"File uploaded to {url}")
    # Convert the url from https to http
    url = url.replace("https", "http")
    return url


def get_upcoming_classes(semester, period):
    result = database_manager.get_class_by_semester_and_period(semester, period)
    print(result)
    return result


def get_phone_number(user_id):
    user = database_manager.get_account_by_id(user_id)
    # Returns User class&object, so we need to extract the phone number
    return user.phone_number


def generate_voice_message(class_name, absences, remaining_min):
    message = f"あと{remaining_min}分で{class_name}が始まります。現在の欠席数は{absences}です。"
    tosend = "こんにちは! " + message * 3
    return tosend


def call_number(phonenumber, url):
    username = "o7a0cfpSNZmOWC1Dzj2qV9E4sUdx8MKT"
    password = "p56fvwxb84iam9urskh2go7et01cjd3z"

    api_url = "https://api.xoxzo.com/voice/simple/playbacks/"

    payload = {
        "caller": "+817089770489",
        "recipient": phonenumber,
        "recording_url": url,
    }

    # Make the POST request
    response = requests.post(
        api_url, data=payload, auth=HTTPBasicAuth(username, password)
    )

    # Check and return the response
    if response.status_code == 200 or response.status_code == 201:
        return True
    else:
        print(
            f"Request failed with status code {response.status_code}, Response: {response.content.decode()}"
        )
        return False


def notify(user_id, class_id, absences, remaining_min):
    phone_number = get_phone_number(user_id)
    class_name = database_manager.get_class(class_id)["class_name"]
    tosend = generate_voice_message(class_name, absences, remaining_min)
    url = speach_text(tosend)
    call_number(phone_number, url)


def main():
    upcoming_classes = get_upcoming_classes("SA", 1)
    for cls in upcoming_classes:
        class_id = cls["class_id"]
        class_name = cls["class_name"]
        absences = cls["absences"]
        remaining_min = 10
        notify("google-oauth2|105038472575077144999", class_id, absences, remaining_min)


def send_sms(phone_number, message):
    # curl -u o7a0cfpSNZmOWC1Dzj2qV9E4sUdx8MKT:p56fvwxb84iam9urskh2go7et01cjd3z --data-urlencode 'recipient=+8190123456789' --data-urlencode 'sender=Xoxzo1' --data-urlencode 'message=こんにちは' https://api.xoxzo.com/sms/messages/
    username = "o7a0cfpSNZmOWC1Dzj2qV9E4sUdx8MKT"
    password = "p56fvwxb84iam9urskh2go7et01cjd3z"

    api_url = "https://api.xoxzo.com/sms/messages/"

    payload = {
        "recipient": phone_number,
        "sender": "klis-nine",
        "message": message,
    }

    # Make the POST request
    response = requests.post(
        api_url, data=payload, auth=HTTPBasicAuth(username, password)
    )

    # Check and return the response
    if response.status_code == 200 or response.status_code == 201:
        return True
    else:
        print(
            f"Request failed with status code {response.status_code}, Response: {response.content.decode()}"
        )
        return False

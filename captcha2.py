import random
from captcha.image import ImageCaptcha
import requests
from constants import *

def create_captcha():
    image = ImageCaptcha(width=280, height=170)
    captcha_text = ''
    for letter in range(ord('А'), ord('Я')+1):
        captcha_text += chr(letter)
    result = ''
    for i in range(7):
        index = random.randint(0, 31)
        result += captcha_text[index]
    data = image.generate(result)
    file_photo = 'CAPTCHA.png'
    image.write(result, file_photo)
    return file_photo, result

def send_captcha(chat_id, file_photo):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {'photo': open(file_photo, 'rb')}
    data = {'chat_id': chat_id}
    response = requests.post(url, files=files, data=data)
    return response.json()

def captcha(message):
    file_photo, result = create_captcha()
    chat_id = message.chat.id
    response = send_captcha(chat_id, file_photo)
    return result

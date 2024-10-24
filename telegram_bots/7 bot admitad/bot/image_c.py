import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def download_image(url, type):
    if type == 'coupon':
        url_temp = 'https://thumb.cloud.mail.ru/weblink/thumb/xw1/'
        url = f"{url_temp}{url.split('/')[-2]}/{url.split('/')[-1]}"
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        return None

def add_text_with_outline(image, text, position=(10, 10), font_size=20, font_color=(255, 255, 255), outline_color=(0, 0, 0), outline_width=2):
    draw = ImageDraw.Draw(image)
    # Разделение текста на два блока
    text1 = text.split('erid')[0]
    text2 = f"erid{text.split('erid')[1]}"
    text1 = text1.replace(', ИНН', '\nИНН')

    if image.width > 1500:
        font_size=50
    elif 1500 >= image.width > 1000:
        font_size=35
    elif 1000>=image.width > 800:
        font_size=20
    elif 800>=image.width:
        font_size=15
    font = ImageFont.truetype("arial.ttf", font_size)  # Make sure to have the font file or use a different one

    x, y = position

    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:  # Avoid drawing the center twice
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)

    # Draw the main text
    draw.text((x, y), text, font=font, fill=font_color)

    return image

def save_image(image, path):
    image.save(path)


def add_text(image_url, text_to_add, type):
    try:
    # Скачивание изображения
        img = download_image(image_url, type)
        if img.width < 470:
            return None
        # Добавление текста на изображение
        # img_with_text = add_text_with_outline(img, text_to_add)

        # Сохранение изображения
        save_image(img, 'image.png')
        return 'image.png'

    except Exception as e:
        print(e)
        return None


if __name__ == "__main__":
    # Текст, который нужно добавить
    text_to_add = "Sample Text"
    image_url = 'https://play-lh.googleusercontent.com/dSYp-Czyew5T2LZhVgCCyM0wf0dG-J8Os4JoK2JT4NIF8mW7gWIqDS-9FH14-oNz0A'
    add_text(image_url, text_to_add)
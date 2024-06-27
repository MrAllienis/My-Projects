import pyautogui
import time
import easyocr
import openpyxl
from openpyxl import load_workbook, Workbook
from numbers1 import main2
from PIL import Image, ImageFilter, ImageEnhance





output_path = "screens/screenshot.png"  # путь для сохранения скриншота
path2 = "screens/screenshot2.png"




def capture_screen(x, y, width, height, output_path):
    # Получаем изображение с экрана в указанной области
    screenshot = pyautogui.screenshot(region=(x, y, width, height))

    # Сохраняем полученное изображение
    screenshot.save(output_path)
    # print("Захват экрана сохранен в", output_path)

def text_rec(path):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(path, detail=0)
    return result

def save_to_xlsx(num):
    wb = load_workbook('numbers.xlsx')
    ws = wb.active
    ws.append(num)
    wb.save('numbers.xlsx')
    print(f"Число {num[0]} сохранено.")


def photo_size():
    image = Image.open(output_path)
    # Изменяем размер изображения с помощью интерполяции
    resized_image = image.resize((300, 200), Image.NEAREST)
    resized_image.save(output_path)

def photo_filter():
    # Открываем изображение
    image = Image.open(output_path)
    # Увеличиваем резкость изображения
    image_sharpened = image.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(image_sharpened)
    enhanced_image = enhancer.enhance(2.0)  # Здесь 2.0 - это множитель контраста
    # Сохраняем улучшенное изображение
    enhanced_image.save(output_path)


def validate(seconds):
    x = 1157  # координата x верхнего левого угла области
    y = 965  # координата y верхнего левого угла области
    width = 30  # ширина области
    height = 25  # высота области

    start_time = time.time()
    time.sleep(seconds-3.7)

    # Получаем изображение с экрана в указанной области
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    # Изменяем размер изображения с помощью интерполяции
    resized_image = screenshot.resize((300, 250), Image.NEAREST)
    image_sharpened = resized_image.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(image_sharpened)
    enhanced_image = enhancer.enhance(2.0)  # Здесь 2.0 - это множитель контраста
    enhanced_image.save(path2)
    reader = easyocr.Reader(['en'])
    result = reader.readtext(path2, detail=0)

    end_time = time.time()
    execution_time = end_time - start_time
    print("Время между скриншотами: ", execution_time, " секунд")

    return result[0][0:2]



def main():
    # active_number = ''
    # previous_number = ''
    # previous_number2 = ''
    x = 1860  # координата x верхнего левого угла области
    y = 1030  # координата y верхнего левого угла области
    width = 30  # ширина области
    height = 20  # высота области
    seconds = 4
    print("Добро пожаловать в программу вычисления вероятности чисел!")
    choice = None
    while choice != "0":
        choice = input(f"\nМеню опций:\n1 - Начало записи чисел в файл.\n2 - Определение вероятности следующих 3-ёх чисел после определённого числа.\n3 - Поменять кординаты для захвата числа.\n4 - Поменять размер области захвата\n5 - Изменить время между скриншотами\n0 - Выход из программы.\nВведите цифру из предложенных, чтобы выбрать опцию: ")
        if choice == "1":

            end = ''
            end = input(
                f"После нажатии клавиши 'Enter', через 5 секунд сделается скриншот экрана и текущее нижнее число в игре запишется в файл 'numbers.xlsx'. Затем будет записываться текущее число во время обратного отсчёта. \nВ любой моммент закройте программу, чтобы закончить сохранение чисел: ")
            time.sleep(5)
            while end != 'end':
                try:
                    num = ''
                    if end != 'end':
                        while True:
                            screens = ['15', '14', '13', '12']
                            try:
                                screen = validate(seconds)
                            except:
                                print('Число не обновлено')
                            if screen in screens:
                                capture_screen(x, y, width, height, output_path)
                                filePath = output_path
                                photo_size()
                                num = text_rec(path=filePath)
                                try:
                                    if (int(num[0]) in range(0, 37)) or (num[0] == '00'):
                                        save_to_xlsx(num)
                                except:
                                    photo_filter()
                                    num = text_rec(path=filePath)
                                    if (int(num[0]) in range(0, 37)) or (num[0] == '00'):
                                        save_to_xlsx(num)
                                    else:
                                        print("! Было получено недопустимое значение. Возможно, игра не была открыта, или были изменены координаты. !")

                            # time.sleep(seconds)
                            # input('next')
                except:
                    pass
        elif choice == "2":
            main2()
        elif choice == "3":
            print("Значения по умолчанию (координаты верхнего левого угла области): X = 1860; Y = 1030 ")
            x = int(input("X: "))
            y = int(input("Y: "))
        elif choice == "4":
            print("Значения по умолчанию (ширина и высота области): X = 30; Y = 20 ")
            width = int(input("X: "))
            height = int(input("Y: "))
        elif choice == "5":
            print("Количество секунд между скриншотами примерно равно 4")
            seconds = int(input("Новое количество секунд: "))
        else:
            if choice != "0":
                print(f"Вы ввели недопустимое значение: {choice}")


if __name__ == '__main__':
    main()




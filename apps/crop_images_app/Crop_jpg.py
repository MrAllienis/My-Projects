import cv2
import os
import re
import time
import icecream
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

import numpy as np


target_size = None
# front_and_back = 0
count_of_photos = 0
the_end = 0


def extract_page_number(filename):
    match = os.path.splitext(filename)[0][-4:]
    if match:
        return int(match)
    else:
        raise ValueError("Имя файла не содержит номер страницы")

# Определение границы фото
def detect_page_boundaries(image, page_number):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    center_col = width // 2
    front = 1
    global count_of_photos
    back = count_of_photos

    if width > 2700:
        minus = 40
        boundary_offset = 170
    elif 2700 >= width > 2500:
        minus = 35
        boundary_offset = 160
    elif 2500 >= width > 2000:
        minus = 30
        boundary_offset = 150
    elif 2000 >= width > 1500:
        minus = 25
        boundary_offset = 130
    elif 1500 >= width > 1250:
        minus = 20
        boundary_offset = 120
    elif 1250 >= width > 1000:
        minus = 15
        boundary_offset = 108
    elif 1000 >= width:
        minus = 10
        boundary_offset = 90


    # Находит первое место где 5 пикслей подряд светлее
    def find_boundary(array):
        for i in range(len(array) - 5):
            if all(array[i + j] > 100 for j in range(5)):
                return i + minus
        return -1

    # Определение обложки и соседних к ним страниц (задней или передней)
    def find_front_and_back(array):
        for i in range(len(array) - 4):
            if all(array[i + j] > 55 for j in range(4)):
                return i
        return -1

    def find_front_and_back2(array):
        for i in range(len(array) - 10):
            if all(array[i + j] > 50 for j in range(10)):
                return i
        return -1

    # def neigh_page(array):
    #     for i in range(len(array) - 3):
    #         if all(array[i + j] < 190 for j in range(3)):
    #             return i
    #     return -1


    # Работа с обложками и их разворотами


    if page_number in [front, back]:
        left_boundary = find_front_and_back(gray[height // 2, :])
        right_boundary = width - find_front_and_back(gray[height // 2, ::-1])
        top_boundary = find_front_and_back(gray[:, center_col])
        bottom_boundary = height - find_front_and_back(gray[::-1, center_col])
    elif page_number in [front+1, back-1]:
        if page_number % 2 == 0:
            left_boundary = find_front_and_back2(gray[height // 2, :])
            # right_boundary = width - neigh_page(gray[height // 2, ::-1])
            right_boundary = width - boundary_offset
        else:
            right_boundary = width - find_front_and_back2(gray[height // 2, ::-1])
            # left_boundary = neigh_page(gray[height // 2, :])
            left_boundary = boundary_offset
        top_boundary = find_front_and_back2(gray[:, center_col])
        bottom_boundary = height - find_front_and_back2(gray[::-1, center_col])

    # Работа с остальными страницами
    else:
        if page_number % 2 == 0:
            left_boundary = find_boundary(gray[height // 2, :])
            # right_boundary = width - neigh_page(gray[height // 2, ::-1])
            right_boundary = width - boundary_offset
        else:
            right_boundary = width - find_boundary(gray[height // 2, ::-1])
            # left_boundary = neigh_page(gray[height // 2, :])
            left_boundary = boundary_offset
        top_boundary = find_boundary(gray[:, center_col])+10
        bottom_boundary = height - find_boundary(gray[::-1, center_col])-10




    # if top_boundary < 50 or bottom_boundary > (height - 50) or \
    #         left_boundary < 50 or right_boundary > (width - 50):
    #     return None

    return top_boundary, bottom_boundary, left_boundary, right_boundary


# Открытие фотографии и поиск границ
def process_image(image_path):
    try:
        image = cv2.imread(image_path)
        page_number = extract_page_number(os.path.basename(image_path))
        boundaries = detect_page_boundaries(image, page_number)
        if boundaries is None:
            return None, image_path
        return boundaries, image_path
    except Exception as e:
        # print(f"Error processing {image_path}: {e}")
        print(f"Ошибка обработки изображения {image_path}: {e}")
        return None, image_path


# Поиск границ фотографий
def find_all_boundaries(image_paths, source_folder_name, threshold=100):
    start_time = time.time()
    global count_of_photos
    count_of_photos = len(image_paths)

    # Работа с фото в многопотоке
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(executor.map(process_image, image_paths))

    valid_results = [r for r, path in results if r is not None]
    if not valid_results:
        # print("No valid results found.")
        print("Результаты не найдены.")
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = []
            for _, path in results:
                futures.append(executor.submit(save_unprocessed, path, unprocessed_folder, source_folder_name))
            for future in futures:
                future.result()
        return None, []

    first_page_boundaries = None
    for r, path in results:
        if r is not None:
            first_page_boundaries = r
            first_path = path
            break

    if first_page_boundaries is None:
        # print("No valid results found after filtering.")
        print("Нет результатов после фильтрации.")
        return None, [path for _, path in results]

    first_page_height = first_page_boundaries[1] - first_page_boundaries[0]
    first_page_width = first_page_boundaries[3] - first_page_boundaries[2]

    final_results = [(r, path) for r, path in results if r is not None and [
                     abs((r[1] - r[0]) - first_page_height) < threshold and
                     abs((r[3] - r[2]) - first_page_width) < threshold]]

    # outliers = [path for _, path in results if _ is None or [
    #         abs((_[1] - _[0]) - first_page_height) >= threshold or
    #         abs((_[3] - _[2]) - first_page_width) >= threshold]]

    if not final_results:
        # print("No final results found after filtering.")
        print("Нет результатов после фильтрации.")
        return
        # return None, outliers

    # avg_top = int(np.mean([r[0] for r, _ in final_results]))
    # avg_bottom = int(np.mean([r[1] for r, _ in final_results]))
    # avg_left = int(np.mean([r[2] for r, _ in final_results]))
    # avg_right = int(np.mean([r[3] for r, _ in final_results]))

    # elapsed_time = time.time() - start_time
    # print(f"find_average_frame_parallel took {elapsed_time:.2f} seconds")

    return final_results


# Выравнивание фото
def image_angel_rotar(image):
    # Определяем угол наклона
    angle = determine_skew(image)

    # Поворот изображения
    rotated = rotate_image(image, -angle)

    angle2 = determine_skew(rotated)

    # Сохранение выровненного изображения
    if abs(angle + angle2) < 2:
        print(f'Угол наклона текста: {angle + angle2} градусов')
        rotated2 = rotate_image(rotated, -angle2)
        return rotated2
    else:
        return image


def determine_skew(image):
    # Преобразование в оттенки серого
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Применение размытия для уменьшения шума
    gray = cv2.GaussianBlur(gray, (9, 9), 0)

    # Применение порогового значения для создания бинарного изображения
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Инвертирование изображения
    binary = cv2.bitwise_not(binary)

    # Находим координаты белых пикселей
    coords = np.column_stack(np.where(binary > 0))

    # Применяем линейную регрессию для нахождения линии, описывающей текст
    [vx, vy, x, y] = cv2.fitLine(coords, cv2.DIST_L2, 0, 0.01, 0.01)

    # Определяем угол наклона
    angle = np.arctan2(vy, vx)[0] * 180 / np.pi  # Извлечение значения из массива

    return angle

def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated


# Обрезка и сохранение
def crop_and_save(image_path, frame, output_folder_tiff, output_folder_jpg, source_folder_name):
    start_time = time.time()
    with Image.open(image_path) as image:
        dpi = image.info.get('dpi', (None, None))
        # image = cv2.imread(image_path)
    # height, width = image.shape[:2]
        image = np.array(image)
        top, bottom, left, right = frame

        top = max(0, top)
        bottom = max(0, bottom)
        left = max(0, left)
        right = max(0, right)


    # page_number = extract_page_number(os.path.basename(image_path))

    # Центрируем рамку
    # center_x = (left + right) // 2
    # center_y = (top + bottom) // 2
    # frame_n_top = center_y - (bottom - top) // 2
    # frame_n_bottom = center_y + (bottom - top) // 2
    # frame_n_left = center_x - (right - left) // 2
    # frame_n_right = center_x + (right - left) // 2

    # Увеличиваем рамку для TIFF
    # cm_to_pixels = int(0.55 * 118.11)
    # if page_number % 2 == 0:
    #     tiff_left = max(0, frame_n_left - cm_to_pixels)
    #     tiff_right = min(width, frame_n_right + cm_to_pixels * 2)
    # else:
    #     tiff_left = max(0, frame_n_left - cm_to_pixels * 2)
    #     tiff_right = min(width, frame_n_right + cm_to_pixels)
    # tiff_top = max(0, frame_n_top - cm_to_pixels)
    # tiff_bottom = min(height, frame_n_bottom + cm_to_pixels)
    # cropped_tiff = image[tiff_top:tiff_bottom, tiff_left:tiff_right]

    # Обрезанный тиф файл
        cropped_jpg = image[top:bottom, left:right]

        if cropped_jpg.size == 0:
            print(f"Ошибка:  JPG изображение пустое {image_path}")
            return

        global target_size
        if target_size is None:
            target_size = (cropped_jpg.shape[1], cropped_jpg.shape[0])


        # Масштабирует фото под единый размер
        resized_image_jpg = cv2.resize(cropped_jpg, target_size, interpolation=cv2.INTER_AREA)
        # Выравнивание фото
        # final_image = image_angel_rotar(resized_image_jpg)

    # cm_to_pixels = int(0.4 * 118.11)
    # cm_to_pixels_more = int(0.3 * 118.11)
    # cm_to_pixels_less = int(-0.62 * 118.11)
    # if page_number % 2 == 0:
    #     jpg_left = min(width, frame_n_left + cm_to_pixels_more)
    #     jpg_right = frame_n_right - cm_to_pixels_less
    # else:
    #     jpg_left = frame_n_left + cm_to_pixels_less
    #     jpg_right = max(0, frame_n_right - cm_to_pixels_more)
    #
    # jpg_top = max(0, frame_n_top + cm_to_pixels)
    # jpg_bottom = min(height, frame_n_bottom - cm_to_pixels)
    # cropped_jpg = image[jpg_top:jpg_bottom, jpg_left:jpg_right]
    # cropped_jpg = image[top:bottom, left:right]
    #
    # if cropped_jpg.size == 0:
    #     print(f"Error: Cropped JPG image is empty for {image_path}")
    #     return

        filename = os.path.splitext(os.path.basename(image_path))[0]
        filename_with_prefix = f"{source_folder_name} - {filename}"

        # tiff_output_path = os.path.join(output_folder_tiff, filename_with_prefix + ".tif")
        jpg_output_path = os.path.join(output_folder_jpg, filename_with_prefix + ".jpg")

        # cv2.imwrite(tiff_output_path, resized_image_tif)
        # cv2.imwrite(jpg_output_path, resized_image_jpg)
        # Сохранение изображения в файл с помощью Pillow
        final_image = Image.fromarray(resized_image_jpg)
        final_image.save(jpg_output_path, dpi=dpi)  # Сохранение с оригинальным DPI
        elapsed_time = time.time() - start_time
        print(f"Обработан файл {filename}.jpg за {elapsed_time:.2f} секунд")


# Основная функция
def process_folder(folder_path, output_folder_tiff, output_folder_jpg, unprocessed_folder):
    start_time = time.time()
    source_folder_name = os.path.basename(folder_path)

    # Поиск фотографий из папки
    image_paths = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path) if
                   filename.endswith(".tif")]
    final_results = find_all_boundaries(image_paths, source_folder_name)
    # icecream.ic(outliers)
    # os.makedirs(output_folder_tiff, exist_ok=True)
    os.makedirs(output_folder_jpg, exist_ok=True)
    # os.makedirs(unprocessed_folder, exist_ok=True)

    # if avg_frame is None:
    #     print("No valid average frame could be determined. Exiting.")
    #     return


    # Запуск обрезки и сохранения фото в многопоточности
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = []
        for boundaries, image_path in final_results:
            # boundaries, _ = process_image(image_path)
            if boundaries is None:
                futures.append(executor.submit(save_unprocessed, image_path, unprocessed_folder, source_folder_name))
            else:
                futures.append(
                    executor.submit(crop_and_save, image_path, boundaries, output_folder_tiff, output_folder_jpg,
                                    source_folder_name))
        for future in futures:
            future.result()

    # while outliers:
    #     print(f"Processing outliers...")
    #     avg_frame_outliers, new_outliners = find_average_frame_parallel(outliers, source_folder_name)
    #     icecream.ic(new_outliners)
    #     if avg_frame_outliers is None:
    #         print("No valid average frame for outliers. Saving all outliers as unprocessed.")
    #         with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    #             futures = []
    #             for image_path in outliers:
    #                 futures.append(executor.submit(save_unprocessed, image_path, unprocessed_folder,
    #                                                source_folder_name))
    #             for future in futures:
    #                 future.result()
    #         break
    #
    #     with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    #         futures = []
    #         for image_path in outliers:
    #             boundaries, _ = process_image(image_path)
    #             if boundaries is None:
    #                 futures.append(executor.submit(save_unprocessed, image_path, unprocessed_folder,
    #                                                source_folder_name))
    #             else:
    #                 futures.append(executor.submit(crop_and_save, image_path, avg_frame_outliers, output_folder_tiff,
    #                                                output_folder_jpg,
    #                                                source_folder_name))
    #         for future in futures:
    #             future.result()
    #         outliers = new_outliners

    total_elapsed_time = time.time() - start_time
    # print(f"Process_folder took {total_elapsed_time:.2f} seconds")
    print('==========================')
    print(f"Процесс выполнен за {total_elapsed_time:.2f} секунд")





def save_unprocessed(image_path, unprocessed_folder, source_folder_name):
    # filename = os.path.basename(image_path)
    # filename_with_prefix = f"{source_folder_name} - {filename}"  # Префикс с исходной папкой
    # output_path = os.path.join(unprocessed_folder, filename_with_prefix)
    # image = cv2.imread(image_path)
    # cv2.imwrite(output_path, image)
    # print(f"Saved unprocessed image {filename_with_prefix} to {unprocessed_folder}")
    print('Ошибка')


def check_dir(directory):
    # Проход по всем элементам в директории
    dirs = []
    for item in os.listdir(directory):
        # Получение полного пути к элементу
        full_path = os.path.join(directory, item)
        # Проверка, является ли элемент папкой
        if os.path.isdir(full_path):
            dirs.append(item)
    return dirs


def main():
    folder_path = 'data'
    output_folder_tiff = 'result'
    output_folder_jpg = 'result_jpg'
    unprocessed_folder = 'result/unprocessed'

    print(
        f"\nЭта программа обрезает фотографии страниц, находящихся в папке '{folder_path}'.\nВ путях к фотографиям не должно быть кириллицы. Перед началом работы можете изменить путь к файлам.\nЧтобы изменить путь к файлам, скопируйте и вставьте его сюда (если не требуется - нажмите ENTER).")
    files_name = input("Путь к файлам: ")

    if files_name != '':
        folder_path = files_name

    print(
        f"\nРезультат будет сохранен в '{output_folder_jpg}'. Чтобы изменить путь сохранения, скопируйте и вставьте его сюда (если не требуется - нажмите ENTER).")
    files_name2 = input("Путь для результата: ")
    if files_name2 != '':
        output_folder_jpg = files_name2

    print('==========================')
    dirs = check_dir(folder_path)
    for dir in dirs:
        try:
            print(f'Работа с папкой {dir}\n')
            process_folder(f'{folder_path}/{dir}', output_folder_tiff, f'{output_folder_jpg}/{dir}', unprocessed_folder)
            print('==========================')

        except:
            print(f"! Произошла ошибка, связанная с путём '{folder_path}/{dir}'. Возможно, указанного пути не существует, либо в нём присутствует кириллица. Попробуйте еще раз")
        global target_size
        target_size = None
    time.sleep(2)
    global the_end
    the_end += 1
    input("Нажмите ENTER для выхода")




if __name__ == '__main__':
    print('Добро пожаловать!')

    while the_end == 0:
        try:
            main()
        except:
            print("Произошла ошибка. Возможно, указанного пути не существует, либо в нём присутствует кириллица. Попробуйте еще раз")
            print('==========================')
            time.sleep(2)






import telebot
from telebot import types
from numbers1 import main2
import openpyxl

bot = telebot.TeleBot("6592509447:AAFqDiWsisoWJkcvrx-ZFDJxh7-L0eHFHn8", parse_mode='HTML')

@bot.message_handler(commands=['start'])
def start(message):
	bot.send_message(message.chat.id, f'Добро пожаловать в бота по определению вероятности чисел. Вам будут выданы три следующих наиболее вероятных числа')


def load_numbers():
    numbers1 = []
    wb = openpyxl.load_workbook('numbers.xlsx')
    ws = wb.active
    for row in ws.iter_rows(values_only=True):
        for cell in row:
            numbers1.append(cell)
    wb.close()
    return numbers1



def calculate_probabilities(numbers):
    # создаем словарь для хранения вероятностей
    probabilities = {}

    # считаем количество каждого числа в списке
    for i in range(len(numbers)-1):
        current_number = numbers[i]

        # проверяем, достаточно ли чисел для вычисления следующих трех
        if i+3 >= len(numbers):
            break

        next_numbers = tuple(numbers[i+1:i+4])  # берем следующие три числа

        if current_number not in probabilities:
            probabilities[current_number] = {}

        if next_numbers not in probabilities[current_number]:
            probabilities[current_number][next_numbers] = 0

        probabilities[current_number][next_numbers] += 1

    # вычисляем вероятности делением количества каждой последовательности на общее количество
    for current_number, next_sequences in probabilities.items():
        total_count = sum(next_sequences.values())
        for next_sequence, count in next_sequences.items():
            probabilities[current_number][next_sequence] = count / total_count

    return probabilities


def print_probabilities(probabilities, num, message):
    # выводим вероятности
    try:
        for current_number, next_sequences in probabilities.items():
            if current_number == num:
                for next_sequence, probability in next_sequences.items():
                    printE, prob = list(next_sequence), probability
                    bot.send_message(message.chat.id, f'{printE[0]}, {printE[1]}, {printE[2]}\nВероятность - {round((prob * 100), 2)} %')
    except:
        bot.send_message(message.chat.id, f'Вы ввели недопустимое, либо пустое значение: {num}')



def numbersv(message):
    numbers = load_numbers()
    end = message.text
    probabilities = calculate_probabilities(numbers)
    print_probabilities(probabilities, end, message)



@bot.message_handler(content_types=['text'])
def number(message):
    numbersv(message)


bot.infinity_polling()





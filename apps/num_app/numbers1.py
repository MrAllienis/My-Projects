import openpyxl


def load_numbers():
    numbers1 = []
    wb = openpyxl.load_workbook('numbers.xlsx')
    ws = wb.active
    for row in ws.iter_rows(values_only=True):
        for cell in row:
            numbers1.append(str(cell))
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

def print_probabilities(probabilities, num):
    # выводим вероятности
    try:
        if (int(num[0]) in range(0, 37)) or (num[0] == '00'):
            for current_number, next_sequences in probabilities.items():
                if current_number == num:
                    for next_sequence, probability in next_sequences.items():
                        printE, prob = list(next_sequence), probability
                        print(f'{printE[0]}, {printE[1]}, {printE[2]}    Вероятность - {round((prob * 100), 2)} %')
        else:
            print(f'Вы ввели недопустимое, либо пустое значение: {num}')
    except:
        print(f'Вы ввели недопустимое, либо пустое значение: {num}')


def main2():
    end = ''
    while end != 'end':
        # numbers = [1, 5, 6, 4, 8, 12, 2, 3, 6, 9, 10, 32, 36, 36, 1, 5, 6, 17, 18, 25, 18, 1, 5, 10, 11, 29, 31, 16, 36, 35, 1, 5, 10, 11, 29, 31, 16, 36]
        numbers = load_numbers()

        end = input(f"\nВведите число, или введите 'end', чтобы вернуться назад: ")
        if end != 'end':
            probabilities = calculate_probabilities(numbers)
            print_probabilities(probabilities, end)


if __name__ == '__main__':
    main2()
import os
import platform
import getpass

def verify_password():
    # Установите ваш пароль здесь
    correct_password = "5db876rd6x6b1"
    password = getpass.getpass("Введите пароль: ")
    return password == correct_password

def modify_hosts(site, action="block"):
    # Определяем путь к файлу hosts в зависимости от операционной системы
    if platform.system() == "Windows":
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    else:
        hosts_path = "/etc/hosts"

    redirect_ip = "127.0.0.1"

    if not verify_password():
        print("Неверный пароль. Доступ запрещен.")
        return

    try:
        with open(hosts_path, 'r+') as hosts_file:
            lines = hosts_file.readlines()
            hosts_file.seek(0)
            if action == "block":
                # Блокировка сайта
                if any(site in line for line in lines):
                    print(f"Сайт {site} уже заблокирован.")
                else:
                    hosts_file.writelines(lines)
                    hosts_file.write(f"{redirect_ip} {site}\n")
                    print(f"Сайт {site} успешно заблокирован.")
            elif action == "unblock":
                # Разблокировка сайта
                for line in lines:
                    if site not in line:
                        hosts_file.write(line)
                hosts_file.truncate()
                print(f"Сайт {site} успешно разблокирован.")
    except PermissionError:
        print("Недостаточно прав для изменения файла hosts. Запустите скрипт с правами администратора.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

# Пример использования
site_to_modify = "example.com"
action_to_take = "block"  # Используйте "unblock" для разблокировки сайта

modify_hosts(site_to_modify, action_to_take)

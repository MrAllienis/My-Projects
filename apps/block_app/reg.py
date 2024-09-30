
import winreg

def add_to_registry(key_path, value_name, value_data):
    try:
        # Открываем ключ реестра для записи
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)

        # Записываем значение в реестр
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value_data)
        winreg.SetValueEx(key, "RequiresElevation", 0, winreg.REG_DWORD, 1)

        # Закрываем ключ реестра
        winreg.CloseKey(key)

        print(f"Добавлено значение '{value_name}' со значением '{value_data}' в реестр по пути {key_path}")

    except Exception as e:
        print(f"Ошибка при добавлении в реестр: {e}")

if __name__ == "__main__":
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    value_name = "BlockSitesScript"
    value_data = r"C:\Users\HP\PycharmProjects\Freelance\My freelance\6\app\block.exe"

    add_to_registry(key_path, value_name, value_data)

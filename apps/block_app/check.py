import subprocess

def run_powershell_command(command):
    result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)
    return result.stdout, result.stderr

def check_and_restore_firewall_rule():
    rule_name = "Block_1xbet"
    remote_address = "1xbet.by"

    # Команда для проверки наличия правила
    check_command = f'Get-NetFirewallRule -DisplayName "{rule_name}" -ErrorAction SilentlyContinue'

    # Команда для создания правила, если оно отсутствует
    create_command = f'New-NetFirewallRule -DisplayName "{rule_name}" -Direction Outbound -Action Block -RemoteAddress "{remote_address}" -Description "Block access to {remote_address}"'

    try:
        # Выполнение команды проверки
        check_stdout, check_stderr = run_powershell_command(check_command)

        if not check_stdout.strip():
            # Если правило отсутствует, создаем его заново
            create_stdout, create_stderr = run_powershell_command(create_command)
            print(f"Rule {rule_name} has been recreated.")
            print("Create command output:", create_stdout)
            print("Create command errors:", create_stderr)
        else:
            print(f"Rule {rule_name} already exists.")
            print("Check command output:", check_stdout)
            print("Check command errors:", check_stderr)

    except Exception as e:
        print(f"Ошибка при выполнении PowerShell команды: {e}")

if __name__ == "__main__":
    check_and_restore_firewall_rule()

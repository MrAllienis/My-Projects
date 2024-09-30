import subprocess
import socket
import time

def get_ip_addresses(domain):
    try:
        return socket.gethostbyname_ex(domain)[2]
    except socket.gaierror:
        print(f"Не удалось получить IP-адреса для {domain}")
        return []

def rule_exists(rule_name):
    command = ['netsh', 'advfirewall', 'firewall', 'show', 'rule', f'name={rule_name}']
    result = subprocess.run(command, capture_output=True, text=True)
    return "No rules match the specified criteria" not in result.stdout and rule_name in result.stdout

def add_firewall_rule(site, ip_addresses):
    rule_name = f"Block_{site}"

    if not rule_exists(rule_name):
        for ip in ip_addresses:
            command = [
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                f'name={rule_name}', 'dir=out', 'action=block',
                f'remoteip={ip}'
            ]
            subprocess.run(command, check=True)
            print(f"Блокировка {ip} для {site} добавлена.")
    else:
        print(f"Правило {rule_name} уже существует.")

if __name__ == "__main__":
    while True:
        domains = []
        with open('sites.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for line in lines:
                if line != lines[-1]:
                    domains.append(line[:-1])
                else:
                    domains.append(line)
        for domain in domains:
            ip_addresses = get_ip_addresses(domain)
            if ip_addresses:
                add_firewall_rule(domain, ip_addresses)
        time.sleep(5)

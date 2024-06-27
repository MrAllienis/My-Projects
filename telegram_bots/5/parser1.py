import requests
import sqlite3

# def create_table():
#     conn = sqlite3.connect('tickets.db')
#     cursor = conn.cursor()
#     cursor.execute('''CREATE TABLE IF NOT EXISTS numbers (
#                         number INTEGER,
#                         count INTEGER,
#                         circulation INTEGER,
#                         PRIMARY KEY (number, circulation)
#                     )''')
#     conn.commit()
#     conn.close()
class Tickets():


    @staticmethod
    def parse_tickets(circulation=1547):
        # print('+20 билетов извлечено')
        url = "https://www.stoloto.ru/p/api/mobile/api/v35/games/change"
        payload = {'game': 'ruslotto',
                   'playerId': 'f55cca7d-273b-44e3-ab50-37272beaacc3',
                   'count': '20',
                   'choosenTickets': ''}
        response = requests.request("POST", url, data=payload)
        tickets = response.json()['tickets']
        conn = sqlite3.connect('tickets.db')
        cur = conn.cursor()
        for ticket in tickets:
            try:
                cur.execute('SELECT tickets (code, circulation) WHERE code = ? AND circulation = ?', (int(ticket["barCode"]), circulation))
                print(f'Такой билет уже есть ({ticket["barCode"]})')
            except:
                cur.execute('INSERT OR IGNORE INTO tickets (code, circulation) VALUES (?, ?)', (int(ticket["barCode"]), circulation))
                for num in ticket["numbers"]:
                    cur.execute('INSERT OR IGNORE INTO numbers (number, count, circulation) VALUES (?, ?, ?)', (int(num), 0, circulation))
                    cur.execute('UPDATE numbers SET count = count + 1 WHERE number = ? AND circulation = ?', (int(num), circulation))
        conn.commit()
        cur.close()
        conn.close()


    @staticmethod
    def clear_all_data():
        conn = sqlite3.connect('tickets.db')
        cur = conn.cursor()
        cur.execute('DELETE FROM tickets')
        cur.execute('DELETE FROM numbers')
        conn.commit()
        cur.close()
        conn.close()
        
    @staticmethod    
    def get_statistic():
        conn = sqlite3.connect('tickets.db')
        cur = conn.cursor()
        cur.execute('SELECT number, count FROM numbers ORDER BY number ASC')
        statistic = cur.fetchall()
        cur.execute('SELECT * FROM numbers ORDER BY count DESC LIMIT 10')
        fast_stat = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return statistic, fast_stat


    @staticmethod
    def count():
        conn = sqlite3.connect('tickets.db')
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM tickets')
        row_count = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return row_count



tickets = Tickets()

if __name__ == '__main__':
    tickets.parse_tickets()






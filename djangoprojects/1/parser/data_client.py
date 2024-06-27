import psycopg2
from psycopg2 import Error
from abc import ABC, abstractmethod



class DataClient(ABC):
    @staticmethod
    def get_connection():
        pass

    @abstractmethod
    def create_mebel_table(self):
        pass

    @abstractmethod
    def get_items(self, price_from=0, price_to=10000):
        pass

    @abstractmethod
    def insert(self, link, price, description):
        pass

    def run(self):
        conn = self.get_connection()
        self.create_mebel_table()
        items = self.get_items(0, 50)
        for item in items:
            print(item)
        conn.close()


class PostgresClient(DataClient):
    NAME = "postgres1"
    USER = "postgres"
    PASSWORD = "1a2s3d4f"
    HOST = "localhost"
    PORT = "5432"

    def get_connection(self):
        try:
            connection = psycopg2.connect(
                dbname=self.NAME,
                user=self.USER,
                password=self.PASSWORD,
                host=self.HOST,
                port=self.PORT
            )
            return connection
        except Error:
            print(Error)

    def create_mebel_table(self):
        with self.get_connection() as conn:
            cursor_object = conn.cursor()
            cursor_object.execute(
                """
                    CREATE TABLE IF NOT EXISTS testapp1_mebel
                    (
                        id serial PRIMARY KEY,
                        link text,
                        price integer,
                        description text
                    )
                """
            )

    def get_items(self, price_from=0, price_to=10000):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM testapp1_mebel WHERE price >= {price_from} and price <= {price_to}')
            return cursor.fetchall()


    def insert(self, link, price, description):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO testapp1_mebel(link, price, description) VALUES ('{link}', '{float(price)}', '{description}') ON CONFLICT DO NOTHING")
            conn.commit()


dataclient = PostgresClient()

dataclient.run()

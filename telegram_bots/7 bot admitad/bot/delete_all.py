import psycopg2

DB_NAME = "postgres1"
DB_USER = "postgres"
DB_PASSWORD = "1a2s3d4f"
DB_HOST = "localhost"
DB_PORT = "5432"

def delete_all():
    connection = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = connection.cursor()
    # Выполнение запроса
    try:
        cursor.execute("""
                        DELETE FROM sales_app_product
                        """)
        cursor.execute("""
                                        DELETE FROM sales_app_coupon
                                        """)
        cursor.execute("""
                                DELETE FROM sales_app_shop
                                """)
        connection.commit()
    finally:
        # Закрытие курсора и подключения
        cursor.close()
        connection.close()

if __name__ == "__main__":
    delete_all()
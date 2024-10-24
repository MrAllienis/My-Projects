import requests
import pandas as pd
import io
import os
import subprocess



def download_csv(feeds, check=True):
    final = []
    file_path = 'data.csv'
    try:
        with open(file_path, 'wb') as file:
            for feed in feeds:
                response = requests.get(feed['csv_link'], stream=True, allow_redirects=True)
                for chunk in response.iter_content(chunk_size=100000000):
                    file.write(chunk)
        # response.raise_for_status()  # Проверяем успешность запроса
    except Exception as e:
        print(f"Error parsing CSV: {e}")
    print('Запрос выполнен')
    downloaded_file_size = os.path.getsize(file_path)
    print(f"Скачанный размер файла: {downloaded_file_size} байт")
    delimiter = ';'
    if check is True:
        try:
            selected_columns = ['id', 'price'] # Укажите нужные колонки
            for result in pd.read_csv(file_path, sep=delimiter, chunksize=100000, usecols=selected_columns, on_bad_lines='skip'):
                final.append(result)
    # try:
    #     try:
    #         selected_columns = ['id', 'name', 'categoryId', 'price', 'oldprice', 'picture',
    #                             'url']  # Укажите нужные колонки
    #         for result in pd.read_csv(file_path, sep=delimiter, chunksize=10000, usecols=selected_columns, on_bad_lines='skip'):
    #             final.append(result)
    #     except:
    #         selected_columns = ['id', 'name', 'categoryId', 'price', 'picture', 'url']  # Укажите нужные колонки
    #         for result in pd.read_csv(file_path, sep=delimiter, chunksize=10000, usecols=selected_columns, on_bad_lines='skip'):
    #             result['oldprice'] = None
    #             final.append(result)
        except Exception as e:
            print(e)
            try:
                # Читаем файл, пропуская первую строку
                data = pd.read_csv(file_path, sep=';', skiprows=1)

                # Записываем оставшиеся данные обратно в файл
                data.to_csv(file_path, sep=';', index=False)
                selected_columns = ['id', 'price']  # Укажите нужные колонки
                for result in pd.read_csv(file_path, sep=delimiter, chunksize=100000, usecols=selected_columns,
                                          on_bad_lines='skip'):
                    final.append(result)
            except Exception as e:
                print(e)


        finally:
            # Очищаем файл после использования
            # if os.path.exists(file_path):
            #     os.remove(file_path)
            return final
    else:
        return False



# def save_csv(df, file_path):
# selected_columns = ['name', 'categoryId', 'price', 'oldprice', 'picture', 'url']  # Укажите нужные колонки
# df_filtered = df[selected_columns]
# df_filtered.to_csv(file_path, index=False)
# df.to_csv(file_path, index=False)
# print(f"CSV file saved to {file_path}")


def get_csv(feeds, check=True):
    # Замените на URL вашего CSV файла
    final = download_csv(feeds, check=check)

    if check is True:
        full_df = pd.concat(final, ignore_index=True)
        print(len(full_df.values), 'товаров скачено')
        final=[]

        # save_path = 'downloaded_file.csv'
        print('Чтение завершено')
        if full_df is not None:
            # selected_columns = ['id', 'name', 'categoryId', 'price', 'oldprice', 'picture', 'url']
            selected_columns = ['id', 'price']
            return full_df[selected_columns]
        else:
            return None
    else:
        return 'Товары скачаны'


if __name__ == '__main__':
    # csv_url = 'http://export.admitad.com/ru/webmaster/websites/2684875/products/export_adv_products/?user=liubovmikhailova&code=uusaqdxo7m&feed_id=19224&format=csv'  # Замените на URL вашего CSV файла
    # csv_url = 'http://export.admitad.com/ru/webmaster/websites/2684875/products/export_adv_products/?user=liubovmikhailova&code=uusaqdxo7m&feed_id=25654&format=csv'
    # csv_url = 'http://export.admitad.com/webmaster/websites/2684875/products/export_adv_products/?user=liubovmikhailova&code=uusaqdxo7m&feed_id=1950&format=csv'
    # csv_url = 'http://export.admitad.com/ru/webmaster/websites/2684875/products/export_adv_products/?user=liubovmikhailova&code=uusaqdxo7m&feed_id=24254&format=csv'
    # get_csv(csv_url)
    pass





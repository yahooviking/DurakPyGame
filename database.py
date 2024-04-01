import json
import os

# Функция для сохранения данных в файл
def save_data(data):
    file_path = 'data.json'
    with open(file_path, 'w') as file:
        json.dump(data, file)
    print(f"File saved at: {os.path.abspath(file_path)}")


# Функция для загрузки данных из файла
def load_data():
    try:
        with open('data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def add_client(ip, port):
    data = load_data()
    client_data = {
        'ip': ip,
        'port': port,
    }
    data['clients'] = data.get('clients', [])
    data['clients'].append(client_data)
    save_data(data)
import csv #импорт стандартной библиотеки Python для работы с CSV-файлами (Comma-Separated Values — значения, разделённые запятыми).
import json #
import random
import os #Доступ к возможностям ОС, работа с файлами и т. п.
import requests # библиотека  для отправки HTTP-запросов

#функция для чтения строк в файле. возвращаем список словарей с данными объектов.
def read_met_objects(file):
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f) #DictReader - класс из библиотеки csv. reader  это объект DictReader (итератор)
        objects = list(reader) # преобразуем в список 
    print(f"Загружено {len(objects)} объектов")
    return objects
    
def source_painting(objects):
      paintings =[obj for obj in objects  if obj['Classification'] == 'Paintings'] #список для хранения  словарей с данными объектов - картин         
      print (f"Найдено {len(paintings)} картин")
      return paintings

def download_random_painting():

    all_objects = read_met_objects("data\\MetObjects.csv")
    paint_found = source_painting(all_objects)
    # Создаём папку для сохранения (один раз до цикла)
    os.makedirs('paintings', exist_ok=True)

    attempt = 1
    while True:
        random_painting = random.choice(paint_found)
        
        object_id = random_painting.get('Object ID') 
        print("id:", object_id)
       
        url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}" # f-строка  
        
        response = requests.get(url)
        #Отправка HTTP-запроса: метод, который отправляет GET-запрос на сервер.содержит объект ответа со всей информацией от сервера.
        #( status_code headers:  text:  content: url:  elapsed: ). объект класса response библиотеки req. это json строка.
            
        if response.status_code != 200:
            print(f"Ошибка API: {response.status_code}, повторяем попытку\n")
            attempt += 1
            continue
        
        #	Метаданные о картине
       
        data = response.json() #словарь, содерж-й Пары "ключ-значение". метод, который преобразует JSON-строку, полученную от сервера, в структуры данных Python.
        
        image_url = data.get('primaryImage') #URL-адрес основного изображения объекта в формате JPEG -строка. запрос
        if not image_url:
                print("У этой картины нет изображения в API, повторяем попытку")
                attempt += 1
                continue
       
        #  СОХРАНЯЕМ ИЗОБРАЖЕНИЕ
        img_path = os.path.join('paintings', f"{object_id}.jpg") #Склеивание частей пути

        img_response = requests.get(image_url) #JPG (бинарные данные) само изображение

        with open(img_path, 'wb') as img_file: #w-write b -bin
            img_file.write(img_response.content) # записывает эти байты в файл
        
        #  СОХРАНЯЕМ МЕТАДАННЫЕ
        json_path = os.path.join('paintings', f"{object_id}.json")

        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=2) #не заменять не-латинские символы на \uкоды indent=2 — делать отступы для читаемости (pretty-print)
       #функция из модуля json, которая записывает Python-объект в файл в формате JSON.
        return img_path
 

def main1():
    image_path = download_random_painting() 
    

main1()    
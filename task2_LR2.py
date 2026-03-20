import csv #импорт стандартной библиотеки Python для работы с CSV-файлами (Comma-Separated Values — значения, разделённые запятыми).
import json #
import random
import os #Доступ к возможностям ОС, работа с файлами и т. п.
import requests # библиотека  для отправки HTTP-запросов
import numpy as np
import cv2
import time
from typing import Dict, Optional, Tuple, List

#  ПРИВЕДЕНИЕ К ПОЛУТОНОВОМУ 
def rgb_to_grayscale_manual(image):
    """
    Ручное преобразование RGB в полутоновое
    Формула: Y = 0.299*R + 0.587*G + 0.114*B
    """
    """Преобразование B-син G-зел R-кр изображения в градации серого"""
    start = time.time()
    digits = np.array([0.299, 0.587, 0.114], dtype=np.float32).reshape(3, 1, 1)
    channels = np.array([image[:, :, 2], image[:, :, 1], image[:, :, 0]])
    #0-str у высота 1- х ширина 2- цветовые каналы в порядке BGR
    # Суммируем вдоль axis=0 (складываем каналы)
    gray = np.sum(digits * channels, axis=0)
    elapsed = time.time() - start
    print(f"Ручная реализация: {elapsed:.4f} сек")
    return gray


def rgb_to_grayscale_opencv(image):
    """OpenCV реализация"""
    start = time.time()
    result = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elapsed = time.time() - start
    print(f"OpenCV: {elapsed:.4f} сек")
    return result


# - СВЁРТКА С МАСКОЙ 
def convolve_manual(image, kernel):
    
    kernel_height, kernel_width = kernel.shape
    pad_height, pad_width = kernel_height // 2, kernel_width // 2

    # Одноканальное изображение
    if image.ndim == 2:                                         # количество измерений (размерность) массива чбшка
        padded = np.pad(                                        # создаём рамку
            image.astype(np.float32),                           # Преобразуем изображение в числа с плавающей точкой во избежании переполнения
            ((pad_height, pad_height), (pad_width, pad_width)), 
            mode="constant",                                    # 0 заполняем
        )

        windows = np.lib.stride_tricks.sliding_window_view (     # функция создаёт все возможные положения ядра одновременно, 4-мерный массив.
            
            padded, (kernel_height, kernel_width)                # форма (выходная_высота, выходная_ширина, высота_ядра, ширина_ядра)
                                                                 #по умолчанию создает окна по первым двум осям
        )

        output = np.sum(windows * kernel, axis=(-1, -2))        #умножаем каждое  окно на ядро, для  каждого окна сложим все 4 числа в одно
        
        return output

    # Трёх канальное изображение
    elif image.ndim == 3:

        padded = np.pad(
            image, 
            ((pad_height, pad_height), (pad_width, pad_width), (0, 0)),     # не добавлять паддинг по оси каналов
            mode='constant')
        
        windows = np.lib.stride_tricks.sliding_window_view(
            padded, (kernel_height, kernel_width), axis=(0, 1)
        )
        
        result = np.sum(windows * kernel, axis=(3,4))
 
        result = np.clip(result, 0, 255) #Все значения < 0 становятся 0 Все значения > 255 становятся 255 Значения в диапазоне [0,255] остаются без изменений
        
        return result.astype(np.uint8)
    else:
        raise ValueError("Ожидается 2D или 3D изображение (H×W или H×W×C)")


def convolve_opencv(image, kernel):
    """OpenCV свёртка"""
    start = time.time()
    result = cv2.filter2D(image, -1, kernel)        #глубину вых изобр не изм
    elapsed = time.time() - start
    print(f"OpenCV свёртка: {elapsed:.4f} сек")
    return result


# 3. СГЛАЖИВАНИЕ ГАУССОМ 

def gaussian_kernel(size=5, sigma=1.0):
    """Создание ядра Гаусса """
    ax = np.linspace(-size // 2, size // 2, size)
    xx, yy = np.meshgrid(ax, ax)
    # Создаёт две матрицы:
    # xx - повторяет ax по строкам (координаты X)
    # yy - повторяет ax по столбцам (координаты Y)
  
    kernel = np.exp(-(xx ** 2 + yy ** 2) / (2.0 * sigma ** 2))  # Гауссова функция: exp(-r²/(2σ²)) r - квадрат расстояния от центра (0,0)
    return kernel / np.sum(kernel)                              #нормализуем,  Сумма всех элементов становится равна 1



def gaussian_blur_manual(image, size=5, sigma=1.0):
    """Ручное размытие Гауссом"""
    start = time.time()
    kernel = gaussian_kernel(size, sigma)
    result = convolve_manual(image, kernel)
    elapsed = time.time() - start
    print(f"Ручной Гаусс: {elapsed:.4f} сек")
    return result


def gaussian_blur_opencv(image, size=5, sigma=1.0):
    """OpenCV размытие Гауссом"""
    start = time.time()
    result = cv2.GaussianBlur(image, (size, size), sigma)
    elapsed = time.time() - start
    print(f"OpenCV Гаусс: {elapsed:.4f} сек")
    return result


#  ВЫДЕЛЕНИЕ ГРАНИЦ (СОБЕЛЬ) 
def sobel_manual(image):
    """Ручная реализация оператора Собеля"""
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
    start = time.time()
    
    grad_x = convolve_manual(image, sobel_x)
    grad_y = convolve_manual(image, sobel_y)
    
    magnitude = np.sqrt(grad_x.astype(np.float32)**2 + grad_y.astype(np.float32)**2)
    
    elapsed = time.time() - start
    print(f"Ручной Собель: {elapsed:.4f} сек")
    return magnitude


def sobel_opencv(image):
    """OpenCV реализация Собеля"""
    start = time.time()
    
    grad_x = cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3) #1 0 порядок произв по х у 
    grad_y = cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3)
    
    magnitude = cv2.magnitude(grad_x, grad_y)
   
    elapsed = time.time() - start
    print(f"OpenCV Собель: {elapsed:.4f} сек")
    return magnitude 



#  ОСНОВНАЯ ФУНКЦИЯ ОБРАБОТКИ 

def process_image(image_path):
    
    
     #Загружает изображение из файла в виде numpy-массива. image_path: Путь к изображению. возвр Массив пикселей изображения в формате BGR.
    original = cv2.imread(image_path) #uint8 
   
    # Создаём папку для результатов
    output_dir = os.path.join(os.path.dirname(image_path), "processed")
    os.makedirs(output_dir, exist_ok=True)
    
    print("ОБРАБОТКА ИЗОБРАЖЕНИЯ")
    
    # 1. Полутоновое преобразование
    print("\n1. ПРЕОБРАЗОВАНИЕ К ПОЛУТОНОВОМУ:")
    gray_manual = rgb_to_grayscale_manual(original)
    gray_opencv = rgb_to_grayscale_opencv(original)
    gray_uint8 = np.clip(gray_manual, 0, 255).astype(np.uint8)
    gray_opencv8 = np.clip(gray_opencv, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(output_dir, "1_grayscale_manual.jpg"), gray_uint8)
    cv2.imwrite(os.path.join(output_dir, "1_grayscale_opencv.jpg"), gray_opencv8)
    
    
    # 2. Свёртка    
    print("\n2. СВЁРТКА С МАСКОЙ ПОВЫШЕНИЯ РЕЗКОСТИ:")
    kernel = np.array([
    [0, -1, 0],
    [-1, 5, -1],
    [0, -1, 0]] , dtype=np.float32)
    #Влияет только на вертикальные и горизонтальные соседей
    start = time.time()
    manual = convolve_manual(original, kernel)
    elapsed = time.time() - start
    print(f"ручная свёртка: {elapsed:.4f} сек")

    opencv = convolve_opencv(original, kernel)

    result_uint8 = np.clip(manual, 0, 255).astype(np.uint8)
    opencv8 = np.clip(opencv, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(output_dir, "2_conv_sharpen_manual.jpg"), result_uint8)
    cv2.imwrite(os.path.join(output_dir, "2_conv_sharpen_opencv.jpg"), opencv8)
   
    
    
    # 3. Сглаживание Гауссом
    print("\n3. СГЛАЖИВАНИЕ ГАУССОМ:")
    gauss_manual = gaussian_blur_manual(original)
    gauss_opencv = gaussian_blur_opencv(original)

    gauss_uint8 = np.clip(gauss_manual, 0, 255).astype(np.uint8)
    opencv_uint8 = np.clip(gauss_opencv, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(output_dir, "3_gauss_manual.jpg"), gauss_uint8)
    cv2.imwrite(os.path.join(output_dir, "3_gauss_opencv.jpg"), opencv_uint8)
    
    # 4. Выделение границ (Собель)
    print("\n4. ВЫДЕЛЕНИЕ ГРАНИЦ (СОБЕЛЬ):")
    sobel_manual_result = sobel_manual(original)
    sobel_opencv_result = sobel_opencv(original)

    sobel_manual8 = np.clip(sobel_manual_result, 0, 255).astype(np.uint8)
    sobel_opencv8 = np.clip(sobel_opencv_result, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(output_dir, "4_sobel_manual.jpg"),  sobel_manual8 )
    cv2.imwrite(os.path.join(output_dir, "4_sobel_opencv.jpg"), sobel_opencv8)
    
    
    

def main():
    
    image_path = "paintings/437509.jpg"
    process_image(image_path)
    

main()    
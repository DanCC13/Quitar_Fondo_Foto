# Version 1.6 Desarrollado por Daniel Campana y Joaquín Pozo
# Version 1.3. Desarrollado por Natalia Escudero y Angela Anhuamán
# Innovaciones: Soporte para subir múltiples archivos o carpetas, descarga individual o en archivo comprimido (.zip).
# Trabajas 

# -------------------------------------------------- Importacion de librerias --------------------------------------------------

import streamlit as st
from rembg import remove, new_session
from PIL import Image
from io import BytesIO
import zipfile
import tkinter as tk
from tkinter import filedialog
import os

# -------------------------------------------------- Codigo Principal --------------------------------------------------
session = new_session("u2net_human_seg") # Define que modelo de IA se va a utilizar

def create_zip_file(images, zip_filename, names): # Funcion que crea un archivo .zip.
    # Parametros: images (Lista de imagenes), zip_filename (Nombre para el archivo), names(Lista con los nombres de los archivos a incluir)
    
    zip_buffer = BytesIO() # Objeto que almacena bytes de memoria
    try:
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file: # Abre el archivo .zip en modo escritura
            for i, img in enumerate(images):
                img_bytes = BytesIO() # Objeto que almacena el contenido de las imagenes creadas
                img.save(img_bytes, format='PNG') # Guarda las imagenes en formato .png
                img_bytes.seek(0) # Se vuelve la escritura del fichero al inicio de la lista
                
                filename = names[i] # Define el nombre del archivo
                zip_file.writestr(filename, img_bytes.getvalue()) # Crea y almacena la imagen en el fichero .zip con el nombre y bytes establecidos
                
        with open(zip_filename, 'wb') as f: # Se crea y abre el archivo .zip final en modo escritura binaria
            f.write(zip_buffer.getvalue())  # Ingresa los datos almacenados en el .zip creado anteriormente y lo guarda con el nombre elegido
    except OSError as e:
        print("Error en OS:", e) # Manejo de errores
    except ValueError:
        print("No se pudo crear el archivo .ZIP") # Manejo de errores

def resize_image(img, target_width, target_height):
    width, height = img.size # Obtiene las dimensiones de la imagen
    original_aspect_ratio = width / height # Guarda la relacion de las dimensiones de la imagen
    target_aspect_ratio = target_width / target_height # Obtiene las dimensiones de la imagen a la que se desea convertir

    if original_aspect_ratio > target_aspect_ratio:
        # La imagen es más ancha que alta
        new_width = int(target_height * original_aspect_ratio)
        resized_img = img.resize((new_width, target_height), Image.BICUBIC)
        x_offset = (new_width - target_width) // 2
        resized_img = resized_img.crop((x_offset, 0, x_offset + target_width, target_height))
    else:
        # La imagen es más alta que ancha
        new_height = int(target_width / original_aspect_ratio)
        resized_img = img.resize((target_width, new_height), Image.BICUBIC)
        y_offset = (new_height - target_height) // 2
        resized_img = resized_img.crop((0, y_offset, target_width, y_offset + target_height))

    return resized_img, target_width, target_height

def img_remover(files, set, dirname, dpi): # Funcion que quita el fondo de las imagenes y las guarda en formato .png
    # Parametros: files (Archivo o archivos subidos), set (1 si es para archivos, 0 si es para carpetas)
    names = [] # Lista que contendra los nombres de los archivos
    images = [] # Lista que almacenara las imagenes editadas
    total_files = [] #Lista en set == '1' la cual almacenará todas las imágenes

    if set == '0':
        for root, dirs, files in os.walk(dirname): # Busca dentro de la carpeta todas las subcarpetas y subcarpetas dentro de esta y se ejecuta por cada una
            for file in files: # Por cada archivo encontrado
                if file.endswith(('.png', '.jpg', '.jpeg', '.jfif', '.tif', '.webp')): # Comprueba que el archivo sea del formato aceptado
                    total_files.append(os.path.join(root, file)) # Si el archivo es compatible, lo anexa al folder de imagenes a editar
    else: # Si se selecciono un archivo
        for file in files: # Primero se recorre por toda la lista para encontrar archivos .zip
            if file.name.endswith('.zip'): # Si se encuentra
                with zipfile.ZipFile(file) as z:
                    # Se obtiene la lista de nombres
                    file_names = z.namelist()
                    # Se filtran solo los archivos deseados
                    for file_name in file_names:
                        if file_name.endswith(('.png', '.jpg', '.jpeg', '.jfif', '.tif', '.webp')): # Comprueba que el archivo sea del formato aceptado
                            with z.open(file_name) as img_file:
                                img_bytes = BytesIO(img_file.read()) # Se guarda el archivo
                                img_bytes.name = file_name  # Agregamos nombre del archivo
                                total_files.append(img_bytes) # Se guarda el archivo en la lista
            else:
                # Los archivos de imagen simplemente se guardan 
                img_bytes = BytesIO(file.read())
                img_bytes.name = file.name  # Agregar el nombre del archivo como atributo
                total_files.append(img_bytes)
          
    for file in total_files: # Se ejecuta archivo por archivo
        if set == '1':
            img = Image.open(file) # Si se sube un archivo o archivos, se abre solo con el nombre del archivo
            names.append(file.name.split(".")[0] + '.png') # Se incluye en nombre del archivo
        elif set == '0':
            path = os.path.join(dirname, file) # Si se sube una carpeta, se define la ruta de los archivos
            img = Image.open(path) # Se abren los archivos
            names.append(file.split(".")[0] + '.png')  # Se incluye en nombre del archivo
        img2 = remove(img, bgcolor=(255,255,255,255), session=session) # Remueve el fondo de la imagen

    # Ajustando el tamaño simétricamente con las dimensiones específicas
       # Desempaquetar los valores devueltos por resize_image
        resized_img, new_width, new_height = resize_image(img2, 244, 288)

    # Reemplazar img3 con la imagen redimensionada
        img3 = resized_img

    # Tamaño del archivo
        quality = 95
        max_size_kb = 50 * 1024  #Resolucion de 50kB
            
        images.append(img3) # Se adiciona la imagen creada a la lista de imagenes 
        st.image(img3) # Muestra la imagen en la interfaz
        buf = BytesIO() # Objeto que permite almacenar el contenido de las imagenes
        img3.save(buf, format='png') # Guardar las imagenes en formato .png

    if len(total_files) == 1:
        st.download_button("Descargar", data=buf, file_name=names[0], mime="image/png") # Si la imagen solo es una se descarga directamente
    else: # Si es mas de una imagen se descarga en un archivo .zip
        # Parte ZIP
        zip_filename = "Imagenes.zip" # Nombre del archivo .zip
        create_zip_file(images, zip_filename, names) # Crea el archivo.zip

        with open(zip_filename, 'rb') as f: # Abre el archivo .zip en modo lectura binaria
            zip_data = f.read() # Carga y guarda el contenido del archivo .zip

        st.download_button(
            label="Descargar Archivo ZIP", data=zip_data, file_name=zip_filename, mime="application/zip"
        ) # Muestra en la interfaz un boton para descargar el archivo en un .zip


def main():
    try:
        st.title("Quitar fondo") # Titulo del programa
        files = st.file_uploader("Seleccione una o varias imagenes", accept_multiple_files=True, type=["png","jpg","jpeg", "tif", "webp", "zip"]) # Crea un boton para subir uno o varios archivos
        st.write("O seleccione una carpeta")# Da la opcion de subir una carpeta entera
        root = tk.Tk() # Crea una ventana en Tkinter (No se puede adjuntar en Streamlit carpetas enteras, asi que este es un metodo para lograrlo)
        root.withdraw() # Oculta la ventana
        root.wm_attributes('-topmost', 1) # Superpone la ventana sobre cualquier otro programa
        boton_carpeta = st.button('Buscar Carpeta') # Crea un boton que permita adjuntar una carpeta 
    except ValueError:
        print('No se pudo cargar el Streamlit correctamente') # Manejo de errores
    if files:
        img_remover(files, '1', None, 300) # Abrir los archivos y ejecutar las funcion segun los parametros necesarios
    elif boton_carpeta:
        dirname = str(filedialog.askdirectory(master=root)) # Obtener la ruta de la carpeta subida
        img_remover(os.listdir(dirname), '0', dirname, 300) # Abrir la carpeta y ejecutar las funcion segun los parametros necesario

if __name__ == "__main__":
    main()

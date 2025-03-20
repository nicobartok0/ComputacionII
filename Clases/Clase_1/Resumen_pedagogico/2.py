import argparse

parser = argparse.ArgumentParser(description="Ejercicio de parseo Computación II UM 2025 Nicolás Bartolomeo")

# Archivo de entrada en parseador
parser.add_argument("archivo_entrada", help="Archivo de entrada para el programa")

# Archivo de salida en parseador
parser.add_argument("archivo_salida", help="Archivo de salida para el programa")

# Opción uppercase
parser.add_argument("-u", "--uppercase", action="store_true", help="Convierte todo en mayúscula")

# Parseamos los argumentos
args = parser.parse_args()

with open(args.archivo_entrada, "r") as archivo:
    if args.uppercase:
        contenido = archivo.read()
        with open(args.archivo_salida, "w") as salida:
            salida.write(contenido.upper())
    else:
        contenido = archivo.read()
        with open(args.archivo_salida, "w") as salida:
            salida.write(contenido)

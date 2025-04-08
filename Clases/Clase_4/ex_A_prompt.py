import os

# Creamos los dos pipes
pipe1_lectura, pipe1_escritura = os.pipe()  # Padre → Hijo1
pipe2_lectura, pipe2_escritura = os.pipe()  # Hijo1 → Hijo2

pid1 = os.fork()

if pid1 == 0:
    # === Hijo1 ===
    os.close(pipe1_escritura)  # Cierra lo que no usa
    os.close(pipe2_lectura)

    # Lee del padre
    mensaje = os.read(pipe1_lectura, 1024).decode()
    mayusculas = mensaje.upper()

    # Escribe al Hijo2
    os.write(pipe2_escritura, mayusculas.encode())

    # Cierra los extremos que usó
    os.close(pipe1_lectura)
    os.close(pipe2_escritura)

else:
    pid2 = os.fork()

    if pid2 == 0:
        # === Hijo2 ===
        os.close(pipe1_lectura)
        os.close(pipe1_escritura)
        os.close(pipe2_escritura)

        # Lee de Hijo1
        mensaje = os.read(pipe2_lectura, 1024).decode()
        invertido = mensaje[::-1]
        print(f"Hijo2 recibió y transformó: {invertido}")

        os.close(pipe2_lectura)

    else:
        # === Padre ===
        os.close(pipe1_lectura)
        os.close(pipe2_lectura)
        os.close(pipe2_escritura)

        texto = "hola mundo"
        os.write(pipe1_escritura, texto.encode())
        os.close(pipe1_escritura)

        # Esperamos que los hijos terminen
        os.wait()
        os.wait()

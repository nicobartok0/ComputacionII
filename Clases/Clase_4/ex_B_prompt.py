import os

# Creamos los dos pipes
padre_a_hijo_r, padre_a_hijo_w = os.pipe()
hijo_a_padre_r, hijo_a_padre_w = os.pipe()

pid = os.fork()

if pid == 0:
    # === Hijo ===
    os.close(padre_a_hijo_w)  # No escribe al padre
    os.close(hijo_a_padre_r)  # No lee del padre

    # Lee el mensaje del padre
    mensaje = os.read(padre_a_hijo_r, 1024).decode()
    print(f"Hijo recibió: {mensaje}")

    respuesta = f"Recibido: {mensaje}"
    os.write(hijo_a_padre_w, respuesta.encode())

    # Cierre
    os.close(padre_a_hijo_r)
    os.close(hijo_a_padre_w)

else:
    # === Padre ===
    os.close(padre_a_hijo_r)  # No lee lo que él mismo escribe
    os.close(hijo_a_padre_w)  # No escribe al hijo

    # Enviar mensaje al hijo
    texto = "¿Todo bien por allá?"
    os.write(padre_a_hijo_w, texto.encode())

    # Leer respuesta del hijo
    respuesta = os.read(hijo_a_padre_r, 1024).decode()
    print(f"Padre recibió: {respuesta}")

    # Cierre
    os.close(padre_a_hijo_w)
    os.close(hijo_a_padre_r)

    # Esperamos que el hijo termine
    os.wait()

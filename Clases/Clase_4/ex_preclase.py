import os

# Creamos el pipe ANTES del fork
read_fd, write_fd = os.pipe()

# Ahora creamos el proceso hijo
pid = os.fork()

if pid == 0:
    # Proceso hijo
    os.close(write_fd)  # Cerramos el extremo que no se usa
    print("Soy el hijo")
    mensaje = os.read(read_fd, 1024)
    print(f"Mensaje leído! el mensaje es: {mensaje.decode()}")
    os.close(read_fd)
else:
    # Proceso padre
    os.close(read_fd)  # Cerramos el extremo que no se usa
    os.write(write_fd, b"Hola hijo")
    print("Soy el padre")
    os.close(write_fd)
    os.wait()

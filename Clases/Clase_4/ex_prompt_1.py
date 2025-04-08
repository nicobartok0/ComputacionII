import os

lectura, escritura = os.pipe()
pid = os.fork()

if pid > 0:
    os.close(lectura)
    mensaje = b"Hola desde el padre"
    os.write(escritura, mensaje)
    os.close(escritura)
else:
    os.close(escritura)
    recibido = os.read(lectura, 1024)
    print(f"Hijo recibió: {recibido.decode()}")
    os.close(lectura)

from multiprocessing import Process, Pipe, Queue, Event
from collections import deque
from datetime import datetime
import time
import random
import statistics
import os
import sys
import hashlib
import json

# --- Configuración ---
NUM_SAMPLES = 60  # total de paquetes a generar
WINDOW_SIZE = 30  # ventana móvil para cada analizador (en muestras)
SLEEP_SEC = 1     # periodo entre paquetes

# Rangos para generar datos
FREQ_RANGE = (60, 180)
PRESS_SYST_RANGE = (110, 180)
PRESS_DIA_RANGE = (70, 110)
OXY_RANGE = (90, 100)

# Tipos de analizadores
TYPES = ("frecuencia", "presion", "oxigeno")


def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def generador(parent_conns, stop_event: Event):
    """Genera NUM_SAMPLES paquetes y los envia por cada parent_conn (list de conexiones)."""
    try:
        for i in range(NUM_SAMPLES):
            paquete = {
                "timestamp": now_iso(),
                "frecuencia": random.randint(*FREQ_RANGE),
                "presion": [random.randint(*PRESS_SYST_RANGE), random.randint(*PRESS_DIA_RANGE)],
                "oxigeno": random.randint(*OXY_RANGE),
            }

            # enviar a cada analizador por su pipe
            for conn in parent_conns:
                conn.send(paquete)

            # informacion de traza
            print(f"[Generador] paquete {i+1}/{NUM_SAMPLES} generado: {paquete}")

            time.sleep(SLEEP_SEC)

        # Senal de finalizacion: enviar None por cada pipe
        for conn in parent_conns:
            try:
                conn.send(None)
            except Exception:
                pass

    finally:
        # Indicar que terminamos
        stop_event.set()
        print("[Generador] terminado y stop_event seteado.")


def analizador_proc(tipo: str, child_conn, result_queue: Queue, stop_event: Event):
    window = deque(maxlen=WINDOW_SIZE)
    conn = child_conn

    try:
        while True:
            paquete = None
            try:
                paquete = conn.recv()
            except EOFError:
                # pipe cerrado por el otro extremo
                break

            if paquete is None:
                # senal de finalizacion
                print(f"[Analizador:{tipo}] recibido sentinel None. Saliendo.")
                break

            # extraer se\u00f1al segun tipo
            if tipo == "frecuencia":
                value = paquete.get("frecuencia")
            elif tipo == "presion":
                pres = paquete.get("presion")
                # Elegimos la sistolica (indice 0) como la se\u00f1al a analizar
                value = pres[0]
            elif tipo == "oxigeno":
                value = paquete.get("oxigeno")
            else:
                value = None

            # anadir a la ventana
            window.append(value)

            # calcular estadisticas de la ventana actual
            # si hay al menos un valor
            if len(window) > 0:
                media = float(statistics.mean(window))
                # pstdev = desviacion poblacional (ddof=0)
                desv = float(statistics.pstdev(window))
            else:
                media = 0.0
                desv = 0.0

            resultado = {
                "tipo": tipo,
                "timestamp": paquete.get("timestamp"),
                "media": media,
                "desv": desv,
            }

            # poner el resultado en la cola hacia el verificador
            result_queue.put(resultado)

            # traza corta
            print(f"[Analizador:{tipo}] {resultado}")

    except Exception as e:
        print(f"[Analizador:{tipo}] Excepcion: {e}")

    finally:
        try:
            conn.close()
        except Exception:
            pass
        print(f"[Analizador:{tipo}] finalizado.")



def verificador_proc(result_queue: Queue, stop_event: Event):
    buffer = {}  # timestamp -> dict(tipo -> result)
    blockchain = []
    prev_hash = "0"
    bloque_index = 0

    while True:
        if stop_event.is_set() and result_queue.empty():
            print("[Verificador] stop_event seteado y cola vacia. Saliendo.")
            break

        try:
            res = result_queue.get(timeout=1)
        except Exception:
            continue

        if res is None:
            print("[Verificador] recibido sentinel None en la cola. Saliendo.")
            break

        t = res.get("timestamp")
        tipo = res.get("tipo")

        if t is None or tipo is None:
            continue

        buffer.setdefault(t, {})[tipo] = res

        if all(k in buffer[t] for k in TYPES):
            datos = {
                "frecuencia": {"media": buffer[t]["frecuencia"]["media"], "desv": buffer[t]["frecuencia"]["desv"]},
                "presion": {"media": buffer[t]["presion"]["media"], "desv": buffer[t]["presion"]["desv"]},
                "oxigeno": {"media": buffer[t]["oxigeno"]["media"], "desv": buffer[t]["oxigeno"]["desv"]},
            }

            alerta = False
            if datos["frecuencia"]["media"] >= 200:
                alerta = True
            if not (90 <= datos["oxigeno"]["media"] <= 100):
                alerta = True
            if datos["presion"]["media"] >= 200:
                alerta = True

            # Generar hash del bloque
            contenido = prev_hash + str(datos) + t
            hash_bloque = hashlib.sha256(contenido.encode()).hexdigest()

            bloque = {
                "timestamp": t,
                "datos": datos,
                "alerta": alerta,
                "prev_hash": prev_hash,
                "hash": hash_bloque
            }

            blockchain.append(bloque)
            prev_hash = hash_bloque

            # Guardar blockchain en disco
            with open("blockchain.json", "w") as f:
                json.dump(blockchain, f, indent=2)

            print(f"[Verificador] Bloque {bloque_index}: hash={hash_bloque} alerta={alerta}")
            bloque_index += 1

            del buffer[t]

    print("[Verificador] terminado.")


def main():
    # pipes: para cada analizador creamos un Pipe()
    parent_conns = []
    child_conns = []
    for _ in range(3):
        parent_conn, child_conn = Pipe()
        parent_conns.append(parent_conn)
        child_conns.append(child_conn)

    # cola compartida Analizadores -> Verificador
    result_queue = Queue()

    # evento de parada global
    stop_event = Event()

    # crear procesos analizadores
    analizadores = []
    for i, tipo in enumerate(TYPES):
        p = Process(target=analizador_proc, args=(tipo, child_conns[i], result_queue, stop_event), name=f"Analizador-{tipo}")
        p.start()
        analizadores.append(p)

    # crear verificador
    verificador = Process(target=verificador_proc, args=(result_queue, stop_event), name="Verificador")
    verificador.start()

    # ejecutar generador en el proceso principal (no en proceso separado para simplicidad)
    try:
        generador(parent_conns, stop_event)
    except KeyboardInterrupt:
        print("[Main] Interrumpido por teclado. Seteando stop_event.")
        stop_event.set()

    # cerrar extremos padres de pipes en main
    for conn in parent_conns:
        try:
            conn.close()
        except Exception:
            pass

    # esperar que analizadores finalicen
    for p in analizadores:
        p.join(timeout=5)
        if p.is_alive():
            print(f"[Main] Analizador {p.name} sigue vivo. Terminando...")
            p.terminate()
            p.join()

    # ahora que los analizadores terminaron, garantizar que el verificador salga:
    # ponemos un sentinel None en la cola
    result_queue.put(None)

    # esperar verificador
    verificador.join(timeout=5)
    if verificador.is_alive():
        print("[Main] Verificador sigue vivo. Terminando...")
        verificador.terminate()
        verificador.join()

    print("[Main] Finalizado correctamente.")



if __name__ == '__main__':
    main()

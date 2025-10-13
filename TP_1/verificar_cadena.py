import json
import hashlib

def calcular_hash(prev_hash, datos, timestamp):
    contenido = prev_hash + str(datos) + timestamp
    return hashlib.sha256(contenido.encode()).hexdigest()

def verificar_cadena(file_path="blockchain.json", reporte_path="reporte.txt"):
    try:
        with open(file_path, "r") as f:
            blockchain = json.load(f)
    except Exception as e:
        print(f"Error leyendo {file_path}: {e}")
        return

    total_bloques = len(blockchain)
    bloques_alerta = 0

    suma_freq = 0.0
    suma_pres = 0.0
    suma_oxi = 0.0

    # Para calcular promedios, contaremos cuántos bloques aportan
    count_freq = 0
    count_pres = 0
    count_oxi = 0

    bloque_anterior_hash = "0"
    corrupcion_detectada = False

    for i, bloque in enumerate(blockchain):
        prev_hash = bloque.get("prev_hash")
        timestamp = bloque.get("timestamp")
        datos = bloque.get("datos")
        hash_actual = bloque.get("hash")
        alerta = bloque.get("alerta", False)

        # Verificar encadenamiento de hashes
        if prev_hash != bloque_anterior_hash:
            print(f"Corrupción en bloque {i}: prev_hash no coincide.")
            corrupcion_detectada = True

        # Recalcular hash
        hash_recalculado = calcular_hash(prev_hash, datos, timestamp)
        if hash_actual != hash_recalculado:
            print(f"Corrupción en bloque {i}: hash incorrecto.")
            corrupcion_detectada = True

        bloque_anterior_hash = hash_actual

        if alerta:
            bloques_alerta += 1

        # Sumar para promedios
        if datos:
            if "frecuencia" in datos and "media" in datos["frecuencia"]:
                suma_freq += datos["frecuencia"]["media"]
                count_freq += 1
            if "presion" in datos and "media" in datos["presion"]:
                suma_pres += datos["presion"]["media"]
                count_pres += 1
            if "oxigeno" in datos and "media" in datos["oxigeno"]:
                suma_oxi += datos["oxigeno"]["media"]
                count_oxi += 1

    # Calcular promedios
    promedio_freq = suma_freq / count_freq if count_freq > 0 else 0
    promedio_pres = suma_pres / count_pres if count_pres > 0 else 0
    promedio_oxi = suma_oxi / count_oxi if count_oxi > 0 else 0

    # Crear reporte
    with open(reporte_path, "w") as f:
        f.write("Reporte de Verificación de Cadena de Bloques\n")
        f.write("===========================================\n\n")
        f.write(f"Cantidad total de bloques: {total_bloques}\n")
        f.write(f"Número de bloques con alerta: {bloques_alerta}\n")
        f.write(f"Promedio general de frecuencia: {promedio_freq:.2f}\n")
        f.write(f"Promedio general de presión sistólica: {promedio_pres:.2f}\n")
        f.write(f"Promedio general de oxígeno: {promedio_oxi:.2f}\n\n")

        if corrupcion_detectada:
            f.write("Se detectaron bloques corruptos en la cadena.\n")
            print("Se detectaron bloques corruptos en la cadena.")
        else:
            f.write("No se detectaron corrupciones en la cadena.\n")
            print("Cadena verificada sin corrupciones.")

    print(f"Reporte generado en {reporte_path}")

if __name__ == "__main__":
    verificar_cadena()

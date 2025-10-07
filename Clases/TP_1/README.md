**Sistema Concurrente de Análisis Biométrico con Cadena de Bloques Local**

Este proyecto implementa un sistema concurrente en Python que simula la captura y análisis de datos biométricos en tiempo real y almacena resultados validados en una cadena de bloques local para garantizar la integridad.
Estructura del proyecto

    biometria_task1.py — Script principal que:

        Genera datos biométricos simulados (frecuencia cardíaca, presión arterial y oxígeno).

        Procesa datos en paralelo con procesos analizador.

        Verifica y construye bloques con hash encadenado.

        Guarda la cadena de bloques en blockchain.json.

    verificar_cadena.py — Script externo que:

        Verifica la integridad del archivo blockchain.json.

        Genera un reporte en reporte.txt con estadísticas y alertas.

Requisitos

    Python 3.9 o superior

    Librerías estándar (multiprocessing, json, hashlib, datetime, etc.)
# TP2 - Sistema de Scraping y Análisis Web Distribuido

Sistema distribuido de scraping y análisis web que utiliza Python con asyncio y multiprocessing. El sistema consta de dos servidores que trabajan de forma coordinada.

## Arquitectura

- **Servidor A (asyncio)**: Maneja solicitudes HTTP de scraping de forma asíncrona
- **Servidor B (multiprocessing)**: Procesa tareas computacionalmente intensivas en paralelo
- **Cliente**: Interactúa únicamente con el Servidor A (transparencia de distribución)

## Requisitos

- Python 3.8 o superior
- Chrome/Chromium instalado (para screenshots)
- ChromeDriver instalado y en el PATH

## Instalación

1. Clonar el repositorio y navegar a la carpeta TP2:

```bash
cd TP2
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Instalar ChromeDriver:

En Ubuntu/Debian:
```bash
sudo apt-get install chromium-chromedriver
```

En macOS:
```bash
brew install chromedriver
```

En Windows: Descargar desde https://chromedriver.chromium.org/

## Uso

### Iniciar el Servidor de Procesamiento (Parte B)

Primero, iniciar el servidor de procesamiento:

```bash
python server_processing.py -i 127.0.0.1 -p 8001
```

Opciones:
- `-i, --ip`: Dirección de escucha (requerido)
- `-p, --port`: Puerto de escucha (requerido)
- `-n, --processes`: Número de procesos en el pool (default: número de CPUs)

### Iniciar el Servidor de Scraping (Parte A)

En otra terminal, iniciar el servidor principal:

```bash
python server_scraping.py -i 127.0.0.1 -p 8000
```

Opciones:
- `-i, --ip`: Dirección de escucha - soporta IPv4/IPv6 (requerido)
- `-p, --port`: Puerto de escucha (requerido)
- `-w, --workers`: Número de workers asíncronos (default: 4)
- `--processing-host`: Host del servidor de procesamiento (default: 127.0.0.1)
- `--processing-port`: Puerto del servidor de procesamiento (default: 8001)

### Usar el Cliente

Para scrapear una URL:

```bash
python client.py https://example.com
```

Opciones:
- `url`: URL a scrapear (requerido)
- `--host`: Host del servidor (default: 127.0.0.1)
- `--port`: Puerto del servidor (default: 8000)
- `--timeout`: Timeout en segundos (default: 60)
- `--json`: Imprimir resultado como JSON

Ejemplos:

```bash
# Scrapear con salida formateada
python client.py https://python.org

# Scrapear con salida JSON
python client.py https://python.org --json

# Especificar servidor diferente
python client.py https://example.com --host 192.168.1.100 --port 9000

# Con timeout personalizado
python client.py https://example.com --timeout 120
```

## Estructura del Proyecto

```
TP2/
├── server_scraping.py          # Servidor asyncio (Parte A)
├── server_processing.py        # Servidor multiprocessing (Parte B)
├── client.py                   # Cliente de prueba
├── scraper/
│   ├── __init__.py
│   ├── html_parser.py          # Parsing de HTML
│   ├── metadata_extractor.py  # Extracción de metadatos
│   └── async_http.py           # Cliente HTTP asíncrono
├── processor/
│   ├── __init__.py
│   ├── screenshot.py           # Generación de screenshots
│   ├── performance.py          # Análisis de rendimiento
│   └── image_processor.py      # Procesamiento de imágenes
├── common/
│   ├── __init__.py
│   └── protocol.py             # Protocolo de comunicación
├── requirements.txt
└── README.md
```

## Funcionalidades

### Servidor de Scraping (Parte A)

- Manejo asíncrono de múltiples solicitudes concurrentes
- Extracción de contenido HTML sin bloquear el event loop
- Obtención de:
  - Título de la página
  - Enlaces (links)
  - Meta tags (description, keywords, Open Graph)
  - Estructura de headers (H1-H6)
  - Contador de imágenes
- Comunicación asíncrona con el servidor de procesamiento
- Consolidación de resultados

### Servidor de Procesamiento (Parte B)

- Pool de procesos para procesamiento paralelo
- Generación de screenshots de páginas web
- Análisis de rendimiento:
  - Tiempo de carga
  - Tamaño total de recursos
  - Número de requests
- Procesamiento de imágenes:
  - Descarga de imágenes principales
  - Generación de thumbnails optimizados

### Comunicación

- Protocolo binario eficiente basado en sockets TCP
- Serialización JSON con header de longitud
- Manejo robusto de errores y timeouts
- Soporte IPv4 e IPv6

## Formato de Respuesta

El servidor devuelve un JSON con la siguiente estructura:

```json
{
  "url": "https://example.com",
  "timestamp": "2024-11-10T15:30:00Z",
  "scraping_data": {
    "title": "Título de la página",
    "links": ["url1", "url2"],
    "meta_tags": {
      "description": "...",
      "keywords": "..."
    },
    "structure": {
      "h1": 2,
      "h2": 5
    },
    "images_count": 15
  },
  "processing_data": {
    "screenshot": "base64_encoded_image",
    "performance": {
      "load_time_ms": 1250,
      "total_size_kb": 2048,
      "num_requests": 45
    },
    "thumbnails": ["base64_thumb1", "base64_thumb2"]
  },
  "status": "success"
}
```

## Manejo de Errores

El sistema maneja los siguientes casos de error:

- URLs inválidas o inaccesibles
- Timeouts en scraping (máximo 30 segundos por página)
- Errores de comunicación entre servidores
- Recursos no disponibles
- Páginas demasiado grandes (límite 10MB)

## Notas Técnicas

- El servidor A utiliza `asyncio` y `aiohttp` para operaciones I/O no bloqueantes
- El servidor B utiliza `multiprocessing` para paralelizar tareas CPU-bound
- La comunicación entre servidores es asíncrona desde la perspectiva del servidor A
- Los screenshots se generan en modo headless para eficiencia
- Las imágenes se procesan con límites de tamaño para evitar sobrecarga de memoria

## Limitaciones

- Los screenshots requieren ChromeDriver instalado
- El procesamiento de imágenes está limitado a 3 imágenes por página
- El tamaño máximo de descarga es 10MB para HTML y 5MB para imágenes
- Los timeouts están configurados en 30 segundos para scraping y 15 segundos para screenshots

## Troubleshooting

### ChromeDriver no encontrado

Si aparece un error relacionado con ChromeDriver:

1. Verificar que ChromeDriver esté instalado: `chromedriver --version`
2. Agregar ChromeDriver al PATH del sistema
3. Alternativamente, especificar la ruta en `screenshot.py`

### Error de conexión entre servidores

Si el servidor A no puede conectarse al servidor B:

1. Verificar que el servidor B esté corriendo
2. Verificar que los puertos no estén bloqueados por firewall
3. Verificar que las direcciones IP/puertos sean correctas

### Timeout en scraping

Si las páginas tardan mucho en cargar:

1. Aumentar el timeout del cliente: `--timeout 120`
2. Verificar la conexión a internet
3. Algunas páginas con mucho JavaScript pueden tardar más
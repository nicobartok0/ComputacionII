# Guía de Uso Rápida

## Instalación y Configuración

### 1. Preparar el entorno

```bash
# Crear directorio del proyecto
mkdir TP2
cd TP2

# Copiar todos los archivos del proyecto aquí
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Verificar ChromeDriver

```bash
# Verificar que esté instalado
chromedriver --version

# Si no está instalado:
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# macOS
brew install chromedriver

# Windows: descargar de https://chromedriver.chromium.org/
```

## Ejecución

### Paso 1: Iniciar el Servidor de Procesamiento

En una terminal:

```bash
python server_processing.py -i 127.0.0.1 -p 8001
```

Deberías ver:
```
Servidor de Procesamiento iniciado en 127.0.0.1:8001
Procesos en el pool: 8
Esperando conexiones...
```

### Paso 2: Iniciar el Servidor de Scraping

En otra terminal:

```bash
python server_scraping.py -i 127.0.0.1 -p 8000
```

Deberías ver:
```
Servidor de Scraping iniciado en 127.0.0.1:8000
Workers asíncronos: 4
Servidor de procesamiento: 127.0.0.1:8001
```

### Paso 3: Usar el Cliente

En una tercera terminal:

```bash
python client.py https://example.com
```

## Ejemplos de Uso

### Ejemplo 1: Scraping básico

```bash
python client.py https://python.org
```

### Ejemplo 2: Con salida JSON

```bash
python client.py https://example.com --json > resultado.json
```

### Ejemplo 3: Con timeout personalizado

```bash
python client.py https://github.com --timeout 120
```

### Ejemplo 4: Servidor en otra máquina

```bash
# En el servidor
python server_scraping.py -i 0.0.0.0 -p 8000

# En el cliente
python client.py https://example.com --host 192.168.1.100 --port 8000
```

### Ejemplo 5: IPv6

```bash
python server_scraping.py -i ::1 -p 8000
```

## Prueba Rápida con el Script de Test

```bash
chmod +x test_system.sh
./test_system.sh
```

Esto iniciará ambos servidores, ejecutará pruebas y los detendrá automáticamente.

## Verificación de que todo funciona

1. El Servidor de Procesamiento debe mostrar "Esperando conexiones..."
2. El Servidor de Scraping debe mostrar las direcciones de escucha
3. El cliente debe poder hacer health check:
   ```bash
   curl http://127.0.0.1:8000/health
   ```
   Respuesta esperada: `{"status": "healthy"}`

## Detener los Servidores

Presionar `Ctrl+C` en cada terminal donde estén corriendo los servidores.

## Solución de Problemas Comunes

### Error: "ModuleNotFoundError"

```bash
# Instalar dependencias faltantes
pip install -r requirements.txt
```

### Error: "ChromeDriver not found"

```bash
# Verificar PATH
echo $PATH

# Instalar ChromeDriver
sudo apt-get install chromium-chromedriver
```

### Error: "Connection refused" entre servidores

1. Verificar que el Servidor B esté corriendo primero
2. Verificar puertos con: `netstat -tulpn | grep 800`
3. Verificar firewall si están en máquinas diferentes

### Los screenshots no se generan

1. Verificar que Chrome/Chromium esté instalado
2. Verificar que ChromeDriver coincida con la versión de Chrome
3. Verificar logs del servidor de procesamiento

## Estructura de Archivos Requerida

```
TP2/
├── server_scraping.py
├── server_processing.py
├── client.py
├── requirements.txt
├── README.md
├── USAGE.md
├── test_system.sh
├── scraper/
│   ├── __init__.py
│   ├── html_parser.py
│   ├── metadata_extractor.py
│   └── async_http.py
├── processor/
│   ├── __init__.py
│   ├── screenshot.py
│   ├── performance.py
│   └── image_processor.py
└── common/
    ├── __init__.py
    └── protocol.py
```

Asegúrate de que todos los archivos `__init__.py` existan en cada carpeta.

## Crear los archivos __init__.py

```bash
# Crear directorios
mkdir -p scraper processor common

# Crear archivos __init__.py vacíos o con imports
touch scraper/__init__.py
touch processor/__init__.py
touch common/__init__.py
```

O copiar el contenido del artifact "init_files" en cada archivo correspondiente.
#!/usr/bin/env python3
"""
Servidor de Procesamiento Distribuido (Parte B)
Maneja tareas computacionalmente intensivas usando multiprocessing.
"""

import argparse
import socketserver
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import sys
import signal

from processor.screenshot import ScreenshotGenerator
from processor.performance import PerformanceAnalyzer
from processor.image_processor import ImageProcessor
from common.protocol import Protocol


class ProcessingHandler(socketserver.BaseRequestHandler):
    """Handler para procesar solicitudes del servidor de scraping"""
    
    def handle(self):
        """Maneja una conexión entrante"""
        try:
            # Recibir datos
            data = Protocol.receive_socket(self.request)
            
            if data is None:
                return
            
            # Procesar solicitud en el pool de procesos
            result = self.server.process_request_data(data)
            
            # Enviar respuesta
            response = Protocol.encode(result)
            self.request.sendall(response)
            
        except Exception as e:
            error_response = Protocol.encode({
                'error': f'Processing error: {str(e)}',
                'screenshot': None,
                'performance': None,
                'thumbnails': []
            })
            self.request.sendall(error_response)


class ProcessingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    Servidor que maneja procesamiento paralelo.
    ThreadingMixIn permite manejar múltiples conexiones concurrentes.
    """
    
    allow_reuse_address = True
    
    def __init__(self, server_address, handler_class, num_processes):
        super().__init__(server_address, handler_class)
        self.num_processes = num_processes
        self.executor = ProcessPoolExecutor(max_workers=num_processes)
        print(f"Pool de procesos inicializado con {num_processes} workers")
    
    def process_request_data(self, data):
        """
        Procesa la solicitud usando el pool de procesos.
        Cada tarea se ejecuta en un proceso separado.
        """
        url = data.get('url', '')
        html = data.get('html', '')
        
        # Crear futures para cada tarea
        screenshot_future = self.executor.submit(generate_screenshot, url)
        performance_future = self.executor.submit(analyze_performance, url)
        thumbnails_future = self.executor.submit(process_images, url, html)
        
        # Esperar resultados (esto bloquea el thread actual, no el proceso)
        try:
            screenshot = screenshot_future.result(timeout=30)
        except Exception as e:
            screenshot = None
            print(f"Screenshot error: {e}")
        
        try:
            performance = performance_future.result(timeout=30)
        except Exception as e:
            performance = None
            print(f"Performance error: {e}")
        
        try:
            thumbnails = thumbnails_future.result(timeout=30)
        except Exception as e:
            thumbnails = []
            print(f"Thumbnails error: {e}")
        
        return {
            'screenshot': screenshot,
            'performance': performance,
            'thumbnails': thumbnails
        }
    
    def shutdown_pool(self):
        """Cierra el pool de procesos de forma limpia"""
        print("\nCerrando pool de procesos...")
        self.executor.shutdown(wait=True)
        print("Pool cerrado")


# Funciones de procesamiento (ejecutadas en procesos separados)

def generate_screenshot(url):
    """
    Genera screenshot de la URL.
    Se ejecuta en un proceso separado.
    """
    try:
        generator = ScreenshotGenerator()
        screenshot = generator.capture(url)
        return screenshot
    except Exception as e:
        print(f"Error generando screenshot: {e}")
        return None


def analyze_performance(url):
    """
    Analiza el rendimiento de la página.
    Se ejecuta en un proceso separado.
    """
    try:
        analyzer = PerformanceAnalyzer()
        performance = analyzer.analyze(url)
        return performance
    except Exception as e:
        print(f"Error analizando rendimiento: {e}")
        return None


def process_images(url, html):
    """
    Procesa imágenes de la página.
    Se ejecuta en un proceso separado.
    """
    try:
        processor = ImageProcessor()
        thumbnails = processor.generate_thumbnails(url, html)
        return thumbnails
    except Exception as e:
        print(f"Error procesando imágenes: {e}")
        return []


def parse_arguments():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Servidor de Procesamiento Distribuido',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-i', '--ip',
        required=True,
        help='Dirección de escucha'
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        required=True,
        help='Puerto de escucha'
    )
    
    parser.add_argument(
        '-n', '--processes',
        type=int,
        default=mp.cpu_count(),
        help=f'Número de procesos en el pool (default: {mp.cpu_count()})'
    )
    
    return parser.parse_args()


def signal_handler(signum, frame):
    """Maneja señales del sistema para shutdown limpio"""
    print("\nSeñal recibida, cerrando servidor...")
    sys.exit(0)


def main():
    args = parse_arguments()
    
    # Configurar handler de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Crear servidor
    server_address = (args.ip, args.port)
    server = ProcessingServer(server_address, ProcessingHandler, args.processes)
    
    print(f"Servidor de Procesamiento iniciado en {args.ip}:{args.port}")
    print(f"Procesos en el pool: {args.processes}")
    print("Esperando conexiones...")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
    finally:
        server.shutdown_pool()
        server.server_close()
        print("Servidor detenido")


if __name__ == '__main__':
    main()
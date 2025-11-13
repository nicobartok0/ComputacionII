#!/usr/bin/env python3
"""
Cliente de prueba para el sistema de scraping.
Interactúa únicamente con el Servidor A (asyncio).
"""

import requests
import argparse
import json
import sys


class ScrapingClient:
    """Cliente para interactuar con el servidor de scraping"""
    
    def __init__(self, host='127.0.0.1', port=8000):
        """
        Inicializa el cliente.
        
        Args:
            host: Host del servidor
            port: Puerto del servidor
        """
        self.base_url = f"http://{host}:{port}"
    
    def scrape(self, url, timeout=60):
        """
        Solicita el scraping de una URL.
        
        Args:
            url: URL a scrapear
            timeout: Timeout en segundos
            
        Returns:
            Diccionario con los resultados o None si falla
        """
        try:
            print(f"Solicitando scraping de: {url}")
            print("Esperando respuesta...")
            
            response = requests.get(
                f"{self.base_url}/scrape",
                params={'url': url},
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error HTTP {response.status_code}: {response.text}")
                return None
                
        except requests.Timeout:
            print("Error: Timeout esperando respuesta del servidor")
            return None
        except requests.ConnectionError:
            print("Error: No se pudo conectar al servidor")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def health_check(self):
        """
        Verifica que el servidor esté activo.
        
        Returns:
            Boolean indicando si el servidor está activo
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def print_results(self, results):
        """
        Imprime los resultados de forma legible.
        
        Args:
            results: Diccionario con los resultados del scraping
        """
        if not results:
            print("\nNo se obtuvieron resultados")
            return
        
        print("\n" + "="*80)
        print("RESULTADOS DEL SCRAPING")
        print("="*80)
        
        print(f"\nURL: {results.get('url')}")
        print(f"Timestamp: {results.get('timestamp')}")
        print(f"Estado: {results.get('status')}")
        
        if 'message' in results:
            print(f"Mensaje: {results['message']}")
        
        # Datos de scraping
        if 'scraping_data' in results:
            print("\n--- DATOS DE SCRAPING ---")
            scraping = results['scraping_data']
            
            print(f"Título: {scraping.get('title', 'N/A')}")
            print(f"Número de enlaces: {len(scraping.get('links', []))}")
            print(f"Número de imágenes: {scraping.get('images_count', 0)}")
            
            if scraping.get('structure'):
                print("Estructura de headers:")
                for header, count in scraping['structure'].items():
                    print(f"  {header}: {count}")
            
            if scraping.get('meta_tags'):
                print("Meta tags:")
                for key, value in list(scraping['meta_tags'].items())[:5]:
                    print(f"  {key}: {value[:100]}..." if len(str(value)) > 100 else f"  {key}: {value}")
        
        # Datos de procesamiento
        if 'processing_data' in results:
            print("\n--- DATOS DE PROCESAMIENTO ---")
            processing = results['processing_data']
            
            if 'error' in processing:
                print(f"Error en procesamiento: {processing['error']}")
            
            if processing.get('screenshot'):
                print(f"Screenshot: Generado ({len(processing['screenshot'])} bytes en base64)")
            else:
                print("Screenshot: No disponible")
            
            if processing.get('performance'):
                perf = processing['performance']
                if 'error' not in perf:
                    print("Rendimiento:")
                    print(f"  Tiempo de carga: {perf.get('load_time_ms', 'N/A')} ms")
                    print(f"  Tamaño total: {perf.get('total_size_kb', 'N/A')} KB")
                    print(f"  Número de requests: {perf.get('num_requests', 'N/A')}")
                else:
                    print(f"  Error: {perf.get('error')}")
            
            if processing.get('thumbnails'):
                print(f"Thumbnails: {len(processing['thumbnails'])} generados")
        
        print("\n" + "="*80)


def parse_arguments():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Cliente para el sistema de scraping web',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'url',
        help='URL a scrapear'
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host del servidor (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Puerto del servidor (default: 8000)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Timeout en segundos (default: 60)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Imprimir resultado como JSON'
    )
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    # Crear cliente
    client = ScrapingClient(args.host, args.port)
    
    # Verificar que el servidor esté activo
    print(f"Verificando conexión con {args.host}:{args.port}...")
    if not client.health_check():
        print("Error: El servidor no está activo o no es accesible")
        sys.exit(1)
    
    print("Servidor activo ✓")
    
    # Realizar scraping
    results = client.scrape(args.url, timeout=args.timeout)
    
    # Imprimir resultados
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        client.print_results(results)
    
    # Código de salida
    if results and results.get('status') == 'success':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Servidor de Scraping Web Asíncrono (Parte A)
Maneja solicitudes de scraping de forma asíncrona y coordina con el servidor de procesamiento.
"""

import asyncio
import argparse
import json
import socket
from datetime import datetime
from aiohttp import web, ClientSession, ClientTimeout
from urllib.parse import urlparse
import sys

# Importar módulos propios
from scraper.html_parser import HTMLParser
from scraper.metadata_extractor import MetadataExtractor
from scraper.async_http import AsyncHTTPClient
from common.protocol import Protocol


class ScrapingServer:
    def __init__(self, host, port, workers, processing_host='127.0.0.1', processing_port=8001):
        self.host = host
        self.port = port
        self.workers = workers
        self.processing_host = processing_host
        self.processing_port = processing_port
        self.app = web.Application()
        self.setup_routes()
        self.http_client = AsyncHTTPClient(max_concurrent=workers)
        
    def setup_routes(self):
        self.app.router.add_get('/scrape', self.handle_scrape)
        self.app.router.add_get('/health', self.handle_health)
        
    async def handle_health(self, request):
        """Endpoint para verificar que el servidor está activo"""
        return web.json_response({'status': 'healthy'})
    
    async def handle_scrape(self, request):
        """
        Endpoint principal de scraping.
        Espera un parámetro 'url' en la query string.
        """
        try:
            # Obtener URL de los parámetros
            url = request.query.get('url')
            if not url:
                return web.json_response(
                    {'status': 'error', 'message': 'URL parameter is required'},
                    status=400
                )
            
            # Validar URL
            if not self._is_valid_url(url):
                return web.json_response(
                    {'status': 'error', 'message': 'Invalid URL format'},
                    status=400
                )
            
            # Realizar scraping completo
            result = await self.scrape_url(url)
            return web.json_response(result)
            
        except asyncio.TimeoutError:
            return web.json_response(
                {'status': 'error', 'message': 'Request timeout'},
                status=504
            )
        except Exception as e:
            return web.json_response(
                {'status': 'error', 'message': str(e)},
                status=500
            )
    
    def _is_valid_url(self, url):
        """Validar formato de URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    async def scrape_url(self, url):
        """
        Orquesta el proceso completo de scraping y procesamiento.
        Esta función coordina las operaciones asíncronas.
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        try:
            # Paso 1: Descargar HTML de forma asíncrona
            html_content = await self.http_client.fetch(url)
            
            # Paso 2: Parsear HTML (CPU-bound pero rápido)
            parser = HTMLParser(html_content)
            scraping_data = {
                'title': parser.get_title(),
                'links': parser.get_links(url),
                'meta_tags': MetadataExtractor.extract_meta_tags(html_content),
                'structure': parser.get_structure(),
                'images_count': parser.count_images()
            }
            
            # Paso 3: Solicitar procesamiento al Servidor B de forma asíncrona
            processing_data = await self.request_processing(url, html_content)
            
            # Paso 4: Consolidar resultados
            result = {
                'url': url,
                'timestamp': timestamp,
                'scraping_data': scraping_data,
                'processing_data': processing_data,
                'status': 'success'
            }
            
            return result
            
        except Exception as e:
            return {
                'url': url,
                'timestamp': timestamp,
                'status': 'error',
                'message': str(e)
            }
    
    async def request_processing(self, url, html_content):
        """
        Comunica con el Servidor B para solicitar procesamiento.
        Implementa comunicación asíncrona mediante sockets.
        """
        try:
            # Preparar solicitud para el servidor de procesamiento
            request_data = {
                'url': url,
                'html': html_content[:10000]  # Limitar tamaño
            }
            
            # Serializar con el protocolo
            message = Protocol.encode(request_data)
            
            # Conectar de forma asíncrona al servidor de procesamiento
            reader, writer = await asyncio.open_connection(
                self.processing_host, 
                self.processing_port
            )
            
            try:
                # Enviar solicitud
                writer.write(message)
                await writer.drain()
                
                # Recibir respuesta
                response = await Protocol.receive(reader)
                
                return response
                
            finally:
                writer.close()
                await writer.wait_closed()
                
        except ConnectionRefusedError:
            return {
                'error': 'Processing server not available',
                'screenshot': None,
                'performance': None,
                'thumbnails': []
            }
        except Exception as e:
            return {
                'error': f'Processing failed: {str(e)}',
                'screenshot': None,
                'performance': None,
                'thumbnails': []
            }
    
    async def start(self):
        """Inicia el servidor"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        # Determinar familia de direcciones (IPv4 o IPv6)
        try:
            family = socket.AF_INET6 if ':' in self.host else socket.AF_INET
        except:
            family = socket.AF_INET
        
        site = web.TCPSite(runner, self.host, self.port, family=family)
        await site.start()
        
        print(f"Servidor de Scraping iniciado en {self.host}:{self.port}")
        print(f"Workers asíncronos: {self.workers}")
        print(f"Servidor de procesamiento: {self.processing_host}:{self.processing_port}")
        
        # Mantener el servidor corriendo
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\nDeteniendo servidor...")
        finally:
            await self.http_client.close()
            await runner.cleanup()


def parse_arguments():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Servidor de Scraping Web Asíncrono',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-i', '--ip',
        required=True,
        help='Dirección de escucha (soporta IPv4/IPv6)'
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        required=True,
        help='Puerto de escucha'
    )
    
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=4,
        help='Número de workers (default: 4)'
    )
    
    parser.add_argument(
        '--processing-host',
        default='127.0.0.1',
        help='Host del servidor de procesamiento (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--processing-port',
        type=int,
        default=8001,
        help='Puerto del servidor de procesamiento (default: 8001)'
    )
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    # Crear y ejecutar servidor
    server = ScrapingServer(
        args.ip, 
        args.port, 
        args.workers,
        args.processing_host,
        args.processing_port
    )
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServidor detenido")
        sys.exit(0)


if __name__ == '__main__':
    main()
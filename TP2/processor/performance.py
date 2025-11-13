"""
Módulo para analizar el rendimiento de páginas web.
"""

import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class PerformanceAnalyzer:
    """Analizador de rendimiento de páginas web"""
    
    def __init__(self, timeout=15):
        """
        Inicializa el analizador.
        
        Args:
            timeout: Timeout en segundos para las requests
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; PerformanceAnalyzer/1.0)'
        })
    
    def analyze(self, url):
        """
        Analiza el rendimiento de una URL.
        
        Args:
            url: URL a analizar
            
        Returns:
            Diccionario con métricas de rendimiento
        """
        try:
            # Medir tiempo de carga de la página principal
            start_time = time.time()
            response = self.session.get(url, timeout=self.timeout)
            load_time = time.time() - start_time
            
            if response.status_code >= 400:
                return {
                    'error': f'HTTP {response.status_code}',
                    'load_time_ms': None,
                    'total_size_kb': None,
                    'num_requests': None
                }
            
            # Tamaño de la página principal
            html_size = len(response.content)
            
            # Parsear HTML para encontrar recursos
            soup = BeautifulSoup(response.content, 'lxml')
            resources = self._extract_resources(soup, url)
            
            # Calcular métricas
            num_requests = 1 + len(resources)  # 1 para HTML + recursos
            total_size = html_size
            
            # Estimar tamaño total (sin descargar todos los recursos)
            # En producción, se descargarían algunos recursos de muestra
            for resource_url in resources[:10]:  # Limitar a 10 recursos
                try:
                    head_resp = self.session.head(resource_url, timeout=5)
                    if 'content-length' in head_resp.headers:
                        total_size += int(head_resp.headers['content-length'])
                except:
                    # Si falla, estimar 50KB por recurso
                    total_size += 50 * 1024
            
            return {
                'load_time_ms': int(load_time * 1000),
                'total_size_kb': int(total_size / 1024),
                'num_requests': num_requests,
                'html_size_kb': int(html_size / 1024),
                'num_resources': len(resources)
            }
            
        except requests.Timeout:
            return {
                'error': 'Timeout',
                'load_time_ms': None,
                'total_size_kb': None,
                'num_requests': None
            }
        except Exception as e:
            return {
                'error': str(e),
                'load_time_ms': None,
                'total_size_kb': None,
                'num_requests': None
            }
    
    def _extract_resources(self, soup, base_url):
        """
        Extrae URLs de recursos (CSS, JS, imágenes) del HTML.
        
        Args:
            soup: Objeto BeautifulSoup
            base_url: URL base para resolver URLs relativas
            
        Returns:
            Lista de URLs de recursos
        """
        resources = []
        seen = set()
        
        # CSS
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                absolute_url = urljoin(base_url, href)
                if self._is_valid_resource(absolute_url) and absolute_url not in seen:
                    resources.append(absolute_url)
                    seen.add(absolute_url)
        
        # JavaScript
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                absolute_url = urljoin(base_url, src)
                if self._is_valid_resource(absolute_url) and absolute_url not in seen:
                    resources.append(absolute_url)
                    seen.add(absolute_url)
        
        # Imágenes
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src:
                absolute_url = urljoin(base_url, src)
                if self._is_valid_resource(absolute_url) and absolute_url not in seen:
                    resources.append(absolute_url)
                    seen.add(absolute_url)
        
        return resources
    
    def _is_valid_resource(self, url):
        """
        Valida si una URL de recurso es válida.
        
        Args:
            url: URL a validar
            
        Returns:
            Boolean indicando si es válida
        """
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https'] and bool(parsed.netloc)
        except:
            return False
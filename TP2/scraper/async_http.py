"""
Cliente HTTP asíncrono para realizar requests sin bloquear el event loop.
"""

import asyncio
from aiohttp import ClientSession, ClientTimeout, TCPConnector
import aiohttp


class AsyncHTTPClient:
    """Cliente HTTP asíncrono con manejo de timeouts y límites de concurrencia"""
    
    def __init__(self, max_concurrent=10, timeout=30):
        """
        Inicializa el cliente HTTP asíncrono.
        
        Args:
            max_concurrent: Número máximo de conexiones concurrentes
            timeout: Timeout en segundos para las requests
        """
        self.max_concurrent = max_concurrent
        self.timeout = ClientTimeout(total=timeout)
        self.session = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _get_session(self):
        """Obtiene o crea la sesión HTTP"""
        if self.session is None or self.session.closed:
            connector = TCPConnector(limit=self.max_concurrent, limit_per_host=5)
            self.session = ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; WebScraper/1.0)'
                }
            )
        return self.session
    
    async def fetch(self, url):
        """
        Descarga el contenido de una URL de forma asíncrona.
        
        Args:
            url: URL a descargar
            
        Returns:
            String con el contenido HTML
            
        Raises:
            aiohttp.ClientError: Si hay error en la request
            asyncio.TimeoutError: Si se excede el timeout
        """
        async with self.semaphore:  # Limitar concurrencia
            session = await self._get_session()
            
            try:
                async with session.get(url) as response:
                    # Verificar status code
                    if response.status >= 400:
                        raise aiohttp.ClientError(
                            f"HTTP {response.status} error for URL: {url}"
                        )
                    
                    # Limitar tamaño de descarga a 10MB
                    content = await response.text(errors='ignore')
                    
                    if len(content) > 10 * 1024 * 1024:  # 10MB
                        raise ValueError("Content too large (>10MB)")
                    
                    return content
                    
            except asyncio.TimeoutError:
                raise asyncio.TimeoutError(f"Timeout fetching URL: {url}")
            except aiohttp.ClientError as e:
                raise aiohttp.ClientError(f"Error fetching {url}: {str(e)}")
    
    async def fetch_multiple(self, urls):
        """
        Descarga múltiples URLs de forma concurrente.
        
        Args:
            urls: Lista de URLs a descargar
            
        Returns:
            Lista de tuplas (url, content) para URLs exitosas
        """
        tasks = [self._fetch_with_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar errores
        successful = []
        for url, result in zip(urls, results):
            if not isinstance(result, Exception):
                successful.append((url, result))
        
        return successful
    
    async def _fetch_with_url(self, url):
        """Helper para fetch que retorna la URL junto con el contenido"""
        try:
            content = await self.fetch(url)
            return content
        except Exception as e:
            return None
    
    async def fetch_binary(self, url):
        """
        Descarga contenido binario (ej: imágenes) de forma asíncrona.
        
        Args:
            url: URL a descargar
            
        Returns:
            Bytes con el contenido binario
        """
        async with self.semaphore:
            session = await self._get_session()
            
            try:
                async with session.get(url) as response:
                    if response.status >= 400:
                        raise aiohttp.ClientError(
                            f"HTTP {response.status} error for URL: {url}"
                        )
                    
                    # Limitar a 5MB para binarios
                    content = await response.read()
                    
                    if len(content) > 5 * 1024 * 1024:  # 5MB
                        raise ValueError("Binary content too large (>5MB)")
                    
                    return content
                    
            except asyncio.TimeoutError:
                raise asyncio.TimeoutError(f"Timeout fetching binary from: {url}")
            except aiohttp.ClientError as e:
                raise aiohttp.ClientError(f"Error fetching binary {url}: {str(e)}")
    
    async def close(self):
        """Cierra la sesión HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            # Esperar a que las conexiones se cierren completamente
            await asyncio.sleep(0.250)
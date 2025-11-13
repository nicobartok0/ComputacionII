"""
Módulo para parsear HTML y extraer información estructurada.
"""

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class HTMLParser:
    """Parser de HTML para extraer información de páginas web"""
    
    def __init__(self, html_content):
        """
        Inicializa el parser con contenido HTML.
        
        Args:
            html_content: String con el contenido HTML
        """
        self.soup = BeautifulSoup(html_content, 'lxml')
    
    def get_title(self):
        """
        Extrae el título de la página.
        
        Returns:
            String con el título o None si no existe
        """
        title_tag = self.soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        return None
    
    def get_links(self, base_url):
        """
        Extrae todos los enlaces de la página.
        
        Args:
            base_url: URL base para resolver enlaces relativos
            
        Returns:
            Lista de URLs absolutas
        """
        links = []
        seen = set()
        
        for a_tag in self.soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Resolver URL relativa a absoluta
            absolute_url = urljoin(base_url, href)
            
            # Validar y agregar si no se ha visto
            if self._is_valid_link(absolute_url) and absolute_url not in seen:
                links.append(absolute_url)
                seen.add(absolute_url)
        
        return links[:100]  # Limitar a 100 enlaces
    
    def _is_valid_link(self, url):
        """
        Valida si un enlace es válido.
        
        Args:
            url: URL a validar
            
        Returns:
            Boolean indicando si es válida
        """
        try:
            parsed = urlparse(url)
            # Debe tener esquema (http/https) y dominio
            return parsed.scheme in ['http', 'https'] and bool(parsed.netloc)
        except:
            return False
    
    def get_structure(self):
        """
        Analiza la estructura de headers de la página.
        
        Returns:
            Diccionario con conteo de cada nivel de header (h1-h6)
        """
        structure = {}
        
        for level in range(1, 7):
            tag_name = f'h{level}'
            headers = self.soup.find_all(tag_name)
            count = len(headers)
            if count > 0:
                structure[tag_name] = count
        
        return structure
    
    def count_images(self):
        """
        Cuenta las imágenes en la página.
        
        Returns:
            Número entero de imágenes encontradas
        """
        images = self.soup.find_all('img')
        return len(images)
    
    def get_images(self, base_url, limit=5):
        """
        Extrae URLs de imágenes de la página.
        
        Args:
            base_url: URL base para resolver URLs relativas
            limit: Número máximo de imágenes a extraer
            
        Returns:
            Lista de URLs absolutas de imágenes
        """
        images = []
        seen = set()
        
        for img_tag in self.soup.find_all('img', src=True):
            if len(images) >= limit:
                break
            
            src = img_tag['src']
            
            # Resolver URL relativa a absoluta
            absolute_url = urljoin(base_url, src)
            
            # Validar y agregar si no se ha visto
            if self._is_valid_image_url(absolute_url) and absolute_url not in seen:
                images.append(absolute_url)
                seen.add(absolute_url)
        
        return images
    
    def _is_valid_image_url(self, url):
        """
        Valida si una URL de imagen es válida.
        
        Args:
            url: URL a validar
            
        Returns:
            Boolean indicando si es válida
        """
        try:
            parsed = urlparse(url)
            # Debe tener esquema y dominio
            if not (parsed.scheme in ['http', 'https'] and parsed.netloc):
                return False
            
            # Verificar extensión común de imagen
            path_lower = parsed.path.lower()
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
            return any(path_lower.endswith(ext) for ext in image_extensions)
        except:
            return False
    
    def get_text_content(self, max_length=1000):
        """
        Extrae el texto visible de la página.
        
        Args:
            max_length: Longitud máxima del texto a extraer
            
        Returns:
            String con el texto visible
        """
        # Remover scripts y styles
        for script in self.soup(['script', 'style']):
            script.decompose()
        
        # Obtener texto
        text = self.soup.get_text(separator=' ', strip=True)
        
        # Limitar longitud
        if len(text) > max_length:
            text = text[:max_length] + '...'
        
        return text
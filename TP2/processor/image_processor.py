"""
Módulo para procesar imágenes de páginas web.
"""

import base64
from io import BytesIO
from PIL import Image
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup


class ImageProcessor:
    """Procesador de imágenes para generar thumbnails"""
    
    def __init__(self, thumbnail_size=(200, 200), max_images=3, timeout=10):
        """
        Inicializa el procesador de imágenes.
        
        Args:
            thumbnail_size: Tupla (ancho, alto) para los thumbnails
            max_images: Número máximo de imágenes a procesar
            timeout: Timeout en segundos para descargar imágenes
        """
        self.thumbnail_size = thumbnail_size
        self.max_images = max_images
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ImageProcessor/1.0)'
        })
    
    def generate_thumbnails(self, url, html_content):
        """
        Genera thumbnails de las imágenes principales de la página.
        
        Args:
            url: URL base de la página
            html_content: Contenido HTML de la página
            
        Returns:
            Lista de strings con thumbnails en base64
        """
        try:
            # Extraer URLs de imágenes
            image_urls = self._extract_image_urls(html_content, url)
            
            if not image_urls:
                return []
            
            # Limitar cantidad
            image_urls = image_urls[:self.max_images]
            
            # Generar thumbnails
            thumbnails = []
            for img_url in image_urls:
                thumbnail = self._create_thumbnail(img_url)
                if thumbnail:
                    thumbnails.append(thumbnail)
            
            return thumbnails
            
        except Exception as e:
            print(f"Error generando thumbnails: {e}")
            return []
    
    def _extract_image_urls(self, html_content, base_url):
        """
        Extrae URLs de imágenes del HTML.
        
        Args:
            html_content: Contenido HTML
            base_url: URL base para resolver URLs relativas
            
        Returns:
            Lista de URLs de imágenes
        """
        soup = BeautifulSoup(html_content, 'lxml')
        image_urls = []
        seen = set()
        
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src:
                # Resolver URL relativa
                absolute_url = urljoin(base_url, src)
                
                # Validar y agregar
                if self._is_valid_image_url(absolute_url) and absolute_url not in seen:
                    image_urls.append(absolute_url)
                    seen.add(absolute_url)
        
        return image_urls
    
    def _is_valid_image_url(self, url):
        """
        Valida si una URL de imagen es válida.
        
        Args:
            url: URL a validar
            
        Returns:
            Boolean indicando si es válida
        """
        try:
            # Verificar que sea HTTP/HTTPS
            if not url.startswith(('http://', 'https://')):
                return False
            
            # Verificar extensión
            lower_url = url.lower()
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
            return any(lower_url.endswith(ext) or ext + '?' in lower_url for ext in image_extensions)
        except:
            return False
    
    def _create_thumbnail(self, image_url):
        """
        Descarga una imagen y crea un thumbnail.
        
        Args:
            image_url: URL de la imagen
            
        Returns:
            String con el thumbnail en base64 o None si falla
        """
        try:
            # Descargar imagen
            response = self.session.get(image_url, timeout=self.timeout, stream=True)
            
            if response.status_code != 200:
                return None
            
            # Limitar tamaño de descarga a 5MB
            content = b''
            max_size = 5 * 1024 * 1024
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > max_size:
                    return None
            
            # Abrir imagen con PIL
            image = Image.open(BytesIO(content))
            
            # Crear thumbnail manteniendo aspect ratio
            image.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            # Convertir a RGB si es necesario (para PNGs con transparencia)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Guardar como JPEG en memoria
            output = BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Convertir a base64
            thumbnail_b64 = base64.b64encode(output.read()).decode('utf-8')
            
            return thumbnail_b64
            
        except requests.Timeout:
            print(f"Timeout descargando imagen: {image_url}")
            return None
        except Exception as e:
            print(f"Error creando thumbnail de {image_url}: {e}")
            return None
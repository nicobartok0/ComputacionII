"""
Módulo para extraer metadatos de páginas web.
"""

from bs4 import BeautifulSoup


class MetadataExtractor:
    """Extractor de metadatos de páginas HTML"""
    
    @staticmethod
    def extract_meta_tags(html_content):
        """
        Extrae meta tags relevantes del HTML.
        
        Args:
            html_content: String con el contenido HTML
            
        Returns:
            Diccionario con los meta tags encontrados
        """
        soup = BeautifulSoup(html_content, 'lxml')
        metadata = {}
        
        # Meta tags estándar
        standard_tags = ['description', 'keywords', 'author', 'viewport', 'robots']
        for tag_name in standard_tags:
            value = MetadataExtractor._get_meta_content(soup, 'name', tag_name)
            if value:
                metadata[tag_name] = value
        
        # Open Graph tags
        og_tags = ['og:title', 'og:description', 'og:image', 'og:url', 'og:type', 'og:site_name']
        for tag_name in og_tags:
            value = MetadataExtractor._get_meta_content(soup, 'property', tag_name)
            if value:
                metadata[tag_name] = value
        
        # Twitter Card tags
        twitter_tags = ['twitter:card', 'twitter:title', 'twitter:description', 'twitter:image']
        for tag_name in twitter_tags:
            value = MetadataExtractor._get_meta_content(soup, 'name', tag_name)
            if value:
                metadata[tag_name] = value
        
        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            metadata['canonical'] = canonical['href']
        
        return metadata
    
    @staticmethod
    def _get_meta_content(soup, attr_name, attr_value):
        """
        Obtiene el contenido de un meta tag específico.
        
        Args:
            soup: Objeto BeautifulSoup
            attr_name: Nombre del atributo ('name' o 'property')
            attr_value: Valor del atributo a buscar
            
        Returns:
            Contenido del meta tag o None si no existe
        """
        meta_tag = soup.find('meta', attrs={attr_name: attr_value})
        if meta_tag and meta_tag.get('content'):
            return meta_tag['content']
        return None
    
    @staticmethod
    def extract_structured_data(html_content):
        """
        Extrae datos estructurados (JSON-LD, Schema.org) del HTML.
        
        Args:
            html_content: String con el contenido HTML
            
        Returns:
            Lista de objetos de datos estructurados
        """
        soup = BeautifulSoup(html_content, 'lxml')
        structured_data = []
        
        # Buscar scripts con type="application/ld+json"
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string)
                structured_data.append(data)
            except:
                continue
        
        return structured_data
    
    @staticmethod
    def extract_language(html_content):
        """
        Detecta el idioma de la página.
        
        Args:
            html_content: String con el contenido HTML
            
        Returns:
            Código de idioma (ej: 'en', 'es') o None
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Buscar en tag html
        html_tag = soup.find('html')
        if html_tag:
            lang = html_tag.get('lang')
            if lang:
                return lang
        
        # Buscar en meta tags
        meta_lang = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if meta_lang and meta_lang.get('content'):
            return meta_lang['content']
        
        return None
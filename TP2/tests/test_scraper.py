"""
Tests para los módulos de scraping.
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import asyncio
from scraper.html_parser import HTMLParser
from scraper.metadata_extractor import MetadataExtractor
from scraper.async_http import AsyncHTTPClient


class TestHTMLParser(unittest.TestCase):
    """Tests para el HTMLParser"""
    
    def setUp(self):
        """Configurar HTML de prueba"""
        self.sample_html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <title>Página de Prueba</title>
            <meta name="description" content="Esta es una página de prueba">
            <meta name="keywords" content="test, prueba, html">
            <meta property="og:title" content="Título OG">
        </head>
        <body>
            <h1>Título Principal</h1>
            <h2>Subtítulo 1</h2>
            <h2>Subtítulo 2</h2>
            <h3>Sección A</h3>
            <h3>Sección B</h3>
            <h3>Sección C</h3>
            
            <a href="https://example.com">Enlace 1</a>
            <a href="/path/page">Enlace 2</a>
            <a href="relative.html">Enlace 3</a>
            
            <img src="image1.jpg" alt="Imagen 1">
            <img src="/images/image2.png" alt="Imagen 2">
            <img src="https://example.com/image3.gif" alt="Imagen 3">
        </body>
        </html>
        """
        self.parser = HTMLParser(self.sample_html)
    
    def test_get_title(self):
        """Test de extracción de título"""
        title = self.parser.get_title()
        self.assertEqual(title, "Página de Prueba")
    
    def test_get_title_missing(self):
        """Test cuando no hay título"""
        parser = HTMLParser("<html><body>No title</body></html>")
        title = parser.get_title()
        self.assertIsNone(title)
    
    def test_get_links(self):
        """Test de extracción de enlaces"""
        links = self.parser.get_links("https://example.com/page.html")
        
        # Verificar que se encontraron enlaces
        self.assertGreater(len(links), 0)
        
        # Verificar que todos son URLs absolutas
        for link in links:
            self.assertTrue(link.startswith('http'))
    
    def test_get_structure(self):
        """Test de estructura de headers"""
        structure = self.parser.get_structure()
        
        self.assertEqual(structure.get('h1'), 1)
        self.assertEqual(structure.get('h2'), 2)
        self.assertEqual(structure.get('h3'), 3)
        self.assertNotIn('h4', structure)
    
    def test_count_images(self):
        """Test de conteo de imágenes"""
        count = self.parser.count_images()
        self.assertEqual(count, 3)
    
    def test_get_images(self):
        """Test de extracción de URLs de imágenes"""
        images = self.parser.get_images("https://example.com/", limit=5)
        
        # Verificar que se encontraron imágenes
        self.assertGreater(len(images), 0)
        
        # Verificar que son URLs válidas
        for img_url in images:
            self.assertTrue(img_url.startswith('http'))
    
    def test_get_text_content(self):
        """Test de extracción de texto"""
        text = self.parser.get_text_content()
        
        self.assertIn("Título Principal", text)
        self.assertIn("Subtítulo", text)


class TestMetadataExtractor(unittest.TestCase):
    """Tests para el MetadataExtractor"""
    
    def setUp(self):
        """Configurar HTML de prueba"""
        self.sample_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta name="description" content="Test description">
            <meta name="keywords" content="test, metadata, extraction">
            <meta name="author" content="Test Author">
            <meta property="og:title" content="OG Title">
            <meta property="og:description" content="OG Description">
            <meta property="og:image" content="https://example.com/image.jpg">
            <meta name="twitter:card" content="summary">
            <link rel="canonical" href="https://example.com/page">
        </head>
        <body></body>
        </html>
        """
    
    def test_extract_meta_tags(self):
        """Test de extracción de meta tags"""
        metadata = MetadataExtractor.extract_meta_tags(self.sample_html)
        
        # Verificar meta tags estándar
        self.assertEqual(metadata.get('description'), "Test description")
        self.assertEqual(metadata.get('keywords'), "test, metadata, extraction")
        self.assertEqual(metadata.get('author'), "Test Author")
        
        # Verificar Open Graph tags
        self.assertEqual(metadata.get('og:title'), "OG Title")
        self.assertEqual(metadata.get('og:description'), "OG Description")
        self.assertEqual(metadata.get('og:image'), "https://example.com/image.jpg")
        
        # Verificar Twitter tags
        self.assertEqual(metadata.get('twitter:card'), "summary")
        
        # Verificar canonical
        self.assertEqual(metadata.get('canonical'), "https://example.com/page")
    
    def test_extract_language(self):
        """Test de detección de idioma"""
        lang = MetadataExtractor.extract_language(self.sample_html)
        self.assertEqual(lang, "en")
    
    def test_extract_language_missing(self):
        """Test cuando no hay idioma definido"""
        html = "<html><head></head><body></body></html>"
        lang = MetadataExtractor.extract_language(html)
        self.assertIsNone(lang)
    
    def test_extract_structured_data(self):
        """Test de extracción de datos estructurados"""
        html_with_jsonld = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "Test Article"
            }
            </script>
        </head>
        <body></body>
        </html>
        """
        
        structured_data = MetadataExtractor.extract_structured_data(html_with_jsonld)
        
        self.assertEqual(len(structured_data), 1)
        self.assertEqual(structured_data[0]['@type'], 'Article')
        self.assertEqual(structured_data[0]['headline'], 'Test Article')


class TestAsyncHTTPClient(unittest.TestCase):
    """Tests para el AsyncHTTPClient"""
    
    def setUp(self):
        """Configurar cliente"""
        self.client = AsyncHTTPClient(max_concurrent=5, timeout=30)
    
    def tearDown(self):
        """Limpiar cliente"""
        asyncio.run(self.client.close())
    
    def test_fetch_success(self):
        """Test de descarga exitosa"""
        async def run_test():
            content = await self.client.fetch("https://example.com")
            self.assertIsNotNone(content)
            self.assertIn("Example", content)
        
        asyncio.run(run_test())
    
    def test_fetch_invalid_url(self):
        """Test con URL inválida"""
        async def run_test():
            with self.assertRaises(Exception):
                await self.client.fetch("https://this-url-does-not-exist-12345.com")
        
        asyncio.run(run_test())
    
    def test_fetch_multiple(self):
        """Test de descarga múltiple"""
        async def run_test():
            urls = [
                "https://example.com",
                "https://www.iana.org",
            ]
            results = await self.client.fetch_multiple(urls)
            
            # Al menos una debería ser exitosa
            self.assertGreater(len(results), 0)
        
        asyncio.run(run_test())
    
    def test_session_reuse(self):
        """Test de reutilización de sesión"""
        async def run_test():
            # Primera request
            await self.client.fetch("https://example.com")
            session1 = self.client.session
            
            # Segunda request
            await self.client.fetch("https://example.com")
            session2 = self.client.session
            
            # Debería ser la misma sesión
            self.assertIs(session1, session2)
        
        asyncio.run(run_test())


class TestHTMLParserEdgeCases(unittest.TestCase):
    """Tests de casos límite para el HTMLParser"""
    
    def test_empty_html(self):
        """Test con HTML vacío"""
        parser = HTMLParser("")
        self.assertIsNone(parser.get_title())
        self.assertEqual(parser.count_images(), 0)
        self.assertEqual(len(parser.get_links("https://example.com")), 0)
    
    def test_malformed_html(self):
        """Test con HTML mal formado"""
        html = "<html><head><title>Test</head><body><h1>Header<body></html>"
        parser = HTMLParser(html)
        
        # Debería funcionar gracias a BeautifulSoup
        self.assertEqual(parser.get_title(), "Test")
    
    def test_html_without_links(self):
        """Test con HTML sin enlaces"""
        html = "<html><body><p>Just text</p></body></html>"
        parser = HTMLParser(html)
        links = parser.get_links("https://example.com")
        self.assertEqual(len(links), 0)
    
    def test_relative_urls_resolution(self):
        """Test de resolución de URLs relativas"""
        html = """
        <html>
        <body>
            <a href="/path/page">Link 1</a>
            <a href="relative">Link 2</a>
            <a href="../parent">Link 3</a>
        </body>
        </html>
        """
        parser = HTMLParser(html)
        links = parser.get_links("https://example.com/current/page.html")
        
        # Todas deberían ser absolutas
        for link in links:
            self.assertTrue(link.startswith("https://example.com"))
    
    def test_duplicate_links(self):
        """Test que no haya enlaces duplicados"""
        html = """
        <html>
        <body>
            <a href="https://example.com/page1">Link</a>
            <a href="https://example.com/page1">Link</a>
            <a href="https://example.com/page1">Link</a>
        </body>
        </html>
        """
        parser = HTMLParser(html)
        links = parser.get_links("https://example.com")
        
        # Debería haber solo 1 enlace
        self.assertEqual(len(links), 1)


def run_tests():
    """Ejecutar todos los tests"""
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar tests
    suite.addTests(loader.loadTestsFromTestCase(TestHTMLParser))
    suite.addTests(loader.loadTestsFromTestCase(TestMetadataExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestAsyncHTTPClient))
    suite.addTests(loader.loadTestsFromTestCase(TestHTMLParserEdgeCases))
    
    # Ejecutar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
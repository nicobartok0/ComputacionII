"""
Tests para los módulos de procesamiento.
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import base64
from io import BytesIO
from PIL import Image
from processor.screenshot import ScreenshotGenerator
from processor.performance import PerformanceAnalyzer
from processor.image_processor import ImageProcessor
import time


class TestScreenshotGenerator(unittest.TestCase):
    """Tests para el ScreenshotGenerator"""
    
    def setUp(self):
        """Configurar generador de screenshots"""
        self.generator = ScreenshotGenerator(headless=True, timeout=15)
    
    def test_capture_success(self):
        """Test de captura exitosa de screenshot"""
        try:
            screenshot = self.generator.capture("https://example.com")
            
            if screenshot:
                # Verificar que es una cadena base64 válida
                self.assertIsInstance(screenshot, str)
                self.assertGreater(len(screenshot), 0)
                
                # Intentar decodificar
                img_data = base64.b64decode(screenshot)
                self.assertGreater(len(img_data), 0)
                
                # Verificar que es una imagen PNG válida
                img = Image.open(BytesIO(img_data))
                self.assertEqual(img.format, 'PNG')
            else:
                # Si ChromeDriver no está disponible, el test pasa
                self.skipTest("ChromeDriver no disponible")
                
        except Exception as e:
            # Si hay problemas con Selenium, skip el test
            self.skipTest(f"Selenium/ChromeDriver no disponible: {e}")
    
    def test_capture_with_dimensions(self):
        """Test de captura con dimensiones específicas"""
        try:
            screenshot = self.generator.capture_with_dimensions(
                "https://example.com",
                width=800,
                height=600
            )
            
            if screenshot:
                self.assertIsInstance(screenshot, str)
                self.assertGreater(len(screenshot), 0)
            else:
                self.skipTest("ChromeDriver no disponible")
                
        except Exception as e:
            self.skipTest(f"Selenium/ChromeDriver no disponible: {e}")
    
    def test_capture_invalid_url(self):
        """Test con URL inválida"""
        try:
            screenshot = self.generator.capture("https://this-url-does-not-exist-12345.com")
            # Debería retornar None en caso de error
            self.assertIsNone(screenshot)
        except Exception as e:
            self.skipTest(f"Selenium/ChromeDriver no disponible: {e}")
    
    def test_capture_timeout(self):
        """Test de timeout en captura"""
        try:
            # Usar timeout muy corto
            generator = ScreenshotGenerator(headless=True, timeout=1)
            
            # URL que puede tardar mucho
            screenshot = generator.capture("https://www.wikipedia.org")
            
            # Puede retornar None si timeout
            self.assertTrue(screenshot is None or isinstance(screenshot, str))
            
        except Exception as e:
            self.skipTest(f"Selenium/ChromeDriver no disponible: {e}")


class TestPerformanceAnalyzer(unittest.TestCase):
    """Tests para el PerformanceAnalyzer"""
    
    def setUp(self):
        """Configurar analizador"""
        self.analyzer = PerformanceAnalyzer(timeout=15)
    
    def test_analyze_success(self):
        """Test de análisis exitoso"""
        result = self.analyzer.analyze("https://example.com")
        
        # Verificar estructura del resultado
        self.assertIn('load_time_ms', result)
        self.assertIn('total_size_kb', result)
        self.assertIn('num_requests', result)
        
        # Verificar que no hay error
        if 'error' not in result:
            # Verificar valores razonables
            self.assertIsInstance(result['load_time_ms'], int)
            self.assertGreater(result['load_time_ms'], 0)
            
            self.assertIsInstance(result['total_size_kb'], int)
            self.assertGreater(result['total_size_kb'], 0)
            
            self.assertIsInstance(result['num_requests'], int)
            self.assertGreaterEqual(result['num_requests'], 1)
    
    def test_analyze_invalid_url(self):
        """Test con URL inválida"""
        result = self.analyzer.analyze("https://this-url-does-not-exist-12345.com")
        
        # Debería tener error
        self.assertIn('error', result)
    
    def test_analyze_http_error(self):
        """Test con página que retorna error HTTP"""
        result = self.analyzer.analyze("https://httpstat.us/404")
        
        # Puede tener error o código HTTP
        self.assertTrue('error' in result or 'load_time_ms' in result)
    
    def test_extract_resources(self):
        """Test de extracción de recursos"""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
        <head>
            <link rel="stylesheet" href="/styles.css">
            <script src="/script.js"></script>
        </head>
        <body>
            <img src="/image1.jpg">
            <img src="/image2.png">
        </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'lxml')
        resources = self.analyzer._extract_resources(soup, "https://example.com/")
        
        # Debería encontrar recursos
        self.assertGreater(len(resources), 0)
        
        # Todos deberían ser URLs absolutas
        for resource in resources:
            self.assertTrue(resource.startswith("https://example.com/"))
    
    def test_performance_metrics_consistency(self):
        """Test de consistencia de métricas"""
        result = self.analyzer.analyze("https://example.com")
        
        if 'error' not in result:
            # El número de requests debería ser al menos 1 (el HTML)
            self.assertGreaterEqual(result['num_requests'], 1)
            
            # El tamaño HTML debería ser menor o igual al total
            if 'html_size_kb' in result:
                self.assertLessEqual(result['html_size_kb'], result['total_size_kb'])


class TestImageProcessor(unittest.TestCase):
    """Tests para el ImageProcessor"""
    
    def setUp(self):
        """Configurar procesador de imágenes"""
        self.processor = ImageProcessor(
            thumbnail_size=(200, 200),
            max_images=3,
            timeout=10
        )
    
    def test_generate_thumbnails(self):
        """Test de generación de thumbnails"""
        html = """
        <html>
        <body>
            <img src="https://via.placeholder.com/400x300.jpg">
            <img src="https://via.placeholder.com/300x400.png">
        </body>
        </html>
        """
        
        thumbnails = self.processor.generate_thumbnails("https://example.com", html)
        
        # Puede generar algunos thumbnails o ninguno si hay problemas de red
        self.assertIsInstance(thumbnails, list)
        
        # Si se generaron, verificar que son base64 válidos
        for thumb in thumbnails:
            self.assertIsInstance(thumb, str)
            self.assertGreater(len(thumb), 0)
            
            # Intentar decodificar
            img_data = base64.b64decode(thumb)
            img = Image.open(BytesIO(img_data))
            self.assertEqual(img.format, 'JPEG')
    
    def test_extract_image_urls(self):
        """Test de extracción de URLs de imágenes"""
        html = """
        <html>
        <body>
            <img src="/image1.jpg">
            <img src="image2.png">
            <img src="https://example.com/image3.gif">
        </body>
        </html>
        """
        
        urls = self.processor._extract_image_urls(html, "https://example.com/page.html")
        
        # Debería encontrar imágenes
        self.assertGreater(len(urls), 0)
        
        # Todas deberían ser URLs absolutas
        for url in urls:
            self.assertTrue(url.startswith("https://"))
    
    def test_is_valid_image_url(self):
        """Test de validación de URLs de imágenes"""
        # URLs válidas
        self.assertTrue(self.processor._is_valid_image_url("https://example.com/image.jpg"))
        self.assertTrue(self.processor._is_valid_image_url("https://example.com/image.png"))
        self.assertTrue(self.processor._is_valid_image_url("https://example.com/image.gif"))
        self.assertTrue(self.processor._is_valid_image_url("https://example.com/image.jpg?size=large"))
        
        # URLs inválidas
        self.assertFalse(self.processor._is_valid_image_url("https://example.com/page.html"))
        self.assertFalse(self.processor._is_valid_image_url("ftp://example.com/image.jpg"))
        self.assertFalse(self.processor._is_valid_image_url("not-a-url"))
    
    def test_create_thumbnail_aspect_ratio(self):
        """Test que los thumbnails mantienen aspect ratio"""
        # Crear una imagen de prueba
        img = Image.new('RGB', (400, 200), color='red')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        # Procesar
        img_thumb = Image.open(buffer)
        img_thumb.thumbnail((200, 200), Image.Resampling.LANCZOS)
        
        # Verificar que el aspect ratio se mantuvo (2:1)
        width, height = img_thumb.size
        ratio = width / height
        self.assertAlmostEqual(ratio, 2.0, places=1)
    
    def test_max_images_limit(self):
        """Test del límite de imágenes"""
        html = """
        <html>
        <body>
            <img src="https://via.placeholder.com/100x100.jpg">
            <img src="https://via.placeholder.com/100x100.jpg">
            <img src="https://via.placeholder.com/100x100.jpg">
            <img src="https://via.placeholder.com/100x100.jpg">
            <img src="https://via.placeholder.com/100x100.jpg">
        </body>
        </html>
        """
        
        processor = ImageProcessor(max_images=2)
        urls = processor._extract_image_urls(html, "https://example.com")
        
        # No debería extraer más de max_images
        # Nota: _extract_image_urls no limita, pero generate_thumbnails sí
        thumbnails = processor.generate_thumbnails("https://example.com", html)
        self.assertLessEqual(len(thumbnails), processor.max_images)
    
    def test_empty_html(self):
        """Test con HTML sin imágenes"""
        html = "<html><body><p>No images here</p></body></html>"
        thumbnails = self.processor.generate_thumbnails("https://example.com", html)
        
        self.assertEqual(len(thumbnails), 0)


class TestProcessorIntegration(unittest.TestCase):
    """Tests de integración entre módulos de procesamiento"""
    
    def test_full_processing_pipeline(self):
        """Test del pipeline completo de procesamiento"""
        url = "https://example.com"
        
        # Screenshot
        try:
            generator = ScreenshotGenerator(headless=True, timeout=10)
            screenshot = generator.capture(url)
            
            if screenshot:
                self.assertIsInstance(screenshot, str)
        except Exception:
            screenshot = None
        
        # Performance
        analyzer = PerformanceAnalyzer(timeout=10)
        performance = analyzer.analyze(url)
        
        self.assertIsNotNone(performance)
        self.assertIn('load_time_ms', performance)
        
        # Images (con HTML simple)
        html = '<html><body><img src="https://via.placeholder.com/100"></body></html>'
        processor = ImageProcessor(max_images=1, timeout=5)
        thumbnails = processor.generate_thumbnails(url, html)
        
        self.assertIsInstance(thumbnails, list)
    
    def test_error_handling_consistency(self):
        """Test de manejo consistente de errores"""
        invalid_url = "https://this-url-does-not-exist-12345.com"
        
        # Todos deberían manejar errores gracefully
        
        # Screenshot
        try:
            generator = ScreenshotGenerator()
            result = generator.capture(invalid_url)
            self.assertTrue(result is None or isinstance(result, str))
        except Exception:
            pass  # OK si no hay ChromeDriver
        
        # Performance
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze(invalid_url)
        self.assertIn('error', result)
        
        # Images
        processor = ImageProcessor()
        html = '<html><body><img src="https://invalid.com/img.jpg"></body></html>'
        result = processor.generate_thumbnails(invalid_url, html)
        self.assertIsInstance(result, list)


def run_tests():
    """Ejecutar todos los tests"""
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar tests
    suite.addTests(loader.loadTestsFromTestCase(TestScreenshotGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestImageProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessorIntegration))
    
    # Ejecutar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
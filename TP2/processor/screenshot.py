"""
Módulo para generar screenshots de páginas web.
"""

import base64
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
import time


class ScreenshotGenerator:
    """Generador de screenshots usando Selenium"""
    
    def __init__(self, headless=True, timeout=15):
        """
        Inicializa el generador de screenshots.
        
        Args:
            headless: Si True, ejecuta el browser en modo headless
            timeout: Timeout en segundos para cargar la página
        """
        self.headless = headless
        self.timeout = timeout
    
    def capture(self, url):
        """
        Captura un screenshot de la URL.
        
        Args:
            url: URL de la página a capturar
            
        Returns:
            String con la imagen en base64 o None si falla
        """
        driver = None
        try:
            # Configurar opciones de Chrome
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Crear driver
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.timeout)
            
            # Cargar página
            driver.get(url)
            
            # Esperar un poco para que cargue JavaScript
            time.sleep(2)
            
            # Capturar screenshot
            screenshot_png = driver.get_screenshot_as_png()
            
            # Convertir a base64
            screenshot_b64 = base64.b64encode(screenshot_png).decode('utf-8')
            
            return screenshot_b64
            
        except TimeoutException:
            print(f"Timeout capturando screenshot de {url}")
            return None
        except WebDriverException as e:
            print(f"Error de WebDriver: {e}")
            return None
        except Exception as e:
            print(f"Error capturando screenshot: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def capture_with_dimensions(self, url, width=1920, height=1080):
        """
        Captura un screenshot con dimensiones específicas.
        
        Args:
            url: URL de la página a capturar
            width: Ancho de la ventana
            height: Alto de la ventana
            
        Returns:
            String con la imagen en base64 o None si falla
        """
        driver = None
        try:
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'--window-size={width},{height}')
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.timeout)
            
            driver.get(url)
            time.sleep(2)
            
            screenshot_png = driver.get_screenshot_as_png()
            screenshot_b64 = base64.b64encode(screenshot_png).decode('utf-8')
            
            return screenshot_b64
            
        except Exception as e:
            print(f"Error capturando screenshot: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
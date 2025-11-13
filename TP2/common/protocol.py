"""
Protocolo de comunicación entre servidores.
Implementa serialización y deserialización de mensajes.
"""

import json
import struct


class Protocol:
    """Protocolo para comunicación entre servidores"""
    
    @staticmethod
    def encode(data):
        """
        Codifica datos a bytes para enviar por socket.
        Formato: [4 bytes longitud][datos JSON]
        
        Args:
            data: Diccionario con los datos a enviar
            
        Returns:
            Bytes con el mensaje codificado
        """
        # Serializar a JSON
        json_data = json.dumps(data, ensure_ascii=False)
        json_bytes = json_data.encode('utf-8')
        
        # Obtener longitud
        length = len(json_bytes)
        
        # Empaquetar: 4 bytes para longitud (big-endian) + datos
        message = struct.pack('>I', length) + json_bytes
        
        return message
    
    @staticmethod
    def decode(data):
        """
        Decodifica datos recibidos por socket.
        
        Args:
            data: Bytes recibidos
            
        Returns:
            Diccionario con los datos deserializados
        """
        # Desempaquetar longitud (primeros 4 bytes)
        if len(data) < 4:
            raise ValueError("Datos insuficientes para decodificar")
        
        length = struct.unpack('>I', data[:4])[0]
        
        # Extraer JSON
        json_bytes = data[4:4+length]
        json_data = json_bytes.decode('utf-8')
        
        # Deserializar JSON
        result = json.loads(json_data)
        
        return result
    
    @staticmethod
    async def receive(reader):
        """
        Recibe un mensaje completo de forma asíncrona desde un StreamReader.
        
        Args:
            reader: asyncio.StreamReader
            
        Returns:
            Diccionario con los datos recibidos
        """
        # Leer longitud (4 bytes)
        length_bytes = await reader.readexactly(4)
        length = struct.unpack('>I', length_bytes)[0]
        
        # Validar longitud razonable (máx 50MB)
        if length > 50 * 1024 * 1024:
            raise ValueError(f"Mensaje demasiado grande: {length} bytes")
        
        # Leer datos
        data_bytes = await reader.readexactly(length)
        json_data = data_bytes.decode('utf-8')
        
        # Deserializar
        result = json.loads(json_data)
        
        return result
    
    @staticmethod
    def receive_socket(sock):
        """
        Recibe un mensaje completo desde un socket (síncrono).
        
        Args:
            sock: Socket conectado
            
        Returns:
            Diccionario con los datos recibidos
        """
        # Leer longitud (4 bytes)
        length_bytes = Protocol._recv_exact(sock, 4)
        if not length_bytes:
            return None
        
        length = struct.unpack('>I', length_bytes)[0]
        
        # Validar longitud razonable (máx 50MB)
        if length > 50 * 1024 * 1024:
            raise ValueError(f"Mensaje demasiado grande: {length} bytes")
        
        # Leer datos
        data_bytes = Protocol._recv_exact(sock, length)
        if not data_bytes:
            return None
        
        json_data = data_bytes.decode('utf-8')
        
        # Deserializar
        result = json.loads(json_data)
        
        return result
    
    @staticmethod
    def _recv_exact(sock, n):
        """
        Recibe exactamente n bytes del socket.
        
        Args:
            sock: Socket conectado
            n: Número de bytes a recibir
            
        Returns:
            Bytes recibidos o None si la conexión se cerró
        """
        data = b''
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data
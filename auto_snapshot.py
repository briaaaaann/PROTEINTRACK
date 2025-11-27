import requests
import datetime
import time

time.sleep(5)

URL = "http://127.0.0.1:5000/api/historial/generar"

try:
    print(f"🔄 Intentando generar snapshot automático: {datetime.datetime.now()}")
    response = requests.post(URL)
    
    if response.status_code == 201:
        print("✅ Éxito: Snapshot generado correctamente.")
    else:
        print(f"⚠️ Alerta: El servidor respondió {response.status_code}. {response.text}")
        
except Exception as e:
    print(f"❌ Error crítico: No se pudo conectar al servidor. ¿Está encendido? Detalle: {e}")
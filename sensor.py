import cv2
import face_recognition
import os
import time
import sys
import numpy as np
import random

# --- CONFIGURACIÓN INICIAL ---
RUTA_ROSTROS = "rostros_autorizados"
SCRIPT_PATH = os.path.abspath(__file__)

def configurar_inicio_automatico():
    """Configura el script para ejecutarse al encender la PC según el S.O."""
    try:
        if sys.platform == "win32":
            import winreg as reg
            clave_ruta = r"Software\Microsoft\Windows\CurrentVersion\Run"
            comando = f'"{sys.executable}" "{SCRIPT_PATH}"'
            clave = reg.OpenKey(reg.HKEY_CURRENT_USER, clave_ruta, 0, reg.KEY_SET_VALUE)
            reg.SetValueEx(clave, "SensorRostroAutostart", 0, reg.REG_SZ, comando)
            reg.CloseKey(clave)
            print("🚀 Configurado para iniciar automáticamente con Windows.")
    except Exception as e:
        print(f"⚠️ No se pudo configurar el inicio automático: {e}")

# 1. Preparar entornos y carpetas
if not os.path.exists(RUTA_ROSTROS):
    os.makedirs(RUTA_ROSTROS)
    print(f"📁 Carpeta '{RUTA_ROSTROS}' creada.")

configurar_inicio_automatico()

# 2. Tomar foto con cuenta regresiva si la carpeta está vacía
if len(os.listdir(RUTA_ROSTROS)) == 0:
    print("\n--- REGISTRO DE NUEVO USUARIO ---")
    nombre_usuario = input("Introduce tu nombre: ").strip().lower()
    
    if nombre_usuario:
        cam_registro = cv2.VideoCapture(0)
        for i in range(3, 0, -1):
            inicio = time.time()
            while time.time() - inicio < 1:
                ret, fotograma = cam_registro.read()
                if ret:
                    cv2.putText(fotograma, str(i), (250, 280), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 165, 255), 10, cv2.LINE_AA)
                    cv2.imshow("Prepara tu rostro", fotograma)
                    cv2.waitKey(1)
        
        ret, foto = cam_registro.read()
        if ret:
            ruta_foto = os.path.join(RUTA_ROSTROS, f"{nombre_usuario}.jpg")
            cv2.imwrite(ruta_foto, foto)
            print(f"✅ Foto guardada en: {ruta_foto}")
        
        cam_registro.release()
        cv2.destroyAllWindows()
    else:
        print("❌ Registro cancelado.")
        sys.exit()

# --- CARGAR ROSTROS AUTORIZADOS ---
rostros_codificados = []
nombres_autorizados = []

for archivo in os.listdir(RUTA_ROSTROS):
    if archivo.endswith((".jpg", ".png", ".jpeg")):
        imagen = face_recognition.load_image_file(os.path.join(RUTA_ROSTROS, archivo))
        codificacion = face_recognition.face_encodings(imagen)
        if len(codificacion) > 0:
            # Guardamos solo la primera codificación encontrada para ahorrar memoria
            rostros_codificados.append(codificacion[0])
            nombres_autorizados.append(os.path.splitext(archivo)[0].capitalize())

# --- CONFIGURACIÓN DE PANTALLA DE VIRUS LIGERA ---
cv2.namedWindow("BLOQUEADO", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("BLOQUEADO", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.moveWindow("BLOQUEADO", -5000, -5000)

carpetas_falsas = ["System32", "Archivos de Programa", "Usuarios/Admin/Documentos", "AppData/Local/Passwords", "Drivers/Kernel"]
extensiones_falsas = [".dll", ".exe", ".jpg", ".docx", ".sys", ".db"]

lineas_consola = []
max_lineas = 18

# OPTIMIZACIÓN: Creamos el lienzo base una sola vez en la RAM
lienzo_base = np.zeros((1080, 1920, 3), dtype=np.uint8)
cv2.rectangle(lienzo_base, (0, 0), (1920, 100), (0, 0, 180), -1)
cv2.putText(lienzo_base, "CRITICAL ERROR - TROJAN.WIN32.DELETER DETECTED", (350, 65), 
            cv2.FONT_HERSHEY_TRIPLEX, 1.4, (255, 255, 255), 3, cv2.LINE_AA)

def generar_pantalla_virus():
    """Genera el texto de la consola falsa reutilizando el lienzo base para no consumir RAM."""
    # Hacemos una copia superficial rápida del lienzo estático
    pantalla = lienzo_base.copy()
    
    # Agregar líneas nuevas de forma controlada
    if random.random() > 0.4 or len(lineas_consola) == 0:
        tipo_accion = random.choice(["[DELETING]", "[WIPING SECTOR]", "[SHREDDING]"])
        ruta_falsa = f"C:/{random.choice(carpetas_falsas)}/file_{random.randint(100,999)}{random.choice(extensiones_falsas)}"
        progreso = f"... {random.randint(10, 100)}% OK"
        lineas_consola.append((f"{tipo_accion} {ruta_falsa} {progreso}", (0, 0, 255)))
        
        if random.random() > 0.8:
            lineas_consola.append((f"[INJECTING_CODE] -> Memory address: {hex(random.randint(0x100000, 0xFFFFFF))}", (0, 255, 0)))

    # OPTIMIZACIÓN CRÍTICA: Forzar la eliminación de elementos viejos para liberar memoria
    while len(lineas_consola) > max_lineas:
        lineas_consola.pop(0)
        
    # Dibujar líneas actuales
    y_start = 180
    for linea, color in lineas_consola:
        cv2.putText(pantalla, linea, (80, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
        y_start += 45
        
    cv2.putText(pantalla, "TOTAL DATA LOSS PROGRESS:  " + str(int(time.time() * 10) % 100) + "%", 
                (1200, 1000), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 165, 255), 2, cv2.LINE_AA)
                
    return pantalla

# --- BUCLE PRINCIPAL (RUNTIME) ---
camara = cv2.VideoCapture(0)
estado_bloqueado = False
ultimo_avistamiento = time.time()

print("\n[INFO] Sensor de seguridad activo.")

while True:
    ret, fotograma = camara.read()
    if not ret:
        rostro_detectado_y_autorizado = False
    else:
        # Reducir imagen a 1/4 para que el procesador no trabaje de más
        fotograma_pequeno = cv2.resize(fotograma, (0, 0), fx=0.25, fy=0.25)
        rgb_fotograma = cv2.cvtColor(fotograma_pequeno, cv2.COLOR_BGR2RGB)

        ubicaciones = face_recognition.face_locations(rgb_fotograma)
        codificaciones = face_recognition.face_encodings(rgb_fotograma, ubicaciones)

        rostro_detectado_y_autorizado = False

        for rostro_anonimo in codificaciones:
            if len(rostros_codificados) > 0:
                # Comparamos directamente con el array optimizado
                coincidencias = face_recognition.compare_faces(rostros_codificados, rostro_anonimo, tolerance=0.55)
                if True in coincidencias:
                    rostro_detectado_y_autorizado = True
                    ultimo_avistamiento = time.time()
                    break

    # Lógica de activación de bloqueo
    if not rostro_detectado_y_autorizado and (time.time() - ultimo_avistamiento > 3):
        if not estado_bloqueado:
            print("🚨 Bloqueando pantalla con simulación segura...")
            cv2.moveWindow("BLOQUEADO", 0, 0)
            cv2.setWindowProperty("BLOQUEADO", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            estado_bloqueado = True
        
        frame_virus = generar_pantalla_virus()
        cv2.imshow("BLOQUEADO", frame_virus)
        cv2.setWindowProperty("BLOQUEADO", cv2.WND_PROP_TOPMOST, 1)
        
        # OPTIMIZACIÓN DE CPU: Dormir el hilo 30ms para limitar los FPS y relajar el procesador
        time.sleep(0.03)
        
    else:
        if estado_bloqueado:
            print("✅ Desbloqueado.")
            cv2.moveWindow("BLOQUEADO", -5000, -5000)
            estado_bloqueado = False

    cv2.waitKey(1)

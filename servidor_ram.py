import cv2
import face_recognition
import os
import time
import sys
import numpy as np
import random
import threading
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- ARCHIVOS Y DIRECTORIOS AUTOMÁTICOS ---
RUTA_ROSTROS = "rostros_autorizados"
CARPETA_TEMPLATES = "templates"
ARCHIVO_HTML = os.path.join(CARPETA_TEMPLATES, "index.html")

# Código HTML incrustado que el script creará solo
CODIGO_HTML_INTERNO = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control de Sensor Facial</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #121212;
            color: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            background: #1e1e1e;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            width: 350px;
        }
        h1 { font-size: 24px; margin-bottom: 10px; }
        .status {
            font-size: 18px;
            margin: 20px 0;
            font-weight: bold;
        }
        .active { color: #00ff00; }
        .inactive { color: #ff0000; }
        .switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 26px; width: 26px;
            left: 4px; bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider { background-color: #00ff00; }
        input:checked + .slider:before { transform: translateX(26px); }
    </style>
</head>
<body>
<div class="container">
    <h1>Panel de Seguridad</h1>
    <p>Control del Sensor Facial</p>
    <div class="status">
        Estado: <span id="status-text" class="inactive">Apagado</span>
    </div>
    <label class="switch">
        <input type="checkbox" id="sensor-toggle" onchange="toggleSensor()">
        <span class="slider"></span>
    </label>
</div>
<script>
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('sensor-toggle').checked = data.activo;
            actualizarInterfaz(data.activo);
        });

    function toggleSensor() {
        const checkbox = document.getElementById('sensor-toggle');
        const accion = checkbox.checked ? 'encender' : 'apagar';
        fetch(`/control?accion=${accion}`)
            .then(response => response.json())
            .then(data => { actualizarInterfaz(data.activo); });
    }

    function actualizarInterfaz(activo) {
        const text = document.getElementById('status-text');
        if (activo) {
            text.innerText = "Encendido / Activo";
            text.className = "active";
        } else {
            text.innerText = "Apagado / Desactivado";
            text.className = "inactive";
        }
    }
</script>
</body>
</html>
"""

# --- INICIALIZACIÓN DE ENTORNO ---
if not os.path.exists(RUTA_ROSTROS):
    os.makedirs(RUTA_ROSTROS)

if not os.path.exists(CARPETA_TEMPLATES):
    os.makedirs(CARPETA_TEMPLATES)

# El script crea automáticamente el archivo HTML si no lo encuentra
if not os.path.exists(ARCHIVO_HTML):
    with open(ARCHIVO_HTML, "w", encoding="utf-8") as f:
        f.write(CODIGO_HTML_INTERNO)
    print("🌐 Archivo 'templates/index.html' generado de forma automática.")

# --- VARIABLES DE CONTROL GLOBAL ---
sensor_activo = False

# --- HILO EN TIEMPO REAL DEL SENSOR ---
def bucle_sensor_facial():
    global sensor_activo
    
    # Intentar cargar firmas de rostros registrados
    rostros_codificados = []
    for archivo in os.listdir(RUTA_ROSTROS):
        if archivo.endswith((".jpg", ".png", ".jpeg")):
            imagen = face_recognition.load_image_file(os.path.join(RUTA_ROSTROS, archivo))
            codificacion = face_recognition.face_encodings(imagen)
            if len(codificacion) > 0:
                rostros_codificados.append(codificacion)

    # Configuración gráfica liviana del virus falso
    cv2.namedWindow("BLOQUEADO", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("BLOQUEADO", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.moveWindow("BLOQUEADO", -5000, -5000)

    carpetas_falsas = ["System32", "Archivos de Programa", "AppData/Local/Passwords", "Drivers/Kernel"]
    extensiones_falsas = [".dll", ".exe", ".sys"]
    lineas_consola = []
    
    lienzo_base = np.zeros((1080, 1920, 3), dtype=np.uint8)
    cv2.rectangle(lienzo_base, (0, 0), (1920, 100), (0, 0, 180), -1)
    cv2.putText(lienzo_base, "CRITICAL ERROR - TROJAN.WIN32.DELETER DETECTED", (350, 65), cv2.FONT_HERSHEY_TRIPLEX, 1.4, (255, 255, 255), 3, cv2.LINE_AA)

    camara = cv2.VideoCapture(0)
    estado_bloqueado = False
    ultimo_avistamiento = time.time()

    # Registro automático rápido por consola integrada si la carpeta está vacía al encender
    if len(rostros_codificados) == 0:
        print("\n⚠️ No se encontraron rostros registrados.")
        nombre_usuario = input("Introduce tu nombre para registrarte rápido (mira la cámara): ").strip().lower()
        if nombre_usuario:
            ret, foto = camara.read()
            if ret:
                ruta_foto = os.path.join(RUTA_ROSTROS, f"{nombre_usuario}.jpg")
                cv2.imwrite(ruta_foto, foto)
                print(f"✅ Registrado. Vuelve a encender el switch desde la web.")
                sensor_activo = False

    while sensor_activo:
        ret, fotograma = camara.read()
        if not ret:
            rostro_detectado = False
        else:
            fotograma_pequeno = cv2.resize(fotograma, (0, 0), fx=0.25, fy=0.25)
            rgb_fotograma = cv2.cvtColor(fotograma_pequeno, cv2.COLOR_BGR2RGB)
            ubicaciones = face_recognition.face_locations(rgb_fotograma)
            codificaciones = face_recognition.face_encodings(rgb_fotograma, ubicaciones)

            rostro_detectado = False
            for rostro_anonimo in codificaciones:
                if len(rostros_codificados) > 0:
                    coincidencias = face_recognition.compare_faces(rostros_codificados, rostro_anonimo, tolerance=0.55)
                    if True in coincidencias:
                        rostro_detectado = True
                        ultimo_avistamiento = time.time()
                        break

        # Lógica de activación de interfaz de pánico
        if not rostro_detectado and (time.time() - ultimo_avistamiento > 3):
            if not estado_bloqueado:
                cv2.moveWindow("BLOQUEADO", 0, 0)
                cv2.setWindowProperty("BLOQUEADO", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                estado_bloqueado = True
            
            pantalla = lienzo_base.copy()
            if random.random() > 0.4 or len(lineas_consola) == 0:
                lineas_consola.append((f"[DELETING] C:/{random.choice(carpetas_falsas)}/file_{random.randint(100,999)}{random.choice(extensiones_falsas)} ... {random.randint(10,100)}% OK", (0, 0, 255)))
            while len(lineas_consola) > 18:
                lineas_consola.pop(0)
                
            y_start = 180
            for linea, color in lineas_consola:
                cv2.putText(pantalla, linea, (80, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
                y_start += 45
            
            cv2.imshow("BLOQUEADO", pantalla)
            cv2.setWindowProperty("BLOQUEADO", cv2.WND_PROP_TOPMOST, 1)
            time.sleep(0.03)
        else:
            if estado_bloqueado:
                cv2.moveWindow("BLOQUEADO", -5000, -5000)
                estado_bloqueado = False

        cv2.waitKey(1)

    camara.release()
    cv2.destroyAllWindows()

# --- ENDPOINTS DE CONTROL WEB ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/status', methods=['GET'])
def obtener_status():
    global sensor_activo
    return jsonify({"activo": sensor_activo})

@app.route('/control', methods=['GET'])
def controlar_sensor():
    global sensor_activo
    accion = request.args.get('accion')
    
    if accion == 'encender' and not sensor_activo:
        sensor_activo = True
        hilo = threading.Thread(target=bucle_sensor_facial)
        hilo.daemon = True
        hilo.start()
        print("▶️ Sensor Facial encendido mediante comandos web.")
    elif accion == 'apagar' and sensor_activo:
        sensor_activo = False
        print("⏸️ Deteniendo sensor remoto.")
        
    return jsonify({"activo": sensor_activo})

if __name__ == '__main__':
    print("\n🌐 Servidor Web Listo.")
    print("👉 Abre en tu navegador la dirección: http://127.0.0.1:5000")
    app.run(debug=True, port=5000, use_reloader=False)


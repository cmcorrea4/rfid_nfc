import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import threading

# Configuración fija del broker MQTT
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "rfid/tags"

# Configuración de la página
st.set_page_config(
    page_title="Monitor RFID/NFC",
    page_icon="📡",
    layout="wide"
)

# Inicialización de variables de estado de la sesión
if 'tags_data' not in st.session_state:
    st.session_state.tags_data = []
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'client' not in st.session_state:
    st.session_state.client = None
if 'tag_count' not in st.session_state:
    st.session_state.tag_count = 0
if 'unique_tags' not in st.session_state:
    st.session_state.unique_tags = set()
if 'last_update' not in st.session_state:
    st.session_state.last_update = "No hay actualizaciones"

# Funciones para MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.connected = True
        client.subscribe(MQTT_TOPIC)
    else:
        st.session_state.connected = False

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        
        # Añadir timestamp más amigable
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["datetime"] = local_time
        
        # Actualizar estadísticas
        st.session_state.tag_count += 1
        st.session_state.unique_tags.add(data["tag_id"])
        
        # Actualizar último mensaje
        st.session_state.last_update = local_time
        
        # Añadir a los datos
        st.session_state.tags_data.append(data)
    except Exception as e:
        st.error(f"Error al procesar el mensaje: {e}")

def connect_mqtt():
    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        st.session_state.client = client
        # Iniciar el loop en un hilo separado
        mqtt_thread = threading.Thread(target=client.loop_forever)
        mqtt_thread.daemon = True
        mqtt_thread.start()
        return True
    except Exception as e:
        st.error(f"Error al conectar: {e}")
        return False

# Conexión automática al inicio
if not st.session_state.connected and st.session_state.client is None:
    connect_mqtt()

# Contenido principal
st.title("Monitor RFID/NFC")
st.write(f"Conectado a: {MQTT_BROKER} en tema: {MQTT_TOPIC}")

# Estado de conexión
if st.session_state.connected:
    st.success("Conectado al broker MQTT")
else:
    st.error("Desconectado del broker MQTT")
    if st.button("Conectar"):
        connect_mqtt()

# Métricas principales
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Lecturas Totales", st.session_state.tag_count)
with col2:
    st.metric("Tags Únicos", len(st.session_state.unique_tags))
with col3:
    st.metric("Última Actualización", st.session_state.last_update)

# Botón para limpiar datos
if st.button("Limpiar datos"):
    st.session_state.tags_data = []
    st.session_state.tag_count = 0
    st.session_state.unique_tags = set()
    st.session_state.last_update = "No hay actualizaciones"

# Tabla de lecturas recientes
st.subheader("Lecturas Recientes")
if st.session_state.tags_data:
    # Crear una tabla simple con las lecturas más recientes
    st.write("Últimas lecturas:")
    
    # Encabezados de la tabla
    col1, col2, col3, col4 = st.columns([3, 2, 3, 3])
    with col1:
        st.write("**Tag ID**")
    with col2:
        st.write("**Tipo**")
    with col3:
        st.write("**Fecha y Hora**")
    with col4:
        st.write("**Datos NFC**")
    
    # Datos de la tabla (últimas 10 entradas)
    for tag in reversed(st.session_state.tags_data[-10:]):
        col1, col2, col3, col4 = st.columns([3, 2, 3, 3])
        with col1:
            st.write(tag["tag_id"])
        with col2:
            st.write(tag.get("tipo", "RFID"))
        with col3:
            st.write(tag.get("datetime", "N/A"))
        with col4:
            st.write(tag.get("nfc_data", "N/A") if "nfc_data" in tag else "N/A")
else:
    st.info("No hay lecturas registradas todavía. Esperando datos desde el ESP32...")

# Actualización automática
if st.session_state.connected:
    time.sleep(1)  # Pequeña pausa para no sobrecargar la interfaz
    st.experimental_rerun()

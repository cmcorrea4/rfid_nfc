import paho.mqtt.client as paho
import time
import streamlit as st
import json
from datetime import datetime

# Configuración fija del broker MQTT
BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "rfid/tags"

# Configuración de la página
st.set_page_config(
    page_title="Monitor RFID/NFC",
    page_icon="📡",
    layout="wide"
)

# Inicialización de variables de estado de la sesión
if 'tags_data' not in st.session_state:
    st.session_state.tags_data = []
if 'tag_count' not in st.session_state:
    st.session_state.tag_count = 0
if 'unique_tags' not in st.session_state:
    st.session_state.unique_tags = set()
if 'last_update' not in st.session_state:
    st.session_state.last_update = "No hay actualizaciones"
if 'message_received' not in st.session_state:
    st.session_state.message_received = ""

# Función para manejar los mensajes recibidos
def on_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8")
        data = json.loads(payload)
        
        # Añadir timestamp más amigable
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["datetime"] = local_time
        
        # Actualizar estadísticas
        st.session_state.tag_count += 1
        if "tag_id" in data:
            st.session_state.unique_tags.add(data["tag_id"])
        
        # Actualizar último mensaje
        st.session_state.last_update = local_time
        
        # Añadir a los datos
        st.session_state.tags_data.append(data)
        
        # Guardar mensaje para mostrar
        st.session_state.message_received = json.dumps(data, indent=2)
        
    except Exception as e:
        st.session_state.message_received = f"Error al procesar el mensaje: {e}"

def subscribe_mqtt():
    try:
        # Crear un nuevo cliente para suscripción
        client = paho.Client("Streamlit-Sub")
        client.on_message = on_message
        client.connect(BROKER, PORT)
        client.subscribe(TOPIC)
        
        # Iniciar un ciclo no bloqueante (procesará mensajes por un tiempo limitado)
        client.loop_start()
        time.sleep(2)  # Esperar 2 segundos para recibir mensajes
        client.loop_stop()
        
        return "Suscripción completada - Esperando mensajes..."
    except Exception as e:
        return f"Error al conectar: {e}"

def publish_test_message():
    try:
        # Crear un nuevo cliente para publicación
        client = paho.Client("Streamlit-Pub")
        client.connect(BROKER, PORT)
        
        # Crear mensaje de prueba
        test_message = {
            "tag_id": "TEST_TAG_123",
            "tipo": "RFID",
            "timestamp": int(time.time() * 1000)
        }
        
        # Publicar mensaje
        result = client.publish(TOPIC, json.dumps(test_message))
        client.disconnect()
        
        if result.rc == 0:
            return "Mensaje de prueba enviado correctamente"
        else:
            return f"Error al enviar mensaje: Código {result.rc}"
    except Exception as e:
        return f"Error al publicar: {e}"

# Contenido principal
st.title("Monitor RFID/NFC")
st.write(f"Broker MQTT: {BROKER}:{PORT} | Tema: {TOPIC}")

# Botones para acciones MQTT
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Suscribirse a mensajes"):
        status = subscribe_mqtt()
        st.info(status)

with col2:
    if st.button("Enviar mensaje de prueba"):
        status = publish_test_message()
        st.info(status)

with col3:
    if st.button("Limpiar datos"):
        st.session_state.tags_data = []
        st.session_state.tag_count = 0
        st.session_state.unique_tags = set()
        st.session_state.last_update = "No hay actualizaciones"
        st.session_state.message_received = ""
        st.success("Datos limpiados")

# Métricas principales
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Lecturas Totales", st.session_state.tag_count)
with col2:
    st.metric("Tags Únicos", len(st.session_state.unique_tags))
with col3:
    st.metric("Última Actualización", st.session_state.last_update)

# Mostrar último mensaje recibido
if st.session_state.message_received:
    st.subheader("Último mensaje recibido")
    st.code(st.session_state.message_received)

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
            st.write(tag.get("tag_id", "N/A"))
        with col2:
            st.write(tag.get("tipo", "RFID"))
        with col3:
            st.write(tag.get("datetime", "N/A"))
        with col4:
            st.write(tag.get("nfc_data", "N/A") if "nfc_data" in tag else "N/A")
else:
    st.info("No hay lecturas registradas todavía. Haz clic en 'Suscribirse a mensajes' para recibir datos.")

# Suscribirse automáticamente cada cierto tiempo
if st.checkbox("Actualización automática", value=False):
    subscribe_mqtt()
    time.sleep(5)  # Esperar 5 segundos
    st.experimental_rerun()

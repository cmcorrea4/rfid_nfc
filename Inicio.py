import streamlit as st
import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
import time

# Configuración de la página
st.set_page_config(
    page_title="Monitor RFID/NFC",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .card {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .tag-rfid {
        background-color: #e6f3ff;
        border-left: 5px solid #0066cc;
    }
    .tag-nfc {
        background-color: #e6fff2;
        border-left: 5px solid #00cc66;
    }
    .tag-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .metric-box {
        background-color: #ffffff;
        border-radius: 5px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

# Inicialización de variables de estado de la sesión
if 'tags_data' not in st.session_state:
    st.session_state.tags_data = []
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'client' not in st.session_state:
    st.session_state.client = None
if 'tag_count' not in st.session_state:
    st.session_state.tag_count = {"RFID": 0, "NFC": 0}
if 'unique_tags' not in st.session_state:
    st.session_state.unique_tags = set()
if 'last_update' not in st.session_state:
    st.session_state.last_update = "No hay actualizaciones"
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = "Desconectado"

# Funciones para MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.connected = True
        st.session_state.connection_status = "Conectado"
        client.subscribe(st.session_state.mqtt_topic)
    else:
        st.session_state.connected = False
        st.session_state.connection_status = f"Error de conexión (código {rc})"

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        
        # Añadir timestamp más amigable
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["datetime"] = local_time
        
        # Actualizar estadísticas
        tag_type = data.get("tipo", "RFID")
        st.session_state.tag_count[tag_type] += 1
        st.session_state.unique_tags.add(data["tag_id"])
        
        # Actualizar último mensaje
        st.session_state.last_update = f"Última lectura: {local_time}"
        
        # Añadir a los datos
        st.session_state.tags_data.append(data)
    except Exception as e:
        st.error(f"Error al procesar el mensaje: {e}")

def connect_mqtt():
    try:
        client = mqtt.Client()
        client.username_pw_set(st.session_state.mqtt_user, st.session_state.mqtt_password)
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(st.session_state.mqtt_server, st.session_state.mqtt_port, 60)
        st.session_state.client = client
        # Iniciar el loop en un hilo separado
        mqtt_thread = threading.Thread(target=client.loop_forever)
        mqtt_thread.daemon = True
        mqtt_thread.start()
        return True
    except Exception as e:
        st.error(f"Error al conectar: {e}")
        return False

def disconnect_mqtt():
    if st.session_state.client:
        st.session_state.client.disconnect()
        st.session_state.connected = False
        st.session_state.connection_status = "Desconectado"

# Sidebar para configuración
with st.sidebar:
    st.title("Configuración MQTT")
    
    st.session_state.mqtt_server = st.text_input("Servidor MQTT", "broker.ejemplo.com")
    st.session_state.mqtt_port = st.number_input("Puerto", min_value=1, max_value=65535, value=1883)
    st.session_state.mqtt_user = st.text_input("Usuario")
    st.session_state.mqtt_password = st.text_input("Contraseña", type="password")
    st.session_state.mqtt_topic = st.text_input("Tema", "rfid/tags")
    
    col1, col2 = st.columns(2)
    with col1:
        if not st.session_state.connected:
            if st.button("Conectar"):
                connect_mqtt()
    with col2:
        if st.session_state.connected:
            if st.button("Desconectar"):
                disconnect_mqtt()
    
    st.write(f"Estado: {st.session_state.connection_status}")
    
    # Opciones adicionales
    st.subheader("Opciones")
    if st.button("Limpiar datos"):
        st.session_state.tags_data = []
        st.session_state.tag_count = {"RFID": 0, "NFC": 0}
        st.session_state.unique_tags = set()

# Contenido principal
st.title("Monitor RFID/NFC")

# Panel de métricas
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-value">{}</div>
        <div class="metric-label">Lecturas Totales</div>
    </div>
    """.format(st.session_state.tag_count["RFID"] + st.session_state.tag_count["NFC"]), unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-value">{}</div>
        <div class="metric-label">Tags Únicos</div>
    </div>
    """.format(len(st.session_state.unique_tags)), unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-label">{}</div>
    </div>
    """.format(st.session_state.last_update), unsafe_allow_html=True)

# Gráfico de distribución
if st.session_state.tags_data:
    st.subheader("Distribución por Tipo")
    
    # Creando un gráfico simple con barras usando componentes de Streamlit
    rfid_count = st.session_state.tag_count["RFID"]
    nfc_count = st.session_state.tag_count["NFC"]
    total = rfid_count + nfc_count
    
    if total > 0:
        rfid_percent = (rfid_count / total) * 100
        nfc_percent = (nfc_count / total) * 100
        
        # Visualización de barras simples
        st.write("RFID: {}%".format(round(rfid_percent, 1)))
        st.progress(rfid_percent / 100)
        st.write("NFC: {}%".format(round(nfc_percent, 1)))
        st.progress(nfc_percent / 100)

# Tabla de lecturas recientes
st.subheader("Lecturas Recientes")
if st.session_state.tags_data:
    # Crear una tabla simple con las lecturas más recientes
    st.write("Últimas 10 lecturas:")
    
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
            st.write(tag.get("nfc_data", "N/A") if tag.get("tipo") == "NFC" else "N/A")
else:
    st.info("No hay lecturas registradas todavía. Conecta al broker MQTT para empezar a recibir datos.")

# Visualización detallada de los tags
st.subheader("Detalles de Tags")
if st.session_state.tags_data:
    for i, tag in enumerate(reversed(st.session_state.tags_data[:5])):  # Mostrar los 5 últimos
        tag_type = tag.get("tipo", "RFID")
        tag_class = "tag-rfid" if tag_type == "RFID" else "tag-nfc"
        
        st.markdown(f"""
        <div class="card {tag_class}">
            <div class="tag-header">Tag ID: {tag["tag_id"]}</div>
            <p><strong>Tipo:</strong> {tag_type}</p>
            <p><strong>Fecha y hora:</strong> {tag.get("datetime", "N/A")}</p>
        """, unsafe_allow_html=True)
        
        # Si es NFC y tiene datos, mostrarlos
        if tag_type == "NFC" and "nfc_data" in tag:
            st.markdown(f"""
            <p><strong>Datos NFC:</strong> {tag["nfc_data"]}</p>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No hay tags detectados.")

# Actualización automática
if st.session_state.connected:
    st.empty()
    time.sleep(1)  # Pequeña pausa para no sobrecargar la interfaz
    st.experimental_rerun()

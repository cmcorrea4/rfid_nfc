import streamlit as st
import paho.mqtt.client as paho
import json
import time

# Configuración fija
BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "rfid/tags"

# Inicialización de estado
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Función para recibir mensajes
def on_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8")
        st.session_state.messages.append(payload)
    except Exception as e:
        st.error(f"Error: {e}")

# Función para conectar y leer
def read_mqtt():
    client = paho.Client("StClient")
    client.on_message = on_message
    
    try:
        client.connect(BROKER, PORT)
        client.subscribe(TOPIC)
        client.loop_start()
        time.sleep(10)  # Escuchar por 10 segundos
        client.loop_stop()
        client.disconnect()
        return True
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return False

# Interface simple
st.title("Lector MQTT")

# Botón para leer
if st.button("Leer mensajes MQTT"):
    with st.spinner("Escuchando mensajes por 10 segundos..."):
        success = read_mqtt()
    if success:
        st.success("Lectura completada")

# Mostrar mensajes
st.subheader("Mensajes recibidos")
if not st.session_state.messages:
    st.info("No hay mensajes. Haz clic en 'Leer mensajes MQTT'")
else:
    for msg in st.session_state.messages:
        st.code(msg)

# Botón para limpiar
if st.button("Limpiar mensajes"):
    st.session_state.messages = []
    st.success("Mensajes limpiados")

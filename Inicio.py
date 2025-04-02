import paho.mqtt.client as paho
import time
import streamlit as st
import json

# Variable global para almacenar mensajes
message_received = ""

# Inicialización de la lista de mensajes
if 'messages' not in st.session_state:
    st.session_state.messages = []

def on_message(client, userdata, message):
    global message_received
    time.sleep(1)
    message_received = str(message.payload.decode("utf-8"))
    
broker = "broker.mqttdashboard.com"
port = 1883
topic = "rfid/tags"

st.title("Lector RFID/NFC")

if st.button('Leer Tags'):
    client = paho.Client("StLector")                           
    client.on_message = on_message                          
    client.connect(broker, port)
    client.subscribe(topic)
    
    # Procesar mensajes por un breve periodo
    client.loop_start()
    time.sleep(5)
    client.loop_stop()
    
    # Mostrar resultado y guardar en la lista
    if message_received:
        st.write("Tag leído:")
        st.code(message_received)
        
        # Guardar en la lista de mensajes
        st.session_state.messages.append(message_received)
    else:
        st.write("No se recibieron tags en este intervalo")
    
# Botón para enviar un mensaje de prueba
if st.button('Enviar Tag de Prueba'):
    client = paho.Client("StPublisher")                        
    client.connect(broker, port)  
    test_message = json.dumps({"tag_id": "TEST123", "tipo": "RFID"})
    ret = client.publish(topic, test_message)
    st.write("Mensaje de prueba enviado")

# Botón para limpiar los mensajes
if st.button('Limpiar Mensajes'):
    st.session_state.messages = []
    st.write("Mensajes limpiados")

# Mostrar todos los mensajes guardados
st.subheader("Historial de mensajes")
if st.session_state.messages:
    st.write(f"Total de mensajes: {len(st.session_state.messages)}")
    for i, msg in enumerate(st.session_state.messages):
        st.write(f"Mensaje #{i+1}:")
        st.code(msg)
else:
    st.write("No hay mensajes en el historial")

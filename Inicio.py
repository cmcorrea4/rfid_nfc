import paho.mqtt.client as paho
import time
import streamlit as st
import json
from datetime import datetime

# Variable global para mensajes
message_received = ""

# Inicialización de la lista de mensajes en session_state
if 'message_list' not in st.session_state:
    st.session_state.message_list = []

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
    
    # Mostrar indicador mientras se procesan mensajes
    with st.spinner('Escuchando mensajes durante 5 segundos...'):
        client.loop_start()
        time.sleep(5)
        client.loop_stop()
    
    # Mostrar resultado y guardar en la lista
    if message_received:
        # Añadir timestamp al mensaje
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Intentar formatear como JSON si es posible
        try:
            json_data = json.loads(message_received)
            formatted_msg = {"timestamp": now, "data": json_data}
        except:
            formatted_msg = {"timestamp": now, "data": message_received}
            
        # Guardar en la lista
        st.session_state.message_list.append(formatted_msg)
        
        st.success("Tag leído correctamente")
    else:
        st.info("No se recibieron tags en este intervalo")
    
# Botón para enviar un mensaje de prueba
if st.button('Enviar Tag de Prueba'):
    client = paho.Client("StPublisher")                        
    client.connect(broker, port)  
    test_message = json.dumps({"tag_id": "TEST123", "tipo": "RFID"})
    ret = client.publish(topic, test_message)
    st.success("Mensaje de prueba enviado")

# Botón para limpiar la lista
if st.button('Limpiar Lista'):
    st.session_state.message_list = []
    st.success("Lista limpiada")

# Mostrar la lista de mensajes
st.subheader("Historial de Tags Leídos")

if not st.session_state.message_list:
    st.info("No hay tags en el historial")
else:
    # Mostrar el número total de tags leídos
    st.write(f"Total de tags leídos: {len(st.session_state.message_list)}")
    
    # Mostrar cada mensaje en la lista (empezando por el más reciente)
    for i, msg in enumerate(reversed(st.session_state.message_list)):
        # Crear un expander para cada mensaje
        with st.expander(f"Tag #{len(st.session_state.message_list) - i} - {msg['timestamp']}"):
            # Si los datos son un diccionario (JSON), mostrarlos con formato
            if isinstance(msg['data'], dict):
                st.json(msg['data'])
            else:
                st.code(msg['data'])

import paho.mqtt.client as paho
import time
import streamlit as st
import json

# Variable global para almacenar mensajes
message_received = ""

def on_message(client, userdata, message):
    global message_received
    time.sleep(1)
    message_received = str(message.payload.decode("utf-8"))
    
broker = "157.230.214.127"
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
    
    # Mostrar resultado
    if message_received:
        st.write("Tag leído:")
        st.code(message_received)
    else:
        st.write("No se recibieron tags en este intervalo")
    
# Botón para enviar un mensaje de prueba
if st.button('Enviar Tag de Prueba'):
    client = paho.Client("StPublisher")                        
    client.connect(broker, port)  
    test_message = json.dumps({"tag_id": "TEST123", "tipo": "RFID"})
    ret = client.publish(topic, test_message)
    st.write("Mensaje de prueba enviado")

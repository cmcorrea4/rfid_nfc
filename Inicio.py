#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Configuración de pines para el módulo RC522
#define RST_PIN     22
#define SS_PIN      21

// Configuración WiFi - DEBES ACTUALIZAR ESTOS VALORES
const char* ssid = "TU_WIFI_SSID";
const char* password = "TU_WIFI_CONTRASEÑA";

// Configuración MQTT - Broker público predefinido
const char* mqtt_server = "broker.mqttdashboard.com";
const int mqtt_port = 1883;
const char* mqtt_topic = "rfid/tags";

// Instancias
MFRC522 mfrc522(SS_PIN, RST_PIN);
WiFiClient espClient;
PubSubClient client(espClient);

// Variable para evitar lecturas duplicadas
String lastReadTag = "";
unsigned long lastReadTime = 0;
const unsigned long READ_DELAY = 3000; // 3 segundos entre lecturas del mismo tag

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi conectado");
  Serial.println("Dirección IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando conexión MQTT...");
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println("conectado");
    } else {
      Serial.print("falló, rc=");
      Serial.print(client.state());
      Serial.println(" intentando en 5 segundos");
      delay(5000);
    }
  }
}

// Función para convertir un array de bytes a String hexadecimal
String byteArrayToHexString(byte* buffer, byte bufferSize) {
  String hex = "";
  for (byte i = 0; i < bufferSize; i++) {
    if (buffer[i] < 0x10) {
      hex += "0";
    }
    hex += String(buffer[i], HEX);
  }
  return hex;
}

// Función para leer datos de memoria NFC (solo para tarjetas MIFARE Classic)
bool readNFCData(MFRC522::MIFARE_Key *key, byte block, byte *buffer, byte size) {
  MFRC522::StatusCode status;
  
  // Autenticación
  status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, block, key, &(mfrc522.uid));
  if (status != MFRC522::STATUS_OK) {
    Serial.print(F("Authentication failed: "));
    Serial.println(mfrc522.GetStatusCodeName(status));
    return false;
  }
  
  // Lectura del bloque
  status = mfrc522.MIFARE_Read(block, buffer, &size);
  if (status != MFRC522::STATUS_OK) {
    Serial.print(F("Reading failed: "));
    Serial.println(mfrc522.GetStatusCodeName(status));
    return false;
  }
  
  return true;
}

void setup() {
  Serial.begin(115200);
  SPI.begin();
  mfrc522.PCD_Init();
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  
  Serial.println(F("Lector RFID RC522 iniciado. Acerque una tarjeta."));
  Serial.println(F("Conectado a broker MQTT: broker.mqttdashboard.com"));
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Buscar nuevas tarjetas
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Seleccionar una de las tarjetas
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Obtener el UID de la tarjeta
  String tagID = byteArrayToHexString(mfrc522.uid.uidByte, mfrc522.uid.size);
  
  // Evitar lecturas duplicadas en corto tiempo
  if (tagID != lastReadTag || (millis() - lastReadTime > READ_DELAY)) {
    lastReadTag = tagID;
    lastReadTime = millis();
    
    Serial.print("Tag detectado: ");
    Serial.println(tagID);
    
    // Crear el objeto JSON para enviar
    StaticJsonDocument<256> jsonDoc;
    jsonDoc["tag_id"] = tagID;
    jsonDoc["tipo"] = "RFID";
    jsonDoc["timestamp"] = millis();
    
    // Si es una tarjeta MIFARE Classic, intentar leer datos de memoria
    if (mfrc522.PICC_GetType(mfrc522.uid.sak) == MFRC522::PICC_TYPE_MIFARE_MINI ||
        mfrc522.PICC_GetType(mfrc522.uid.sak) == MFRC522::PICC_TYPE_MIFARE_1K ||
        mfrc522.PICC_GetType(mfrc522.uid.sak) == MFRC522::PICC_TYPE_MIFARE_4K) {
      
      // Datos para la autenticación
      MFRC522::MIFARE_Key key;
      for (byte i = 0; i < 6; i++) {
        key.keyByte[i] = 0xFF;  // Clave predeterminada
      }
      
      // Buffer para leer los datos
      byte buffer[18];
      byte size = sizeof(buffer);
      
      // Leer datos del bloque 4 (un bloque de ejemplo)
      byte block = 4;
      if (readNFCData(&key, block, buffer, size)) {
        // Convertir datos a string para enviar
        String dataHex = byteArrayToHexString(buffer, 16); // Solo primeros 16 bytes
        jsonDoc["nfc_data"] = dataHex;
        jsonDoc["tipo"] = "NFC";
        
        Serial.print("Datos NFC: ");
        Serial.println(dataHex);
      }
    }
    
    // Serializar a JSON
    char jsonBuffer[256];
    serializeJson(jsonDoc, jsonBuffer);
    
    // Publicar en MQTT
    if (client.publish(mqtt_topic, jsonBuffer)) {
      Serial.println("Mensaje MQTT enviado correctamente");
    } else {
      Serial.println("Error al enviar mensaje MQTT");
    }
  }
  
  // Detener la comunicación con la tarjeta
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}

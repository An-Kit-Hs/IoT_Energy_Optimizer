#include <Arduino.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <SensirionI2cScd30.h>
#include <SensirionI2CSen5x.h>
#include <IRremoteESP8266.h>
#include <IRsend.h>
#include <ir_Panasonic.h>
#include <ArduinoJson.h>

#define IR_LED_PIN D8

/*
==================== WIRING ====================
D2 (GPIO4) -> SDA
D1 (GPIO5) -> SCL

SCD30 -> 0x61
SEN55 -> 0x69

IR LED:
D8 -> Resistor -> IR LED (+)
IR LED (-) -> GND
===============================================
*/

// ---------------- WiFi ----------------
struct WiFiCred {
  const char* ssid;
  const char* password;
};

WiFiCred wifiList[] = {
  {"LAVA", "Ankit@123"},
  {"Prabhakar", "Prabhakar_9309"}
};

const int wifiCount = sizeof(wifiList) / sizeof(wifiList[0]);

// ---------------- MQTT ----------------
const char* mqtt_server = "broker.hivemq.com";

const char* topic_ac = "control/ac/command";
const char* topic_scd30_data = "sensor/data/scd30";
const char* topic_sen55_data = "sensor/data/sen55";

WiFiClient espClient;
PubSubClient client(espClient);

// ---------------- Sensors ----------------
SensirionI2cScd30 scd30;
SensirionI2CSen5x sen55;

bool scd30Available = false;
bool sen55Available = false;

// SCD30
float co2, temp_scd, hum_scd;

// SEN55
float pm1, pm2_5, pm4, pm10;
float temp_sen, hum_sen, voc, nox;

// ---------------- IR AC ----------------
IRPanasonicAc ac(IR_LED_PIN);

bool powerState = false;
uint8_t temperatureAC = 24;
String mode = "cool";

// ---------------- Timing ----------------
unsigned long lastReconnectAttempt = 0;
unsigned long lastMeasurement = 0;
const unsigned long measurementInterval = 120000; // 2 minutes

// ---------------- Functions ----------------

void applyAcState() {
  if (powerState) ac.on();
  else ac.off();

  ac.setTemp(temperatureAC);

  if (mode == "cool") ac.setMode(kPanasonicAcCool);
  else if (mode == "auto") ac.setMode(kPanasonicAcAuto);
  else if (mode == "heat") ac.setMode(kPanasonicAcHeat);
  else if (mode == "dry") ac.setMode(kPanasonicAcDry);
  else if (mode == "fan") ac.setMode(kPanasonicAcFan);

  ac.send();
  Serial.println("AC command sent");
}

// ---------------- MQTT Callback ----------------

void mqttCallback(char* topic, byte* payload, unsigned int length) {

  String message;
  for (int i = 0; i < length; i++)
    message += (char)payload[i];

  Serial.print("Topic: ");
  Serial.println(topic);
  Serial.print("Message: ");
  Serial.println(message);

  if (String(topic) == topic_ac) {

    StaticJsonDocument<200> doc;
    if (deserializeJson(doc, message)) return;

    if (doc.containsKey("power"))
      powerState = (doc["power"] == "on");

    if (doc.containsKey("temp"))
      temperatureAC = constrain(doc["temp"], 16, 30);

    if (doc.containsKey("mode"))
      mode = doc["mode"].as<String>();

    applyAcState();
  }
}

// ---------------- WiFi ----------------

void connectWiFi() {
  Serial.println("Connecting WiFi...");

  for (int i = 0; i < wifiCount; i++) {

    Serial.print("Trying: ");
    Serial.println(wifiList[i].ssid);

    WiFi.begin(wifiList[i].ssid, wifiList[i].password);

    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 20) {
      delay(500);
      Serial.print(".");
      retry++;
    }

    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\nConnected!");
      Serial.println(WiFi.localIP());
      return;
    }

    WiFi.disconnect();
  }

  Serial.println("WiFi failed!");
}

// ---------------- MQTT ----------------

void reconnectMQTT() {
  Serial.print("Connecting MQTT...");

  if (client.connect("NodeMCU_AIR")) {
    Serial.println("Connected");
    client.subscribe(topic_ac);
  } else {
    Serial.print("Failed rc=");
    Serial.println(client.state());
  }
}

// ---------------- Setup ----------------

void setup() {
  Serial.begin(9600);

  Wire.begin(D2, D1);

  // AC setup
  ac.begin();
  ac.setFan(kPanasonicAcFanAuto);
  ac.setSwingVertical(true);

  // WiFi + MQTT
  connectWiFi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(mqttCallback);

  // -------- Detect SCD30 --------
  if (scd30.begin(Wire, SCD30_I2C_ADDR_61)) {
    scd30.stopPeriodicMeasurement();
    scd30.softReset();
    delay(2000);
    scd30.startPeriodicMeasurement(0);

    scd30Available = true;
    Serial.println("SCD30 detected");
  } else {
    Serial.println("SCD30 NOT detected");
  }

  // -------- Detect SEN55 --------
  sen55.begin(Wire);
  uint16_t error = sen55.deviceReset();

  if (error == 0) {
    delay(1000);
    sen55.startMeasurement();

    sen55Available = true;
    Serial.println("SEN55 detected");
  } else {
    Serial.println("SEN55 NOT detected");
  }

  Serial.println("System ready");
}

// ---------------- Loop ----------------

void loop() {

  if (WiFi.status() != WL_CONNECTED)
    connectWiFi();

  if (!client.connected()) {
    if (millis() - lastReconnectAttempt > 5000) {
      lastReconnectAttempt = millis();
      reconnectMQTT();
    }
  } else {
    client.loop();
  }

  // -------- 2 MIN MEASUREMENT --------
  if (millis() - lastMeasurement >= measurementInterval) {

    lastMeasurement = millis();

    Serial.println("\n=== Measurement ===");

    // -------- SCD30 --------
    if (scd30Available && scd30.dataReady()) {
      scd30.readMeasurementData(co2, temp_scd, hum_scd);

      Serial.print("CO2: "); Serial.println(co2);
      Serial.print("Temp(SCD): "); Serial.println(temp_scd);
      Serial.print("Hum(SCD): "); Serial.println(hum_scd);
    }

    // -------- SEN55 --------
    if (sen55Available) {
      uint16_t error = sen55.readMeasuredValues(
        pm1, pm2_5, pm4, pm10,
        temp_sen, hum_sen, voc, nox
      );

      if (!error) {
        Serial.print("PM2.5: "); Serial.println(pm2_5);
        Serial.print("VOC: "); Serial.println(voc);
        Serial.print("NOx: "); Serial.println(nox);
      }
    }

    // -------- Publish SCD30 --------
    if (scd30Available) {
      StaticJsonDocument<150> doc;

      doc["co2"] = co2;
      doc["temperature"] = temp_scd;
      doc["humidity"] = hum_scd;

      char buffer[150];
      serializeJson(doc, buffer);

      client.publish(topic_scd30_data, buffer);
    }

    // -------- Publish SEN55 --------
    if (sen55Available) {
      StaticJsonDocument<200> doc;

      doc["pm1"] = pm1;
      doc["pm2_5"] = pm2_5;
      doc["pm4"] = pm4;
      doc["pm10"] = pm10;

      doc["temperature"] = temp_sen;
      doc["humidity"] = hum_sen;

      doc["voc"] = voc;
      doc["nox"] = nox;

      char buffer[200];
      serializeJson(doc, buffer);

      client.publish(topic_sen55_data, buffer);
    }

    Serial.println("Published available sensor data\n");
  }
}
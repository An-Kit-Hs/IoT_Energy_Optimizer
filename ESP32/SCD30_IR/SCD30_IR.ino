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

// ---------------- DEBUG ----------------
#define DEBUG_PIN D0
bool DEBUG_MODE = false;

#define DBG(x) if (DEBUG_MODE) Serial.println(x)
#define DBG2(x,y) if (DEBUG_MODE) { Serial.print(x); Serial.println(y); }

// ---------------- IR ----------------
#define IR_LED_PIN_AC1 D8
#define IR_LED_PIN_AC2 D7

// ---------------- WIFI ----------------
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

const char* topic_ac1_command = "control/ac1/command";
const char* topic_ac1_state   = "control/ac1/state";

const char* topic_ac2_command = "control/ac2/command";
const char* topic_ac2_state   = "control/ac2/state";

const char* topic_scd30_data = "sensor/data/scd30";
const char* topic_sen55_data = "sensor/data/sen55";

WiFiClient espClient;
PubSubClient client(espClient);

// ---------------- SENSORS ----------------
SensirionI2cScd30 scd30;
SensirionI2CSen5x sen55;

bool scd30Available = false;
bool sen55Available = false;

float co2, temp_scd, hum_scd;
float pm1, pm2_5, pm4, pm10;
float temp_sen, hum_sen, voc, nox;

// ---------------- AC ----------------
IRPanasonicAc ac1(IR_LED_PIN_AC1);
IRPanasonicAc ac2(IR_LED_PIN_AC2);

// ---------------- TIMING ----------------
unsigned long lastReconnectAttempt = 0;
unsigned long lastWiFiAttempt = 0;
unsigned long lastMeasurement = 0;

const unsigned long interval = 5000;

// ---------------- MQTT CALLBACK ----------------
void mqttCallback(char* topic, byte* payload, unsigned int length) {

  String msg;
  for (int i = 0; i < length; i++) msg += (char)payload[i];

  DBG("----- MQTT MESSAGE -----");
  DBG2("Topic: ", topic);
  DBG2("Payload: ", msg);

  StaticJsonDocument<200> doc;
  if (deserializeJson(doc, msg)) {
    DBG("JSON parse failed");
    return;
  }

  bool power = doc["power"] | false;
  int temp = doc["temp"] | 24;
  String mode = doc["mode"] | "cool";
  mode.toLowerCase();

  String t = String(topic);

  // -------- AC1 --------
  if (t == topic_ac1_command || t == topic_ac1_state) {

    DBG("Applying AC1");

    if (power) ac1.on();
    else ac1.off();

    ac1.setTemp(temp);

    if (mode == "cool") ac1.setMode(kPanasonicAcCool);
    else if (mode == "heat") ac1.setMode(kPanasonicAcHeat);
    else if (mode == "auto") ac1.setMode(kPanasonicAcAuto);
    else if (mode == "dry") ac1.setMode(kPanasonicAcDry);
    else if (mode == "fan") ac1.setMode(kPanasonicAcFan);

    ac1.send();
  }

  // -------- AC2 --------
  else if (t == topic_ac2_command || t == topic_ac2_state) {

    DBG("Applying AC2");

    if (power) ac2.on();
    else ac2.off();

    ac2.setTemp(temp);

    if (mode == "cool") ac2.setMode(kPanasonicAcCool);
    else if (mode == "heat") ac2.setMode(kPanasonicAcHeat);
    else if (mode == "auto") ac2.setMode(kPanasonicAcAuto);
    else if (mode == "dry") ac2.setMode(kPanasonicAcDry);
    else if (mode == "fan") ac2.setMode(kPanasonicAcFan);

    ac2.send();
  }
}

// ---------------- WIFI ----------------
void connectWiFi() {
  DBG("Connecting WiFi...");

  for (int i = 0; i < wifiCount; i++) {

    DBG2("Trying: ", wifiList[i].ssid);

    WiFi.begin(wifiList[i].ssid, wifiList[i].password);

    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 20) {
      delay(500);
      if (DEBUG_MODE) Serial.print(".");
      retry++;
    }

    if (WiFi.status() == WL_CONNECTED) {
      DBG("\nWiFi Connected!");
      DBG2("IP: ", WiFi.localIP());
      DBG2("RSSI: ", WiFi.RSSI());
      return;
    }

    DBG("\nFailed, trying next...");
    WiFi.disconnect();
  }

  DBG("WiFi failed!");
}

// ---------------- MQTT ----------------
void reconnectMQTT() {

  DBG("Connecting MQTT...");

  String clientId = "ESP_AC_" + String(ESP.getChipId());

  if (client.connect(clientId.c_str())) {
    DBG("MQTT Connected");

    client.subscribe(topic_ac1_command);
    client.subscribe(topic_ac1_state);
    client.subscribe(topic_ac2_command);
    client.subscribe(topic_ac2_state);

    DBG("Subscribed to topics");
  } else {
    DBG2("MQTT Failed rc=", client.state());
  }
}

// ---------------- SETUP ----------------
void setup() {

  pinMode(DEBUG_PIN, INPUT_PULLUP);
  delay(50);

  if (digitalRead(DEBUG_PIN) == LOW) {
    DEBUG_MODE = true;
  }

  if (DEBUG_MODE) {
    Serial.begin(115200);
    delay(200);
    Serial.println("\n=== DEBUG MODE ENABLED ===");
  }

  Wire.begin();

  connectWiFi();

  client.setServer(mqtt_server, 1883);
  client.setCallback(mqttCallback);

  ac1.begin();
  ac2.begin();

  // ================= SCD30 INIT =================
  scd30.begin(Wire, SCD30_I2C_ADDR_61);

  scd30.softReset();
  delay(2000);

  uint16_t err = scd30.startPeriodicMeasurement(0);

  if (err == 0) {
    delay(3000); 
    scd30Available = true;
    DBG("SCD30 initialized OK");
  } else {
    DBG2("SCD30 init error: ", err);
  }

  // ================= SEN55 INIT =================
  sen55.begin(Wire);
  err = sen55.deviceReset();

  if (err == 0) {
    delay(1000);
    sen55.startMeasurement();
    sen55Available = true;
  }
}

// ---------------- LOOP ----------------
void loop() {

  static unsigned long lastLog = 0;

  if (millis() - lastLog > 10000) {
    lastLog = millis();
    DBG("---- SYSTEM STATUS ----");
    DBG2("WiFi: ", WiFi.status() == WL_CONNECTED ? "OK" : "DOWN");
    DBG2("MQTT: ", client.connected() ? "OK" : "DOWN");
  }

  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - lastWiFiAttempt > 10000) {
      lastWiFiAttempt = millis();
      connectWiFi();
    }
  }

  if (!client.connected()) {
    if (millis() - lastReconnectAttempt > 5000) {
      lastReconnectAttempt = millis();
      reconnectMQTT();
    }
  } else {
    client.loop();
  }

  // ================= SENSOR =================
  if (millis() - lastMeasurement > interval) {
    lastMeasurement = millis();

    // ---------- SCD30 ----------
    if (scd30Available) {

      uint16_t ready = 0;
      int16_t error = scd30.getDataReady(ready);

      DBG("Checking SCD30...");
      DBG2("Ready: ", ready);
      DBG2("Error: ", error);

      if (error) {
        DBG2("SCD30 getDataReady error: ", error);
      }
      else if (ready != 1) {
        DBG("SCD30 not ready yet");
      }
      else {
        error = scd30.readMeasurementData(co2, temp_scd, hum_scd);

        if (!error) {
          DBG("SCD30 OK");
          DBG2("CO2: ", co2);

          StaticJsonDocument<150> doc;
          doc["co2"] = co2;
          doc["temperature"] = temp_scd;
          doc["humidity"] = hum_scd;

          char buffer[150];
          serializeJson(doc, buffer);
          client.publish(topic_scd30_data, buffer);
        } else {
          DBG2("SCD30 read error: ", error);
        }
      }
    }

    // ---------- SEN55 ----------
    if (sen55Available) {
      uint16_t error = sen55.readMeasuredValues(
        pm1, pm2_5, pm4, pm10,
        temp_sen, hum_sen, voc, nox
      );

      if (!error) {
        DBG("SEN55 OK");
        DBG2("PM2.5: ", pm2_5);

        StaticJsonDocument<200> doc;
        doc["pm1"] = pm1;
        doc["pm2_5"] = pm2_5;
        doc["pm4"] = pm4;
        doc["pm10"] = pm10;
        doc["voc"] = voc;
        doc["nox"] = nox;

        char buffer[200];
        serializeJson(doc, buffer);
        client.publish(topic_sen55_data, buffer);
      } else {
        DBG2("SEN55 Error: ", error);
      }
    }
  }
}
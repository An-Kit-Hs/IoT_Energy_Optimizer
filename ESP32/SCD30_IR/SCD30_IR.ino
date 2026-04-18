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

// ---------------- IR ----------------
#define IR_LED_PIN_AC1 D8
#define IR_LED_PIN_AC2 D7

// ---------------- MULTI WIFI ----------------
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

// ---------------- Sensors ----------------
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

bool power1 = false;
uint8_t temp1 = 24;
String mode1 = "cool";

bool power2 = false;
uint8_t temp2 = 24;
String mode2 = "cool";

// ---------------- Timing ----------------
unsigned long lastReconnectAttempt = 0;
unsigned long lastMeasurement = 0;
const unsigned long interval = 120000;

// ---------------- PARSERS ----------------
bool parsePower(JsonVariant val) {
  if (val.is<bool>()) return val.as<bool>();

  if (val.is<const char*>()) {
    String s = val.as<String>();
    s.toLowerCase();
    return (s == "on" || s == "1" || s == "true");
  }

  if (val.is<int>()) return val.as<int>() == 1;

  return false;
}

uint8_t parseTemp(JsonVariant val) {
  int t = 24;

  if (val.is<const char*>())
    t = atoi(val.as<const char*>());
  else if (val.is<int>())
    t = val.as<int>();

  return constrain(t, 16, 30);
}

String parseMode(JsonVariant val) {
  if (!val.is<const char*>()) return "cool";

  String m = val.as<String>();
  m.toLowerCase();

  if (m == "cool" || m == "auto" || m == "heat" || m == "dry" || m == "fan")
    return m;

  return "cool";
}

// ---------------- WIFI ----------------
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

// ---------------- AC APPLY ----------------
void applyAc(IRPanasonicAc &ac, bool power, uint8_t temp, String mode) {
  if (power) ac.on();
  else ac.off();

  ac.setTemp(temp);

  if (mode == "cool") ac.setMode(kPanasonicAcCool);
  else if (mode == "auto") ac.setMode(kPanasonicAcAuto);
  else if (mode == "heat") ac.setMode(kPanasonicAcHeat);
  else if (mode == "dry") ac.setMode(kPanasonicAcDry);
  else if (mode == "fan") ac.setMode(kPanasonicAcFan);

  ac.send();
}

// ---------------- MQTT CALLBACK ----------------
void mqttCallback(char* topic, byte* payload, unsigned int length) {

  String msg;
  for (int i = 0; i < length; i++)
    msg += (char)payload[i];

  StaticJsonDocument<200> doc;
  if (deserializeJson(doc, msg)) return;

  String t = String(topic);

  // ===== AC1 =====
  if (t == topic_ac1_state) {

    if (doc.containsKey("power"))
      power1 = parsePower(doc["power"]);

    applyAc(ac1, power1, temp1, mode1);
  }

  else if (t == topic_ac1_command) {

    if (doc.containsKey("power"))
      power1 = parsePower(doc["power"]);

    if (doc.containsKey("temp")) {
      temp1 = parseTemp(doc["temp"]);
    }

    if (doc.containsKey("mode")) {
      mode1 = parseMode(doc["mode"]);
    }

    applyAc(ac1, power1, temp1, mode1);
  }

  // ===== AC2 =====
  else if (t == topic_ac2_state) {

    if (doc.containsKey("power"))
      power2 = parsePower(doc["power"]);

    applyAc(ac2, power2, temp2, mode2);
  }

  else if (t == topic_ac2_command) {

    if (doc.containsKey("power"))
      power2 = parsePower(doc["power"]);

    if (doc.containsKey("temp")) {
      temp2 = parseTemp(doc["temp"]);
    }

    if (doc.containsKey("mode")) {
      mode2 = parseMode(doc["mode"]);
    }

    applyAc(ac2, power2, temp2, mode2);
  }
}

// ---------------- MQTT ----------------
void reconnectMQTT() {
  Serial.print("Connecting MQTT...");

  if (client.connect("ESP_AC")) {
    Serial.println("Connected");

    client.subscribe(topic_ac1_command);
    client.subscribe(topic_ac1_state);
    client.subscribe(topic_ac2_command);
    client.subscribe(topic_ac2_state);
  } else {
    Serial.print("Failed rc=");
    Serial.println(client.state());
  }
}

// ---------------- SETUP ----------------
void setup() {
  Serial.begin(115200);
  Wire.begin();

  connectWiFi();

  client.setServer(mqtt_server, 1883);
  client.setCallback(mqttCallback);

  ac1.begin();
  ac2.begin();

  ac1.setFan(kPanasonicAcFanAuto);
  ac2.setFan(kPanasonicAcFanAuto);

  // SCD30
  scd30.begin(Wire, SCD30_I2C_ADDR_61);
  uint16_t err = scd30.stopPeriodicMeasurement();

  if (err == 0) {
    scd30.softReset();
    delay(2000);
    scd30.startPeriodicMeasurement(0);
    scd30Available = true;
  }

  // SEN55
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

  if (millis() - lastMeasurement > interval) {
    lastMeasurement = millis();

    // SCD30
    if (scd30Available) {
      uint16_t ready = 0;
      int16_t error = scd30.getDataReady(ready);

      if (!error && ready == 1) {
        error = scd30.readMeasurementData(co2, temp_scd, hum_scd);

        if (!error) {
          StaticJsonDocument<150> doc;
          doc["co2"] = co2;
          doc["temperature"] = temp_scd;
          doc["humidity"] = hum_scd;

          char buffer[150];
          serializeJson(doc, buffer);
          client.publish(topic_scd30_data, buffer);
        }
      }
    }

    // SEN55
    if (sen55Available) {
      uint16_t error = sen55.readMeasuredValues(
        pm1, pm2_5, pm4, pm10,
        temp_sen, hum_sen, voc, nox
      );

      if (!error) {
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
      }
    }
  }
}
#include <Arduino.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <SensirionI2cScd30.h>
#include <IRremoteESP8266.h>
#include <IRsend.h>
#include <ir_Panasonic.h>
#include <ArduinoJson.h>

#define IR_LED_PIN D8

// WiFi
struct WiFiCred {
  const char* ssid;
  const char* password;
};

WiFiCred wifiList[] = {
  {"LAVA", "Ankit@123"},
  {"Prabhakar", "Prabhakar_9309"}
};

const int wifiCount = sizeof(wifiList) / sizeof(wifiList[0]);

// MQTT
const char* mqtt_server = "broker.hivemq.com";

WiFiClient espClient;
PubSubClient client(espClient);

// Sensor
SensirionI2cScd30 sensor;

// IR AC
IRPanasonicAc ac(IR_LED_PIN);

// AC state
bool powerState = false;
uint8_t temperatureAC = 24;
String mode = "cool";

float co2, temp, hum;

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

void mqttCallback(char* topic, byte* payload, unsigned int length) {

  String message;

  for (int i = 0; i < length; i++)
    message += (char)payload[i];

  Serial.print("MQTT Received: ");
  Serial.println(message);

  StaticJsonDocument<200> doc;

  if (deserializeJson(doc, message))
    return;

  if (doc.containsKey("power")) {
    String p = doc["power"];
    powerState = (p == "on");
  }

  if (doc.containsKey("temp")) {
    temperatureAC = constrain(doc["temp"], 16, 30);
  }

  if (doc.containsKey("mode")) {
    mode = doc["mode"].as<String>();
  }

  applyAcState();
}

void connectWiFi() {

  Serial.println("Connecting to WiFi...");

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
      Serial.print("IP: ");
      Serial.println(WiFi.localIP());
      return;
    }

    Serial.println("\nFailed, trying next...");
    WiFi.disconnect();
  }

  Serial.println("Could not connect to any WiFi!");
}

void reconnectMQTT() {

  while (!client.connected()) {

    Serial.print("Connecting MQTT...");

    if (client.connect("NodeMCU_SCD30_AC")) {

      Serial.println("Connected");

      client.subscribe("control/ac/command");

    } else {

      Serial.print("Failed rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

void setup() {

  Serial.begin(9600);

  Wire.begin(D2, D1);

  ac.begin();
  ac.setFan(kPanasonicAcFanAuto);
  ac.setSwingVertical(true);
  ac.setSwingHorizontal(false);

  connectWiFi();

  client.setServer(mqtt_server, 1883);
  client.setCallback(mqttCallback);

  sensor.begin(Wire, SCD30_I2C_ADDR_61);

  sensor.stopPeriodicMeasurement();
  sensor.softReset();

  delay(2000);

  sensor.startPeriodicMeasurement(0);
}

void loop() {

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi lost. Reconnecting...");
    connectWiFi();
  }

  if (!client.connected())
    reconnectMQTT();

  client.loop();

  delay(2000);

  sensor.blockingReadMeasurementData(co2, temp, hum);

  Serial.print("CO2: ");
  Serial.println(co2);

  Serial.print("Temp: ");
  Serial.println(temp);

  Serial.print("Humidity: ");
  Serial.println(hum);

  StaticJsonDocument<200> doc;

  doc["co2"] = co2;
  doc["temperature"] = temp;
  doc["humidity"] = hum;

  char buffer[200];
  serializeJson(doc, buffer);

  client.publish("sensor/data/scd30", buffer);
}
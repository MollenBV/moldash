#define sensor A0 // Sharp IR GP2Y0A41SK0F (4-30cm, analog)

bool bewegingGedetecteerd = false; // Flag om bij te houden of er beweging is gedetecteerd

void setup() {
  Serial.begin(9600); // start de seriële poort
}


void loop() {
  // 5v
  float volts = analogRead(sensor) * 0.0048828125;  // Sensor value (5/1024)
  float m = -13.33; // Helling
  float b = 38.13;  // Y - Snijpunt

  int distance = m * volts + b;
  delay(500); // vertraag de seriële poort

  if (distance <= 20 && !bewegingGedetecteerd) {
    bewegingGedetecteerd = true; // Mark that movement is detected
    Serial.print("Beweging"); // Start character and delimiter
  } else if (distance > 20) {
    bewegingGedetecteerd = false; // Reset movement detection if no movement
  }
}

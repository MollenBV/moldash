// Inclusie van de WiFi-bibliotheek
#include <WiFi.h>

// Definieer Wi-Fi credentials en serverinformatie
const char *ssid = "Loading...";
const char *password = "";
const char *serverIP = "192.168.2.11";
const int serverPort = 80;

// Definieer pinnen voor de seriële communicatie met een ander apparaat
#define RXp2 16
#define TXp2 17

// Initialisatie van variabelen voor punten en tellers
int entrancePoint = 0;
int beforePassportPoint = 0;
int afterPassportPoint = 0;
int exitPoint = 0;
int currentPeopleCount = 0;

// Vlag om bewegingsdetectie bij te houden
bool movementDetected = false;

// Setup-functie wordt eenmaal uitgevoerd bij het opstarten van de microcontroller
void setup() {
  // Start de seriële communicatie met baudrate 115200
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RXp2, TXp2);

  // Maak verbinding met Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Verbinding maken met WiFi...");
  }
  Serial.println("Verbonden met WiFi");
}

// Loop-functie wordt herhaaldelijk uitgevoerd na de setup
void loop() {
  // Controleer of er gegevens beschikbaar zijn op de tweede seriële poort
  if (Serial2.available()) {
    // Lees de ontvangen gegevens tot het teken '>'
    String message = Serial2.readString();
    Serial.println(message);

    // Werk JSON-gegevens bij op basis van bewegingsdetectie
    updateJSONData();

    // Stuur JSON-gegevens naar de server alleen als beweging is gedetecteerd
    if (message.equals("Beweging")) {
      sendJSONData();
      movementDetected = false;  // Reset de vlag na het verzenden van gegevens
    }
  }
}

// Functie om JSON-gegevens bij te werken op basis van bewegingsdetectie
void updateJSONData() {
  // Veronderstel dat bewegingsdetectie de entrancePoint bijwerkt
  if (entrancePoint == 0) {
    entrancePoint = 1;  // Incrementeer alleen als het 0 was (geen eerdere beweging)
    currentPeopleCount++;  // Incrementeer het totale aantal mensen
    movementDetected = true;  // Zet de vlag om beweging aan te geven
  } else {
    // Voeg hier extra logica toe als dat nodig is voor andere punten
  }
}

// Functie om JSON-gegevens naar de server te sturen
void sendJSONData() {
  // Maak verbinding met de server via een WiFi-client
  WiFiClient client;
  if (client.connect(serverIP, serverPort)) {
    // Creëer de specifieke JSON-payload
    String jsonPayload = "{"
                         "\"entrance_point\":" + String(entrancePoint) + ","
                         "\"before_passport_point\":" + String(beforePassportPoint) + ","
                         "\"after_passport_point\":" + String(afterPassportPoint) + ","
                         "\"exit_point\":" + String(exitPoint) +
                         "}";

    // Print de JSON-payload ter verificatie
    Serial.println("Verzenden van JSON-payload:");
    Serial.println(jsonPayload);

    // Verzend het HTTP POST-verzoek met de JSON-payload
    client.println("POST /customs_area HTTP/1.1");
    client.println("Host: " + String(serverIP));
    client.println("Content-Type: application/json");
    client.println("Content-Length: " + String(jsonPayload.length()));
    client.println();
    client.print(jsonPayload);

    // Lees de HTTP-responsstatuscode
    int statusCode = client.parseInt();

    if (statusCode == 200) {
      Serial.println("Server reageerde met een successtatuscode (200)");
    } else {
      Serial.println("Server reageerde met een foutstatuscode: " + String(statusCode));
    }

    // Print de respons van de server naar de Serial Monitor
    while (client.available()) {
      Serial.write(client.read());
    }

    // Verbreek de verbinding met de server (als je deze regel hebt toegevoegd, zal dit de verbinding verbreken)
    //client.stop();
  } else {
    Serial.println("Kan geen verbinding maken met de server");
  }
}

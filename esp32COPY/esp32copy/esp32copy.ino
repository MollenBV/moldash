#include <painlessMesh.h>
#include <ArduinoJson.h>
#include <list>

#define MESH_PREFIX     "ESPMESH"
#define MESH_PASSWORD   "test1234"
#define MESH_PORT       5555

Scheduler userScheduler;
painlessMesh mesh;

uint32_t rootnodeID = 2223841881;
int nodeNummer = 3;

#define RXp2 16
#define TXp2 17

int entrancePoint = 0;
int beforePassportPoint = 0;
int afterPassportPoint = 0;
int exitPoint = 0;
int currentPeopleCount = 0;

// Sequence number for outgoing messages
uint8_t sequenceNumber = 0;

// List to keep track of sent sequence numbers
std::list<uint8_t> sentSequenceNumbers;

// Time variables for delay
unsigned long lastTransmissionTime = 0;

void sendData() {
  // Increase entrancePoint and sequenceNumber
  entrancePoint++;
  sequenceNumber++;

  // Increase sequenceNumber and reset to 0 if it reaches 1024
  sequenceNumber++;
  if (sequenceNumber == 1024) {
    sequenceNumber = 0;
  }
  DynamicJsonDocument doc(200);
  doc["Sensor"] = "Bewegingsensor";
  doc["entrance_point"] = entrancePoint;
  doc["before_passport_point"] = beforePassportPoint;
  doc["after_passport_point"] = afterPassportPoint;
  doc["exit_point"] = exitPoint;
  doc["SequenceNumber"] = sequenceNumber;

  String message;
  serializeJson(doc, message);
  mesh.sendSingle(rootnodeID, message);

  // Store the sent sequence number for potential retransmission
  sentSequenceNumbers.push_back(sequenceNumber);

  Serial.println("Sent message with sequence number: " + String(sequenceNumber));

  // Update the last transmission time
  lastTransmissionTime = millis();
}

void checkForArduinoData();

void checkForArduinoData() {
  if (Serial2.available()) {
    String message = Serial2.readString();
    Serial.println(message);

    if (message.equals("Beweging")) {
      sendData();
    }
  }
}

Task taskCheckForArduinoData(TASK_SECOND * 0.4, TASK_FOREVER, &checkForArduinoData);

void receivedCallback(uint32_t from, String &msg) {
  Serial.printf("Received from %u msg=%s\n", from, msg.c_str());

  DynamicJsonDocument doc(200);
  deserializeJson(doc, msg);

  // Check if the received message is from the root node
  if (from == rootnodeID) {
    // If it's an acknowledgment message
    if (doc.containsKey("Ack")) {
      uint8_t ackedSequenceNumber = doc["SequenceNumber"];
      Serial.println("Received Acknowledgment for sequence number: " + String(ackedSequenceNumber));

      // Remove the acknowledged sequence number from the list
      sentSequenceNumbers.remove(ackedSequenceNumber);
    }
  } else {
    // If it's a regular message from a non-root node
    // Process the received message as needed

    // Send acknowledgment back to the sender
    DynamicJsonDocument ackDoc(50);
    ackDoc["Ack"] = "Received";
    ackDoc["SequenceNumber"] = doc["SequenceNumber"];
    String ackMessage;
    serializeJson(ackDoc, ackMessage);
    mesh.sendSingle(from, ackMessage);
  }
}

void newConnectionCallback(uint32_t nodeId) {
  Serial.printf("New Connection, nodeId = %u\n", nodeId);
}

void changedConnectionCallback() {
  Serial.println("Changed connections");
}

void nodeTimeAdjustedCallback(int32_t offset) {
  // Handle adjusted time if needed
}

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RXp2, TXp2);

  mesh.setDebugMsgTypes(ERROR | STARTUP);
  mesh.init(MESH_PREFIX, MESH_PASSWORD, &userScheduler);
  mesh.onReceive(&receivedCallback);
  mesh.onNewConnection(&newConnectionCallback);
  mesh.onChangedConnections(&changedConnectionCallback);
  mesh.onNodeTimeAdjusted(&nodeTimeAdjustedCallback);
  mesh.setRoot(false);

  userScheduler.addTask(taskCheckForArduinoData);
  taskCheckForArduinoData.enable();

  if (taskCheckForArduinoData.isEnabled()) {
    Serial.println("taskCheckForArduinoData is enabled");
  }
}

void loop() {
  mesh.update();
}

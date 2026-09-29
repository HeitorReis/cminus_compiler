#include <Arduino.h>

namespace {

// DATA_PINS[0] is the least-significant bit. Change only these constants if
// different Arduino GPIOs are more convenient for the final wiring.
constexpr uint8_t DATA_PINS[] = {2, 3, 4};
constexpr uint8_t SUBMIT_PIN = 5;

// The FPGA samples the interface with a divided clock. Millisecond-scale setup,
// pulse, and hold times ensure it observes both the idle-high and active-low
// submit levels while the three data bits remain stable.
constexpr unsigned long DATA_SETUP_US = 3000;
constexpr unsigned long SUBMIT_LOW_US = 5000;
constexpr unsigned long DATA_HOLD_US = 3000;

void writeData(const uint8_t value) {
  for (uint8_t bit = 0; bit < 3; ++bit) {
    digitalWrite(DATA_PINS[bit], bitRead(value, bit) ? HIGH : LOW);
  }
}

void submitValue(const uint8_t value) {
  // Re-establish idle before changing data. This also rearms the FPGA's
  // falling-edge detector between consecutive submissions.
  digitalWrite(SUBMIT_PIN, HIGH);
  writeData(value);
  delayMicroseconds(DATA_SETUP_US);

  digitalWrite(SUBMIT_PIN, LOW);
  delayMicroseconds(SUBMIT_LOW_US);

  digitalWrite(SUBMIT_PIN, HIGH);
  delayMicroseconds(DATA_HOLD_US);
}

void printHelp() {
  Serial.println(F("Enter one digit from 0 to 7."));
  Serial.println(F("Each digit is placed on DATA[2:0] and submitted once."));
}

}  // namespace

void setup() {
  // Preload output levels before enabling the GPIO drivers to avoid an
  // unintended active-low submit pulse during startup.
  for (const uint8_t pin : DATA_PINS) {
    digitalWrite(pin, LOW);
    pinMode(pin, OUTPUT);
  }

  digitalWrite(SUBMIT_PIN, HIGH);
  pinMode(SUBMIT_PIN, OUTPUT);

  Serial.begin(115200);
  printHelp();
}

void loop() {
  while (Serial.available() > 0) {
    const char input = static_cast<char>(Serial.read());

    if (input >= '0' && input <= '7') {
      const uint8_t value = static_cast<uint8_t>(input - '0');
      submitValue(value);
      Serial.print(F("Submitted: "));
      Serial.println(value);
    } else if (input == '?' || input == 'h' || input == 'H') {
      printHelp();
    } else if (input != '\r' && input != '\n' && input != ' ' && input != '\t') {
      Serial.print(F("Invalid input: "));
      Serial.println(input);
    }
  }
}

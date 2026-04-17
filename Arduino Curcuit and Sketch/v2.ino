const int joyX = A0, joyY = A1, btnPin = 3, btnPin2 = 4, btnPin3 = 5;
int centerX, centerY;
char lastState = 'I'; 

void setup() {
  Serial.begin(115200);
  delay(500);
  centerX = analogRead(joyX);
  centerY = analogRead(joyY);
  pinMode(btnPin, INPUT_PULLUP);
  pinMode(btnPin2, INPUT_PULLUP);
  pinMode(btnPin3, INPUT_PULLUP);
}
 void loop() {
  int x = analogRead(joyX) - centerX;
  int y = analogRead(joyY) - centerY;
  if (abs(x) < 20) x = 0; if (abs(y) < 20) y = 0;
  char curr = 'I';

  if (!digitalRead(btnPin)) curr = 'Z'; //Space
  else if (!digitalRead(btnPin2)) curr = 'Q';
  else if (!digitalRead(btnPin3)) curr = 'E';
  else if (x >= 300 && abs(y) <= 200) curr = 'W';
  else if (x <= -300 && abs(y) <= 200) curr = 'S';
  else if (y >= 300 && abs(x) <= 200) curr = 'D';
  else if (y <= -300 && abs(x) <= 200) curr = 'A';

  if (curr != lastState) {
    if (curr != 'I') Serial.println(curr);
    lastState = curr;
  }
  delay(5);
}


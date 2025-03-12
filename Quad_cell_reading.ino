/* 
Step by step plan to read out the quad cell
1. Connect the arduino to your laptop via an USB-A port.
2. Check port of connection
3. Upload this script to the Arduino board
4. Enjoy the results flowing in
*/  

// Constants
float dt = 0.01;
float target_x = 0.0, target_y = 0.0;
float x_smoothed = 0, y_smoothed = 0;
float smoothingFactor = 0.9;  // Smoothing factor (0.0 to 1.0)
float radius = 2.5;

// Timing process
void setup() {
  Serial.begin(9600);
}

// Keep running
void loop() {
  // Read quad-cell transimpedance amplifier voltage outputs
  int sensorVal_0 = analogRead(A2);
  int sensorVal_1 = analogRead(A3);
  int sensorVal_2 = analogRead(A1);
  int sensorVal_3 = analogRead(A0);
  
  // Convert sensor values to voltages
  float V_0 = sensorVal_0 * (5.0 / 1023.0);
  float V_1 = sensorVal_1 * (5.0 / 1023.0);
  float V_2 = sensorVal_2 * (5.0 / 1023.0);
  float V_3 = sensorVal_3 * (5.0 / 1023.0);

  // Calculate laser spot centroid from cell
  float x_correction = 0;
  float y_correction = 0;
  float total_intensity = V_0 + V_1 + V_2 + V_3;
  float x = ((V_1 + V_3) - (V_0 + V_2)) / total_intensity - target_x + x_correction;
  float y = ((V_0 + V_1) - (V_2 + V_3)) / total_intensity - target_y + y_correction;

  // Apply exponential smoothing
  x_smoothed = smoothingFactor * x_smoothed + (1 - smoothingFactor) * x;
  y_smoothed = smoothingFactor * y_smoothed + (1 - smoothingFactor) * y;

  // Displaying output
  Serial.print(x_smoothed)
  Serial.print(',')
  Serial.println(y_smoothed)
  // float x_real = x*radius;
  // float y_real = y*radius;
  
  // Delay for stability
  delay(5);  // Use a shorter delay for better responsiveness
}
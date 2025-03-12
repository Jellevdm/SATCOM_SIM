/* 
Initialisation of variables
*/  
#include <Wire.h>
float distance = 100; //distance (mm) from FSM to Quad cell
float dt = 0.01;
float k_p = 2.5/distance, k_i = 0.0, k_d = 2.5/distance/5;
float x_error_proportional = 0, x_error_integral = 0, x_error_derivative = 0;
float y_error_proportional = 0, y_error_integral = 0, y_error_derivative = 0;
float x_error_prev = 0, y_error_prev = 0;

float target_x = 0.0, target_y = 0.0;
float x_smoothed = 0, y_smoothed = 0;
float smoothingFactor = 0.9;  // Smoothing factor (0.0 to 1.0)
float radius = 2.5;

void setup() {
  Serial.begin(9600);
}

//This is where errofunctions and objective functions will be.
//Note to self: Check how C works before finishing
/*
float Err(float x, float y){
  //Calculate the errorfunction for PID
  Error = pow(x,2) + pow(x,2)
  return Error;
}

float Gradient(float x,float y, float step, float result[2]){
  //calculate the gradient based of an x and y value
  result[0] = 2*x
  result[1] = 2*y
  return;
}
*/

void DAC (int v, char channel, byte mode) {
  byte b=0;
  Wire.beginTransmission(0x4C); //0x48 or 0x4C
  // A3 A2 L1 L0 X Sel1 Sel0 PD0
  channel-='A';
  b|=(channel<<1);
  b|=(mode<<4);
  Wire.write(b);
  // D9 D8 D7 D6 D5 D4 D3 D2
  Wire.write(v>>2);
  // D1 D0 X X X X X X
  Wire.write(v<<6);
  Wire.endTransmission();
};

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

  // PID Controller
  // X-Axis
  x_error_proportional = k_p * x_smoothed;// e_p_max = 2.5 * k_p
  x_error_integral += k_i * x_smoothed;
  x_error_integral = constrain(x_error_integral, -1, 1); //Change if necessary
  x_error_derivative = k_d * (x_smoothed - x_error_prev) / dt; //e_d_max = 5/dt*k_d
  float x_output = x_error_proportional + x_error_integral + x_error_derivative;
  
  x_output = constrain(x_output,-2.5/distance, 2.5/distance);
  //Serial.print(x_output, 4);
  x_error_prev = x_smoothed;

  //This may not be the derivative we want to use
  // float a=0.1; 
  // float command = x_smoothed - a * x_error_derivative;

  // Y-Axis
  y_error_proportional = k_p * y_smoothed;
  y_error_integral += k_i * y_smoothed;
  y_error_integral = constrain(y_error_integral, -1, 1);
  y_error_derivative = k_d * (y_smoothed - y_error_prev) / dt;
  float y_output = y_error_proportional + y_error_integral + y_error_derivative;
  //Serial.print(',');

  y_output = constrain(y_output,-2.5/distance, 2.5/distance);
  //Serial.println(y_output, 4);

  y_error_prev = y_smoothed;

  // Debugging: Print smoothed values and outputs
  // Serial.print(x_smoothed);
  // Serial.print(',');
  // Serial.println(y_smoothed);
  
  //convert the x and y intensity coordinates to real x and y coordinates

  
  // float x_real = x*radius;
  // float y_real = y*radius;
  
  // //convert the physical x and y coordinates to angles
  // float x_angle = x_real/distance;
  // float y_angle = y_real/distance; 

  //convert physical angle to a voltage
  // float x_v = 2.5 - 2.5 * x_angle/1.5;
  // float y_v = 2.5 - 2.5 * y_angle/1.5;


  //concert x and y outputs to voltages that DAC understands
  // float x_voltage = (x_output / (1 * k_p)) * radius * 2.5 / distance + 2.5;
  // float y_voltage = (y_output / (1 * k_p)) * radius * 2.5 / distance + 2.5;


  
  // x_voltage = 0;
  // y_voltage = 0;
  // x=-1;
  // y=-1;
  // // Convert voltage to DAC values
  // int x_dac_value = constrain(x_voltage * (1023), 0, 1023);
  // int y_dac_value = constrain(y_voltage * (1023), 0, 1023);
  // float x_command = map(x_output, -2.5/distance, 2.5/distance, 0, 5);
  // float y_command = map(y_output, -2.5/distance, 2.5/distance, 0, 5);
  float range = 2.5/distance;
  // float x_command = map(x_output, -range,range, 0, 5);
  // float y_command = map(y_output, -range, range, 0, 5);

  float x_command = 2.5 - x_output * 5/range;
  x_command = constrain(x_command, 0, 5);
  float y_command = 2.5 - y_output * 5 /range;
  y_command = constrain(y_command, 0, 5);

  


  // Serial.print(x_output);
  // Serial.print(',');
  // Serial.print(y_output);
  // Serial.print(',');
  // Serial.print(-range);
  // Serial.print(',');
  // Serial.println(range);

  // Serial.print(',');
  // Serial.print(x_command, 4);
  // Serial.print(',');
  // Serial.print(y_command, 4);
  // Serial.print(',');
  // Serial.println(2.5);

  // DAC(x_command, 'A', 0);
  // DAC(y_command, 'B', 2);

  //Serial.print("")
  
  //Serial.print(x_angle);
  //Serial.print(',');
  //Serial.println(y_angle);

  // Serial.print(x_output);
  // Serial.print(',');
  // Serial.println(y_output);

  Serial.print(x);
  Serial.print(',');
  Serial.println(y);

  // Serial.print(',');
  // Serial.print(-1);
  // Serial.print(',');
  // Serial.println(1);

  // Serial.print(V_0);
  // Serial.print(',');
  // Serial.print(V_1);
  // Serial.print(',');
  // Serial.print(V_2);
  // Serial.print(',');
  // Serial.print(V_3);
  // Serial.print(',');
  // Serial.print(0);
  // Serial.print(',');
  // Serial.println(5);


  //Serial.print(x);
  //Serial.println(y);
  // Serial.print(", x_output: ");
  // Serial.print(x_output);
  // Serial.print(", y_output: ");
  // Serial.println(y_output);

  // Delay for stability
  delay(5);  // Use a shorter delay for better responsiveness
}

//PLans:
//lab connect to quad and get readout like mathis did
//lab print hypothetical values for DAC
//Lab try out control on FSM

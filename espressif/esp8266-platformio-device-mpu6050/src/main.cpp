///
/// @file   main.cpp
/// @Author Adam Saxen
/// @date   Oktober, 2016
/// @brief  Boiler plate application for MQTT communication
///

#include <ioant.h>
#include <Wire.h>
using namespace ioant;
/// @brief on_message() function
/// Function definition for handling received MQTT messages
///
/// @param received_topic contains the complete topic structure
/// @param payload contains the contents of the message received
/// @param length the number of bytes received
///
void on_message(Ioant::Topic received_topic, ProtoIO* message);

// ############################################################################
// Everything above this line is mandatory
// ############################################################################

const int MPU = 0x68;
int16_t AcX, AcY, AcZ, GyX, GyY, GyZ;
float gForceX, gForceY, gForceZ, rotX, rotY, rotZ;
long timer = 0;

/// Custom function definitions
// void TestFunction(int t);
/// END OF - Custom function definitions

///. CUSTOM variables
// int variable_test = 1;
/// END OF - CUSTOM variables

void setup(void){
    //Initialize IOAnt core
    //Ioant::GetInstance(on_message);
    Wire.begin(0, 2);//Wire.begin(4, 5);
    Wire.beginTransmission(MPU);
    Wire.write(0x6B);  // PWR_MGMT_1 register
    Wire.write(0);     // set to zero (wakes up the MPU-6050)
    Wire.endTransmission(true);
    // ########################################################################
    //    Now he basics all set up. Send logs to your computer either
    //    over Serial or WifiManager.
    // ########################################################################
    ULOG_DEBUG << "This is a debug message over serial port";
    //WLOG_DEBUG << "This is a debug message over wifi";

}

void dataReceiver(){
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);  // starting with register 0x3B (ACCEL_XOUT_H)
  Wire.endTransmission(false);
  Wire.requestFrom(MPU,14,true);  // request a total of 14 registers
  AcX = Wire.read()<<8|Wire.read();  // 0x3B (ACCEL_XOUT_H) & 0x3C (ACCEL_XOUT_L)
  AcY = Wire.read()<<8|Wire.read();  // 0x3D (ACCEL_YOUT_H) & 0x3E (ACCEL_YOUT_L)
  AcZ = Wire.read()<<8|Wire.read();  // 0x3F (ACCEL_ZOUT_H) & 0x40 (ACCEL_ZOUT_L)
  gForceX = AcX / 16384.0;
  gForceY = AcY / 16384.0;
  gForceZ = AcZ / 16384.0;
}

void loop(void){
    // Monitors Wifi connection and loops MQTT connection. Attempt reconnect if lost
    //IOANT->UpdateLoop();


    dataReceiver();
    if(millis() - timer > 1000){
      ULOG_DEBUG << "getAccX:" << gForceX;
      ULOG_DEBUG << "getAccY:" << gForceY;
      ULOG_DEBUG << "getAccZ:" << gForceZ;
      timer = millis();
    }
    yield();

}

// Function for handling received MQTT messages
void on_message(Ioant::Topic received_topic, ProtoIO* message){

}

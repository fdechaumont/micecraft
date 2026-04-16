/*
  code by : Fabrice de Chaumont
  target : Arduino Nano 33 BLE Sense
  
*/


#include <Arduino_LPS22HB.h>
//#include <Arduino_HTS221.h>

#include <Arduino_HS300x.h>

#include <Arduino_APDS9960.h>
#include <PDM.h>

#include "Arduino_BMI270_BMM150.h"
float x, y, z;
int degreesX = 0;
int degreesY = 0;

int delayMs = 200;
int nbShockSampling = 20;

// buffer to read samples into, each sample is 16-bits

short sampleBuffer[256];


// number of samples read

volatile int samplesRead;


String stringBuffer="";

String receiveSerialData() {
    
    char rc;
    char endMarker = '\n';

    while (Serial.available() > 0 )
    {
      rc = Serial.read();
      if (rc != endMarker) {
        stringBuffer+=rc;
      }else
      {
        String dataReceived = stringBuffer;
        stringBuffer = "";
        return dataReceived;
      }
    }
    return "";

}

void setup() {

  Serial.begin(115200);

  while (!Serial);


  if (!BARO.begin()) {

    Serial.println("Failed to initialize pressure sensor!");

    while (1);

  }

  /*
  if (!HTS.begin()) {

    Serial.println("Failed to initialize humidity temperature sensor!");

    while (1);

  }
  */

    if (!HS300x.begin()) {

    Serial.println("Failed to initialize humidity temperature sensor!");

    while (1);

  }
  
  if (!APDS.begin()) {
    Serial.println("Error initializing APDS-9960 sensor.");
  }
  


  PDM.onReceive(onPDMdata);


  // optionally set the gain, defaults to 20

  // PDM.setGain(30);


  // initialize PDM with:

  // - one channel (mono mode)

  // - a 16 kHz sample rate

  if (!PDM.begin(1, 16000)) {

    Serial.println("Failed to start PDM!");

    while (1);

  }

  if (!IMU.begin()) {

    Serial.println("Failed to initialize IMU!");

    while (1);

  }


  Serial.print("Accelerometer sample rate (Hz): ");

  Serial.print(IMU.accelerationSampleRate()); // Hz

  Serial.println("Block RoomSensor version: 2.2 (february 2025)");
  
 
}


void loop() {

  String incomingString = receiveSerialData();
  if ( incomingString != "" )
  {    
    
    //String s = Serial.readStringUntil('\r\n');
    incomingString.trim();

    if( incomingString.startsWith( "delay" ) )
    {

      char buffer[200];
      
      int ind1 = incomingString.indexOf(':');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). example: delay:200 (ms)" );
        return;
      }
      incomingString.substring(ind1+1).toCharArray( buffer, 200 );      
      delayMs = atoi( buffer );

      Serial.print("Delay set to ");
      Serial.println(delayMs);

    }


    if( incomingString.startsWith( "nbShockSampling" ) )
    {

      char buffer[200];
      
      int ind1 = incomingString.indexOf(':');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). example: nbShockSampling:50 (ms)" );
        return;
      }
      incomingString.substring(ind1+1).toCharArray( buffer, 200 );      
      nbShockSampling = atoi( buffer );

      Serial.print("nbShockSampling set to ");
      Serial.println(nbShockSampling);
    }

      

  }

  Serial.println("-");

  // read the sensor value

  float pressure = BARO.readPressure();
  //float altitude = 44330 * ( 1 - pow(pressure/101.325, 1/5.255) );

  Serial.print("Pressure: "); // hPa
  Serial.println(pressure);

  // temp / humidity

  float temperature = HS300x.readTemperature();
  float humidity    = HS300x.readHumidity();
  
  Serial.print("Temperature: ");
  Serial.println( temperature );
  Serial.print("Humidity: ");
  Serial.println( humidity );

  int r, g, b, a;

  // Read the color.
  if (APDS.colorAvailable()) {
  
    APDS.readColor(r, g, b, a);
  
  

  // Print the values:
  Serial.print("r:");
  Serial.println(r);
  Serial.print("g:");
  Serial.println(g);
  Serial.print("b:");
  Serial.println(b);
  Serial.print("a:");
  Serial.println(a);

  Serial.print("lum visible: ");
  Serial.println(a);
  Serial.print("lum IR+visible: ");
  Serial.println(a);
 
  }

if (APDS.proximityAvailable()) {
    // Read the proximity where:
    // - 0   => close
    // - 255 => far
    // - -1  => error
    int proximity = APDS.readProximity();

    // Print value to the Serial Monitor.
    Serial.print("Proximity: ");
    Serial.println(proximity);
  }

if (samplesRead) {


    // print samples to the serial monitor or plotter

    int max = 0;
    for (int i = 0; i < samplesRead; i++) {
      if ( abs(sampleBuffer[i]) > max ) 
      {
        max = abs(sampleBuffer[i]);
      }
    }

      Serial.print("Sound level: ");
      Serial.println(max);

      // check if the sound value is higher than 500

      if (max>= 50 ){

        digitalWrite(LEDR,LOW);

        digitalWrite(LEDG,HIGH);

        digitalWrite(LEDB,HIGH);

      }

      // check if the sound value is higher than 250 and lower than 500

      if (max>=25 && max < 50){

        digitalWrite(LEDB,LOW);

        digitalWrite(LEDR,HIGH);

        digitalWrite(LEDG,HIGH);

      }

      //check if the sound value is higher than 0 and lower than 250

      if ( max < 25){

        digitalWrite(LEDG,LOW);

        digitalWrite(LEDR,HIGH);

        digitalWrite(LEDB,HIGH);

      }

    


    // clear the read count

    samplesRead = 0;

  }

  float x, y, z;
  float previousX, previousY, previousZ;
  bool firstRead = true;
  float shock = 0;


  int readPauseMs = 5;
  int correctedDelayMs = delayMs - nbShockSampling * readPauseMs;
  if ( correctedDelayMs < 0 )
  {
    correctedDelayMs = 0;
  }

  for ( int i = 0; i< nbShockSampling ; i++ )
  {
    if (IMU.accelerationAvailable())
    {
    
      IMU.readAcceleration(x, y, z);
      if ( firstRead )
      {
        firstRead = false;
      }else
      {
        shock+= abs(x-previousX)+abs(y-previousY)+abs(z-previousZ);
      }


      previousX =x;
      previousY =y;
      previousZ =z;

      /*
      x = 100*x;
      degreesX = map(x, 0, 97, 0, 90);
      Serial.print("Tilting x: ");
      Serial.println(degreesX);

      y = 100*y;
      degreesY = map(y, 0, 97, 0, 90);

      Serial.print("Tilting y: ");
      Serial.println(degreesY);
      
      Serial.print("Raw accel x: ");    
      Serial.println( x );

      Serial.print("Raw accel y: ");    
      Serial.println( y );

      Serial.print("Raw accel z: ");    
      Serial.println( z );
      */
    } 
    delay( readPauseMs );
  }

  Serial.print("Shock: ");
  Serial.println(shock);


 if (IMU.accelerationAvailable())
    {
    
      IMU.readAcceleration(x, y, z);

      x = 100*x;
      degreesX = map(x, 0, 97, 0, 90);
      Serial.print("Tilting x: ");
      Serial.println(degreesX);

      y = 100*y;
      degreesY = map(y, 0, 97, 0, 90);
      
      Serial.print("Tilting y: ");
      Serial.println(degreesY);
      
      Serial.print("Raw accel x: ");    
      Serial.println( x );

      Serial.print("Raw accel y: ");    
      Serial.println( y );

      Serial.print("Raw accel z: ");    
      Serial.println( z );
      
  } 

  Serial.println("end");


  // wait 1 second to print again

  //delay(50); // block compatibility
  delay(correctedDelayMs); // LMT compatibility
}


void onPDMdata() {

  // query the number of bytes available

  int bytesAvailable = PDM.available();


  // read into the sample buffer

  PDM.read(sampleBuffer, bytesAvailable);


  // 16-bit, 2 bytes per sample

  samplesRead = bytesAvailable / 2;

}

#include <Wire.h>

// Lever control / Fabrice de Chaumont

int LED_PIN = 11; // but any pin can be controlled ( nano PWM pins are 9,10,11,3,5,6 on atMega328p )
int LIDAR_PIN = 3;

int currentState = 10;

//Setup
void setup() {
  
  pinMode( LED_PIN, OUTPUT);
  pinMode( LIDAR_PIN, INPUT );
  
  Serial.begin( 115200 );
  Serial.setTimeout( 50 );
  
  digitalWrite( LED_PIN, LOW );
  Serial.println("Lever control started.");
}

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


//Loop
void loop() {

  int r = digitalRead(LIDAR_PIN);
  if ( currentState != r )
  {
    if ( r )
    {
      Serial.println("press");
    }else
    {
      Serial.println("release");
    }
    currentState = r;
  }

  String incomingString = receiveSerialData();
  if ( incomingString != "" )  // read incoming orders  
  { 
    
    incomingString.trim();
    
    if( incomingString.startsWith( "lightOn" ) )
    {

      char buffer[200];
      
      int ind1 = incomingString.indexOf(' ');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). should be: lightOn n(1-3),pwm (0-255) example: lightOn 1,128" );
        return;
      }

      int ind2 = incomingString.indexOf(',');
      if ( ind2 == -1 )
      {
        Serial.println( "Error: argument missing(pos2). should be: lightOn n(1-3),pwm (0-255) example: lightOn 1,128" );
        return;
      }

      int ind3 = incomingString.length();

      incomingString.substring(ind1+1, ind2).toCharArray( buffer, 200 );
      int number = atoi( buffer );

      incomingString.substring(ind2+1, ind3).toCharArray( buffer, 200 );
      int pwm = atoi( buffer );

      Serial.println( incomingString );      
      pinMode( number , OUTPUT); 
      analogWrite( number , pwm ); 
    }
  
  if ( incomingString.startsWith( "lightOff" ) )
    {

      char buffer[200];
      
      int ind1 = incomingString.indexOf(' ');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). should be: lightOff n(1-3)example: lightOff 1" );
        return;
      }

      int ind2 = incomingString.length();

      incomingString.substring(ind1+1, ind2 ).toCharArray( buffer, 200 );

      int number = atoi( buffer );


      Serial.println( incomingString );      
      //Serial.println( number );
      pinMode( number , OUTPUT); // led
      digitalWrite( number , LOW ); 
      


    }

    if ( incomingString.equals( "click" ) )
    {      
      //todo ?
    }

    if ( incomingString.equals( "ping" ) )
    {
      Serial.println("pong");
    }

    if ( incomingString.equals( "hello" ) )
    {
      Serial.println("Hello, i am a *lever* / driver v2.0");
    }
  
  }
    
}


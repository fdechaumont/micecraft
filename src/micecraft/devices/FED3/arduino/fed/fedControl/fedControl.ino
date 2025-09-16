
#include <FED3.h>                                       //Include the FED3 library 
#include <Wire.h>
String sketch = "BLOCK";                                  //Unique identifier text for each sketch
FED3 fed3 (sketch);                                     //Start the FED3 object
Adafruit_SharpMem display(SHARP_SCK, SHARP_MOSI, SHARP_SS, 144, 168);

//Initialize value

int nbLeft = 0;
int nbRight = 0;


//Setup
void setup() {
  
  
  display.begin();
  display.setRotation(3); //Rotate 180°
  display.setTextSize(2);
  display.clearDisplay();
  pinMode(RIGHT_POKE, INPUT_PULLUP); //  RIGHT_POKE Pullup
  pinMode(LEFT_POKE, INPUT_PULLUP); //  RIGHT_POKE Pullup
  
  //fed3.disableSleep();

  fed3.begin();
  //fed3.DisplayPokes = false;
  //fed3.DisplayPo
  Serial.begin(115200); // 57600
  Serial.setTimeout( 50 );
}

boolean tryFeeding = false; // flag to start the feeding
long startFeedingMs = 0;
boolean pelletDelivered = false;
boolean pelletPicked = false;
boolean rightIn= false;
boolean leftIn= false;
int motorStep=1;
boolean previousCheckPelletState = true;
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

  if ( rightIn )
  {
    if (digitalRead(RIGHT_POKE) == HIGH)
    {
      rightIn = false;
      Serial.println("rightOut");
    }
  }else
  {  
    if (digitalRead(RIGHT_POKE) == LOW)
    {
      rightIn = true;
      Serial.println("rightIn");
    }
  }


  if ( leftIn )
  {
    if (digitalRead(LEFT_POKE) == HIGH)
    {
      leftIn = false;
      Serial.println("leftOut");
    }
  }else
  {  
    if (digitalRead(LEFT_POKE) == LOW)
    {
      leftIn = true;
      Serial.println("leftIn");
    }
  }
 
  String incomingString = receiveSerialData();
  if ( incomingString != "" )  // read incoming orders
  { 

    incomingString.trim();
    //Serial.println("I received: ");
    //Serial.println( incomingString );
        
    if ( incomingString.startsWith( "rotation:" ) ) // rotate the feeder wheel, stops if a pellet is delivered
    {   
      //Serial.println( "step1" );
      //fed3.RotateDisk( 20 );
      //fed3.ClearJam();
      //fed3.VibrateJam();
      //fed3.MinorJam();
      
      //Serial.println( incomingString.substring(9,incomingString.length() ) );
      //fed3.stepper.setSpeed( 1000 );
      int rotation = incomingString.substring(9,incomingString.length() ).toInt();
      fed3.RotateDisk( rotation );
      //fed3.stepper.setSpeed(motorSpeed);   // 250
      
      /*
      Serial.println( incomingString.substring(5,incomingString.length() ) );
      motorStep=incomingString.substring(5,incomingString.length() ).toInt();
      Serial.print("motor step set to:");
      Serial.println( motorStep );
      */
      //Serial.println( "step2" );
    }

    if ( incomingString.equals( "feed" ) )
    {
      //Serial.println("feed order received");
      
      if ( checkPellet() )
      {
        Serial.println("pellet already delivered");                
        return;
      }

      if ( tryFeeding == true )
      {
        Serial.println("already feeding");
        return;
      }

      
      tryFeeding = true; //fed3.Feed();
      startFeedingMs = millis();
      pelletDelivered = false;
      pelletPicked = false;
    
      //Serial.println("feed done");  
    }

    if ( incomingString.equals( "hello" ) )
    {
      Serial.println("hello, i am a *fed3* / block-driver v3.2");      
    }

    if ( incomingString.equals( "ping" ) )
    {
      Serial.println("pong");
    }


    if ( incomingString.equals( "cancel feed" ) )
    {
      tryFeeding = false;
      fed3.ReleaseMotor();
    }

    /*
    if ( incomingString.equals( "light" ) )
    {
        fed3.rightPokePixel(10,10,10,0); 
        fed3.leftPokePixel(10,10,10,0); 
    }

    if ( incomingString.equals( "lightleft" ) )
    {        
        fed3.leftPokePixel(10,10,10,0); 
    }

    if ( incomingString.equals( "lightright" ) )
    {        
        fed3.rightPokePixel(10,10,10,0); 
    }
    */


    if ( incomingString.equals( "lightoff" ) )
    {
      fed3.pixelsOff();
    }

    if ( incomingString.indexOf("RGBWdef_") >= 0 ) // adapted from Nicolas Torquet's code
    {
      // incomingString must be like: RGBWdef_R000_G100_B100_W100_SideL
      // Side: l for left, r for right, b for both, c for center, a for all
      int red = incomingString.substring(incomingString.indexOf("_R")+2, 11).toInt();
      int green = incomingString.substring(incomingString.indexOf("_G")+2, 16).toInt();
      int blue = incomingString.substring(incomingString.indexOf("_B")+2, 21).toInt();
      int white = incomingString.substring(incomingString.indexOf("_W")+2, 26).toInt();
      String side = incomingString.substring(incomingString.indexOf("_Side")+5, incomingString.length());
      
      if ( side == "a" )
      {
          fed3.pixelsOn(red, green, blue, white);
          fed3.leftPokePixel(red, green, blue, white);
          fed3.rightPokePixel(red, green, blue, white);
      }

      if ( side == "l" )
      {
          fed3.leftPokePixel(red, green, blue, white);
      }
      if ( side == "r" )
      {
          fed3.rightPokePixel(red, green, blue, white);
      }
      if ( side == "b" )
      {
          fed3.leftPokePixel(red, green, blue, white);
          fed3.rightPokePixel(red, green, blue, white);
      }
      if ( side == "c" )
      {
          fed3.pixelsOn(red, green, blue, white);
      }
      if ( side == "cr" )
      {
          fed3.rightPixel(red, green, blue, white);          
      }
      if ( side == "cl" )
      {
          fed3.leftPixel(red, green, blue, white);          
      }

    }

    /*

    if ( incomingString.equals( "clickflash" ) )
    {      
      fed3.Click();
      fed3.rightPokePixel(0,0,10,0); 
      fed3.leftPokePixel(0,0,10,0);
      fed3.pixelsOn(0,0,10,0); // pixel at the bottom of the device
      delay(10);
      fed3.pixelsOff();
    }
    */


    if ( incomingString.equals( "click" ) )
    {      
      fed3.Click();
    }

    //delay(10);
    
  }

  manageFeeding();

  if ( !pelletDelivered )
  {
    if ( checkPellet() == true )
    {
      pelletDelivered = true;
      Serial.println("pellet delivered");
    }
  }

  if ( !pelletPicked && pelletDelivered )
  {
    if ( checkPellet() == false )
    {
      pelletPicked = true;
      Serial.println("pellet picked");
    }
  }

  if ( checkPellet() != previousCheckPelletState )
  {
    if ( checkPellet() == true )
    {
      Serial.println("pellet present");
      previousCheckPelletState = true;
    }else
    {
      Serial.println("pellet not present");
      previousCheckPelletState = false;
    }
  }

}

void manageFeeding()
{
  if ( !tryFeeding )
  {
    return;
  }
  
  digitalWrite (MOTOR_ENABLE, HIGH);  //Enable motor driver
  fed3.stepper.step(motorStep);
  if ( checkPellet() )
  {
    fed3.ReleaseMotor ();
    tryFeeding = false;
  }

  /*
  if ( millis() - startFeedingMs > 60000 )
  {
    Serial.println("feed timeout");  
    fed3.ReleaseMotor ();
    tryFeeding = false;
  }
  */
  
}

boolean checkPellet()
{
  for (int j = 0; j < 20; j++)
  {
    delayMicroseconds(100);   
    if (digitalRead (PELLET_WELL) == LOW)
    {
      delayMicroseconds(100);
      // Debounce
      if (digitalRead (PELLET_WELL) == LOW)
      {        
        return true;
      }
    }
  }
  return false;
}

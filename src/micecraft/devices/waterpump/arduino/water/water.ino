/*
 * Water
 * Fab March 2022
 */

// nano PWM out pins are : d3, d5, d6, d9, d10

int pinLight = 3; // pin D3
int pinLight2 = 5; // pin D5
int pinPump = 6; // pin D6
int pinFlush = 7; // pin D7
int pinAptic = 8; // aptic feedback
int pinLiddar = 9; // pin D9
int pinPump2 = 11; // pin D11
int pinPumpWash = 12; // pin D11

int pinBeeper = 10;

int frequencyBeeper = 8000;

int liddarState = 10;
int liddarDebounceDelayMs = 300;
unsigned long lastliddarDebounceTime = 0;

void setup() {

  // delay( 500 ); // may try this to avoid problem at USB discovery ( some people say that if the arduino send info, it can be seen as mouse pointer device ?)

  pinMode( pinPump , OUTPUT); // filling pump
  pinMode( pinFlush , OUTPUT); // flushing pump
  pinMode( pinPump2 , OUTPUT); 
  pinMode( pinPumpWash , OUTPUT);
  pinMode( pinAptic , OUTPUT );

  pinMode( 13 , OUTPUT); // led when pump is running
  pinMode( pinLight , OUTPUT); // led
  pinMode( pinLight2 , OUTPUT); // led
  
  pinMode( pinLiddar , INPUT); // led
  

  Serial.begin(115200 );
  //Serial.begin( 9600 );
  Serial.setTimeout( 10 );
  Serial.println("init pump...");
  Serial.println("ready");
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


void loop() {

/* test
delay( 300 );
Serial.println( "-----");
  digitalWrite( 13, HIGH );
      Serial.println( "step 6");
      //analogWrite( pinPump , 255 );  // 80
      Serial.println( "step 7");
      delay( 20 );
      Serial.println( "step 8");
      //digitalWrite( pinPump, LOW );
      Serial.println( "step 9");
      digitalWrite( 13, LOW );
      Serial.println( "step 10");
  */
  
  String incomingString = receiveSerialData();
  if ( incomingString != "" ) {    
    
    //String s = Serial.readStringUntil('\r\n');
    incomingString.trim();

    if ( incomingString.equals( "ping" ) )
    {
      Serial.println("pong");
    }

    /*
    if ( incomingString.equals( "lightOn" ) )
    {
      //digitalWrite( pinLight, HIGH );
      analogWrite( pinLight , 128 );  // 80
      Serial.println("light On");
    }
    */

    if ( incomingString.startsWith( "click" ) )
    {
      tone ( pinBeeper, frequencyBeeper );
      delay(20);
      noTone( pinBeeper );
      Serial.println("click");
    }

    if ( incomingString.startsWith( "frequency:" ) )
    {
      //Serial.println ( incomingString.substring(9,incomingString.length() ) );
      int reading = incomingString.substring(10,incomingString.length() ).toInt();
      if ( reading > 0 )
      {
        frequencyBeeper = reading;
        Serial.print("Frequency set to ");
        Serial.println( frequencyBeeper );
      }
    }

  if( incomingString.startsWith( "lightOn" ) )
    {

      char buffer[200];
      
      int ind1 = incomingString.indexOf(',');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). should be: lightOn,pwm (0-255) example: lightOn,128" );
        return;
      }

      int ind2 = incomingString.length();

      incomingString.substring(ind1+1, ind2).toCharArray( buffer, 200 );

      int pwm = atoi( buffer );

      Serial.println( incomingString );      
      analogWrite( pinLight , pwm );  // 80
      
    }


    if ( incomingString.equals( "lightOff" ) )
    {
      digitalWrite( pinLight, LOW );
      Serial.println("light Off");
    }

  if( incomingString.startsWith( "light2On" ) )
    {

      char buffer[200];
      
      int ind1 = incomingString.indexOf(',');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). should be: light2On,pwm (0-255) example: light2On,128" );
        return;
      }

      int ind2 = incomingString.length();

      incomingString.substring(ind1+1, ind2).toCharArray( buffer, 200 );

      int pwm = atoi( buffer );

      Serial.println( incomingString );      
      analogWrite( pinLight2 , pwm );  // 80
      
    }
   
   if ( incomingString.equals( "light2Off" ) )
    {
      digitalWrite( pinLight2, LOW );
      Serial.println("light2 Off");
    }


    if ( incomingString.equals( "hello" ) )
    {
      Serial.println("Hello, I am a *water pump* / Driver v2.5");
    }

    if( incomingString.startsWith( "pump" ) )
    {

      char buffer[200];
      
      int ind1 = incomingString.indexOf(',');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). should be: pump,pwm (0-255),duration (ms) example: pump,255,1000" );
        return;
      }

      String txt = incomingString.substring(5, ind1);

      int ind2 = incomingString.indexOf(',', ind1+1 );

      if ( ind2 == -1 )
      {
        Serial.println( "Error: argument missing(pos2). should be: pump,pwm (0-255),duration (ms) example: pump,255,1000" );
        return;
      }
      incomingString.substring(ind1+1, ind2).toCharArray( buffer, 200 );

      int pwm = atoi( buffer );
      incomingString.substring(ind2+1).toCharArray( buffer, 200 );

      int duration = atoi( buffer );

      Serial.println( incomingString );
      digitalWrite( 13, HIGH );
      analogWrite( pinPump , pwm );  // 80
      delay(duration);
      digitalWrite( pinPump, LOW );
      digitalWrite( 13, LOW );

      
      
    }

    if( incomingString.startsWith( "flush" ) )
    {
      char buffer[200];
      
      int ind1 = incomingString.indexOf(',');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). should be: flush,pwm (0-255),duration (ms) example: flush,255,1000" );
        return;
      }
      String txt = incomingString.substring(5, ind1);

      int ind2 = incomingString.indexOf(',', ind1+1 );
      if ( ind2 == -1 )
      {
        Serial.println( "Error: argument missing(pos2). should be: flush,pwm (0-255),duration (ms) example: flush,255,1000" );
        return;
      }
      incomingString.substring(ind1+1, ind2).toCharArray( buffer, 200 );

      int pwm = atoi( buffer );
      incomingString.substring(ind2+1).toCharArray( buffer, 200 );

      int duration = atoi( buffer );

      Serial.println( incomingString );

      analogWrite( pinFlush , 255 );  // 80 // the PWM is set to maximum, we ignore the PWM parameter ( also because the pin is not PWM )
      delay(duration);
      digitalWrite( pinFlush, LOW );
      
    }


    if( incomingString.startsWith( "wash" ) )
    {
      char buffer[200];
      
      int ind1 = incomingString.indexOf(',');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). should be: wash,pwm (0-255),duration (ms) example: wash,255,1000" );
        return;
      }
      String txt = incomingString.substring(5, ind1);

      int ind2 = incomingString.indexOf(',', ind1+1 );
      if ( ind2 == -1 )
      {
        Serial.println( "Error: argument missing(pos2). should be: wash,pwm (0-255),duration (ms) example: wash,255,1000" );
        return;
      }
      incomingString.substring(ind1+1, ind2).toCharArray( buffer, 200 );

      int pwm = atoi( buffer );
      incomingString.substring(ind2+1).toCharArray( buffer, 200 );

      int duration = atoi( buffer );

      Serial.println( incomingString );

      analogWrite( pinPumpWash , 255 );  // 80 // the PWM is set to maximum, we ignore the PWM parameter ( also because the pin is not PWM )
      delay(duration);
      digitalWrite( pinPumpWash, LOW );
      
    }

    if( incomingString.startsWith( "p2" ) )
    {
      char buffer[200];
      
      int ind1 = incomingString.indexOf(',');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). should be: p2,pwm (0-255),duration (ms) example: p2,255,1000" );
        return;
      }
      String txt = incomingString.substring(5, ind1);

      int ind2 = incomingString.indexOf(',', ind1+1 );
      if ( ind2 == -1 )
      {
        Serial.println( "Error: argument missing(pos2). should be: p2,pwm (0-255),duration (ms) example: p2,255,1000" );
        return;
      }
      incomingString.substring(ind1+1, ind2).toCharArray( buffer, 200 );

      int pwm = atoi( buffer );
      incomingString.substring(ind2+1).toCharArray( buffer, 200 );

      int duration = atoi( buffer );

      Serial.println( incomingString );

      analogWrite( pinPump2 , 255 );  // 80 // the PWM is set to maximum, we ignore the PWM parameter ( also because the pin is not PWM )
      delay(duration);
      digitalWrite( pinPump2, LOW );
      
    }

    if( incomingString.startsWith( "aptic" ) )
    {

      char buffer[200];
      
      int ind1 = incomingString.indexOf(',');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). should be: aptic,pwm (0-255),duration (ms) example: aptic,255,1000" );
        return;
      }

      String txt = incomingString.substring(5, ind1);

      int ind2 = incomingString.indexOf(',', ind1+1 );

      if ( ind2 == -1 )
      {
        Serial.println( "Error: argument missing(pos2). should be: aptic,pwm (0-255),duration (ms) example: aptic,255,1000" );
        return;
      }
      incomingString.substring(ind1+1, ind2).toCharArray( buffer, 200 );

      int pwm = atoi( buffer );
      incomingString.substring(ind2+1).toCharArray( buffer, 200 );

      int duration = atoi( buffer );

      Serial.println( incomingString );
      digitalWrite( 13, HIGH );
      analogWrite( pinAptic , pwm );  // 80
      delay(duration);
      digitalWrite( pinAptic, LOW );
      digitalWrite( 13, LOW );
  
    }

    
  } // end of reading incoming messages
  
  // liddar section
  {
    int r = digitalRead(pinLiddar);
    
    if ( liddarState == r )
    {      
      lastliddarDebounceTime = millis();
    }
    
    if ((millis() - lastliddarDebounceTime) > liddarDebounceDelayMs)
    {
      if ( liddarState != r )
      {
        if ( r )
        {
          Serial.println("animal out");
        }else
        {
          Serial.println("animal in");
        }
        liddarState = r;
      }
    }
  }
  
}


      /*
      char buffer[20];
      int ind1 = incomingString.indexOf(',');
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos1). should be: flush,pwm (0-255),duration (ms) example: flush,255,1000" );
        return;
      }
      String txt = incomingString.substring(5, ind1);
      //int ind2 = incomingString.indexOf(',', ind1+1 );
      if ( ind1 == -1 )
      {
        Serial.println( "Error: argument missing(pos2). should be: flush,pwm (0-255),duration (ms) example: flush,255,1000" );
        return;
      }
      incomingString.substring(5, ind1).toCharArray( buffer, 20 );
      int pwm = atoi( buffer );
      incomingString.substring(ind1+1).toCharArray( buffer, 20 );
      int duration = atoi( buffer );

      //Serial.println( pwm );
      //Serial.println( duration );
      Serial.println( incomingString );
      //digitalWrite( 13, HIGH );
      analogWrite( pinFlush , pwm );  // 80
      delay(duration);
      digitalWrite( pinFlush, LOW );
      //digitalWrite( 13, LOW );
      */

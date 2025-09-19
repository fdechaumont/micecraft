// Arduino balance and lidar control for gate by Fabrice de Chaumont

#include "HX711.h" // use HX711 by Rob Tillaart 0.3.9

// HX711 circuit wiring
const int broche_DT = 3;
const int broche_SCK = 2;

// pins for optic readers
const int pinDoorAExt = 6;
const int pinDoorAIn = 7;
const int pinDoorBIn = 8;
const int pinDoorBExt = 9;

HX711 balance;

void setup() {
  Serial.begin(115200 );
  Serial.setTimeout( 10 );
  Serial.println("init Gate arduino...");
  Serial.println("Init scale...");

  balance.begin(broche_DT, broche_SCK);

  while (!balance.is_ready())
  {
    ;
  }

  balance.set_scale(2000); 
  balance.tare(); 
  Serial.println("Scale initialized.");

  pinMode( pinDoorAExt, INPUT);
  pinMode( pinDoorAIn, INPUT);
  pinMode( pinDoorBIn, INPUT);
  pinMode( pinDoorBExt, INPUT);
 
  Serial.println("ready");

}

void loop() {

  Serial.println("w:"+ String( balance.get_units(1) ) );
  //Serial.println(" grammes");
  delay(10);
  if (Serial.available() > 0) {    
    Serial.readString();
    Serial.println("tare");
    balance.tare();
    Serial.println("tare ok");
  }

  // read and send LIDAR infos:
  
  String lidar = "lidar:";
  lidar+= !digitalRead( pinDoorAExt );
  lidar+= !digitalRead( pinDoorAIn );
  lidar+= !digitalRead( pinDoorBIn );
  lidar+= !digitalRead( pinDoorBExt );

  Serial.println( lidar );







  


}

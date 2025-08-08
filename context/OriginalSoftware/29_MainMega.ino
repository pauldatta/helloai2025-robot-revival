// MT = Main Teensy / Mega

#include <FastLED.h>
#include <PololuMaestro.h>
#include <SoftwareSerial.h>

// SERVOS
#define tempRXpin 12
#define servoControllerTXpin 2

SoftwareSerial maestroSerial(tempRXpin, servoControllerTXpin); // RX, TX
MiniMaestro maestro(maestroSerial);


// ----------------------------
// Alive LED
boolean aliveState = false;
unsigned int aliveInterval = 600;
unsigned long aliveLED_OT = 0;


// ----------------------------
// Sensors
int distanceSensor2_pin = A1;
int detectedDistance2 = 0;
int sensedPerson_Count = 0;
int sensedPerson_MaxCount = 10;

// averaging
const int numReadings = 10;



int readings_2[numReadings];      
int readIndex_2 = 0;              
int total_2 = 0;                 
int average_2 = 0; 
// ----------------------------



// Serial Command
/*
#define STRING_BUF_NUM 64
String cmd[STRING_BUF_NUM];
int commandNum = -1;
*/


// Scene
boolean toggleState = false;
unsigned long toggleServoInterval = 3000;


// Time
unsigned long OT = 0;
unsigned long sceneOT = 0;




// ----------------------------
// LEDs
// Frontal Artwork lights
#define NUM_LEDS_ledartwork 127
#define DATA_PIN_ledartwork 3
CRGB leds_artwork[NUM_LEDS_ledartwork];


// Google Map
#define NUM_LEDS_ledmap 79
#define DATA_PIN_ledmap 4
CRGB leds_map[NUM_LEDS_ledmap];


// LOGO BACK
#define NUM_LEDS_ledback 360
#define DATA_PIN_ledback 5
CRGB leds_logo_back[NUM_LEDS_ledback];


// G-TAIL leds
#define NUM_LEDS_ledlogoartwork 21
#define DATA_PIN_ledlogoartwork 6
CRGB leds_logoartwork[NUM_LEDS_ledlogoartwork];


// LOGO FRONT - its a data pin
int ledfront_datapin_show = 7;
int ledfront_datapin_hide = 8;

boolean inform_SecMega = true;


// Logo color count
// red | yellow | green | blue
int count_logoR = 0;
int count_logoY = 0;
int count_logoG = 0;
int count_logoB = 0;

int count_main = 0;

// Logo end color index
int endIdx_logoB = 548;


// Logo Leds
// speed of filling up the logoleds
int numLeds_aniFirstSpeed = 4;//8;
int numLeds_aniRestSpeed = 3;//7;

unsigned long interval_logo = 25; // interval of update
unsigned long OT_logo = 0;

int ledfrontled_idx = 359;
int ledDim_value = 130;

// frontal led brightness
int frontalLED_brightness = 210;
int frontalLED_brightnessNow = 210;
int frontalLED_brightnessNowAdd = 0;

// new serial command
int commandNum = 0;


// -----------------------------
// STATE
// Declare scenes
enum googleScene { 
  NOTHING,
  
  INIT,
  RUN_SENSOR,
  DETECTED_PERSON,

  HOME_SIGN_SHOW,
  HOME_SIGN_REST,
  HOME_SIGN_HIDE,
  
  AUM_CRY_START,
  AUM_CRY_REST,
  AUM_CRY_STOP,
  
  AUNTY_SHOW,
  AUNTY_REST,
  AUNTY_HIDE,
  
  PHONE_RING,
  PHONE_REST,
  PHONE_HIDE,
  
  LED_MAP_SHOW,
  LED_MAP_REST,
  LED_MAP_HIDE,
  LED_MAP_HIDE_REST,

  LED_LOGO_SHOW,
  LED_LOGO_SHOW_NEXT,
  LED_LOGO_SHOW_DONE,
  LED_LOGO_HIDE,

  ARTWORK_SHOW,
  ARTWORK_HIDE
};
googleScene gs = INIT;  //LED_ARTWORK; //INIT;
// -----------------------------






void setup() {
  maestroSerial.begin(9600);

  Serial.begin(9600);

  // Alive pin
  pinMode(13, OUTPUT);  

  // LOGO FRONT - data pin
  pinMode(ledfront_datapin_show, OUTPUT);
  pinMode(ledfront_datapin_hide, OUTPUT);

  // init pin
  // clear front led!
  digitalWrite(ledfront_datapin_show, LOW);
  digitalWrite(ledfront_datapin_hide, HIGH);

  // LEDs
  // 1. Logo
  FastLED.addLeds<WS2812B, DATA_PIN_ledback, GRB>(leds_logo_back, 0, NUM_LEDS_ledback);
  // FastLED.addLeds<WS2812B, DATA_PIN_ledfront, GRB>(leds_logo, NUM_LEDS_ledback, NUM_LEDS_ledfront);

  // 2. Google Map
  FastLED.addLeds<WS2812B, DATA_PIN_ledmap, GRB>(leds_map, NUM_LEDS_ledmap);

  // 3. Frontal Artwork Lighting
  FastLED.addLeds<WS2812B, DATA_PIN_ledartwork, GRB>(leds_artwork, NUM_LEDS_ledartwork);

  // 4. G-tail
  FastLED.addLeds<WS2812B, DATA_PIN_ledlogoartwork, GRB>(leds_logoartwork, NUM_LEDS_ledlogoartwork);
  
  FastLED.clear();
  FastLED.show();

  delay(1000);

  // set speed / Accel
  maestro.setSpeed(0, 100);
  maestro.setSpeed(1, 50); // aum cry move slower
  maestro.setSpeed(2, 10);
  maestro.setSpeed(3, 100);
  maestro.setSpeed(4, 100);
  
  maestro.setAcceleration(0, 10); // 0 - 255
  maestro.setAcceleration(1, 10);
  maestro.setAcceleration(2, 5);
  maestro.setAcceleration(3, 10);
  maestro.setAcceleration(4, 10);

  maestro.setTarget(0, 7900); // HOME: 7900 - down/keep . | 4000- vertically up
  maestro.setTarget(1, 6000); // AUM Cry: 
  maestro.setTarget(2, 7100); // MARKET Aunty : 8000 is on right, 400 is on left
  maestro.setTarget(3, 4000); // PHONE: 4000 - phone down | 5500 - phone up
  maestro.setTarget(4, 8000);  // BK MARKET: 8000 - down/keep | 400 - vertically up



  // averaging - init
  for (int i = 0; i < numReadings; i++) {
    readings_2[i] = 0;
  }


  // do frontal artwork light
  for(int i=0; i<NUM_LEDS_ledartwork; i++) {
    leds_artwork[i] = CHSV(28,160,   frontalLED_brightness);
  }
  FastLED.show();
  
  
  
  delay(1000);
}



void loop() {
  
  // alive led
  if (millis() - aliveLED_OT > aliveInterval) {
    aliveLED_OT = millis();
    if (aliveState) {
      digitalWrite(13, LOW);
    } else {
      digitalWrite(13, HIGH);
    }
    aliveState = !aliveState;
  }


  // --------------------------------------------------
  if (Serial.available()) {

      // look for the next valid integer in the incoming serial stream:
      commandNum = Serial.parseInt();


      // look for the newline. That's the end of your sentence:
      //if (Serial.read() == '\n') {
  
        Serial.print("commandNum > ");
        Serial.println(commandNum);


        if(commandNum == 1) {
          gs = RUN_SENSOR;


      
        } else if (commandNum == 2) {
          gs = HOME_SIGN_SHOW;

        } else if (commandNum == 3) {
          gs = HOME_SIGN_HIDE;

          
          
        } else if (commandNum == 4) {
          gs = AUM_CRY_START;

        } else if (commandNum == 5) {
          gs = AUM_CRY_STOP;


        
          
        } else if (commandNum == 6) {
          gs = AUNTY_SHOW;
        } else if (commandNum == 7) {
          gs = AUNTY_HIDE;


          
        } else if (commandNum == 8) {
          gs = PHONE_RING;
        } else if (commandNum == 9) {
          gs = PHONE_HIDE;


          
        } else if (commandNum == 10) {
          gs = LED_MAP_SHOW;

        }  else if (commandNum == 11) {
          gs = LED_MAP_HIDE;



          
        } else if (commandNum == 12) {
          gs = LED_LOGO_SHOW;

        } else if (commandNum == 13) {
          gs = LED_LOGO_HIDE;
          

        } else if (commandNum == 14) {
          // artwork led
          gs = ARTWORK_SHOW;
          
        } else if (commandNum == 15) {
          // artwork leds
          gs = ARTWORK_HIDE;
        }


        // init once, when there is a serial command
        // init time
        sceneOT = millis();
        OT_logo = millis();

        // init vars
        count_logoR = 0;
        count_logoY = 0;
        count_logoG = 0;
        count_logoB = 0;

        count_main = 0;

        //
        toggleState = true;

        // 
        sensedPerson_Count = 0;


        // 
        frontalLED_brightnessNow = 210;
        frontalLED_brightnessNowAdd = 0;

        // set speed / accel
        // set speed / Accel
        maestro.setSpeed(0, 100);
        maestro.setSpeed(1, 50); // aum cry move slower
        maestro.setSpeed(2, 30);
        maestro.setSpeed(3, 100);
        maestro.setSpeed(4, 100);
        
        maestro.setAcceleration(0, 10); // 0 - 255
        maestro.setAcceleration(1, 10);
        maestro.setAcceleration(2, 5);
        maestro.setAcceleration(3, 10);
        maestro.setAcceleration(4, 10);

        // init data pins
        digitalWrite(ledfront_datapin_show, LOW);
        digitalWrite(ledfront_datapin_hide, LOW);


        inform_SecMega = true;

  
      //}
  }

  // --------------------------------------------------


  switch (gs) {
    
    case NOTHING: {
      // do nothing
    } break;



    case ARTWORK_SHOW:{
      frontalLED_brightnessNowAdd += 3;
      
      for(int i=0; i<NUM_LEDS_ledartwork; i++) {
        leds_artwork[i] = CHSV(28,160,   frontalLED_brightnessNowAdd);
      }
      delay(1);
      FastLED.show();

      if (frontalLED_brightnessNowAdd > frontalLED_brightness) { 
        frontalLED_brightnessNowAdd = frontalLED_brightness;

        gs = NOTHING;
      }
      
    } break;
    

    case ARTWORK_HIDE:{
      frontalLED_brightnessNow -= 3;
      if (frontalLED_brightnessNow < 0) { frontalLED_brightnessNow = 0; }
      
      for(int i=0; i<NUM_LEDS_ledartwork; i++) {
        leds_artwork[i] = CHSV(28,160,   frontalLED_brightnessNow);
      }
      delay(1);
      FastLED.show();

      if (frontalLED_brightnessNow <= 0) { 
        frontalLED_brightnessNow=0;

        gs = NOTHING;
      }
    } break;




    
    case INIT:{
      // init this LOGO FRONT data pin
      digitalWrite(ledfront_datapin_show, LOW);
      digitalWrite(ledfront_datapin_hide, LOW);
    } break;


    
    

    case RUN_SENSOR:{
      // Serial.println("");
      
      // Sensors 
      total_2 = total_2 - readings_2[readIndex_2];

      detectedDistance2 = analogRead(distanceSensor2_pin);

      readings_2[readIndex_2] = detectedDistance2;
      total_2 = total_2 + readings_2[readIndex_2];
      readIndex_2++;
      if (readIndex_2 >= numReadings) { readIndex_2 = 0;}
      average_2 = total_2 / numReadings;

      
      delay(50);
      
      Serial.print("dist=");
      Serial.print(detectedDistance2);
      Serial.print(" | ave=");
      Serial.println(average_2);

      // with glass
      // no one is 720
      // <500 then starts
      
      if (average_2 < 500) {
        sensedPerson_Count++;
        
        if (sensedPerson_Count > sensedPerson_MaxCount) {
          // MC = Master Controller
          Serial.println("pDetected");
          gs = DETECTED_PERSON;
        }
      }
    } break;



    case DETECTED_PERSON:{
      // Serial.println("DETECTED...");
    } break;





    // ==============================================
    // Mechanical Scenes
    // ==============================================
    case HOME_SIGN_SHOW:{
      // show
      maestro.setTarget(0, 4000);
      delay(350);
      maestro.setTarget(0, 4500);
      delay(350);

      maestro.setTarget(0, 4000);
      delay(350);
      maestro.setTarget(0, 4500);
      delay(350);

      maestro.setTarget(0, 4000);
      delay(350);
      maestro.setTarget(0, 4500);
      delay(350);

      maestro.setTarget(0, 4000);

      gs = HOME_SIGN_REST;
    } break;

    case HOME_SIGN_REST:{
      maestro.setTarget(0, 4000);
    } break;





    // --------------------------------------
    // HOME SIGNAGE
    // --------------------------------------
    case HOME_SIGN_HIDE:{
      // hide
      maestro.setTarget(0, 7900);
      // Serial.println("home sign 2");
    } break;




    // --------------------------------------
    // AUM CRY
    // --------------------------------------
    case AUM_CRY_START:{
      maestro.setTarget(1, 5500);
      delay(600);
      maestro.setTarget(1, 6000);
      delay(600);
      
      maestro.setTarget(1, 5300);
      delay(600);
      maestro.setTarget(1, 6000);
      delay(600);
      
      maestro.setTarget(1, 5500);
      delay(600);
      maestro.setTarget(1, 6000);
      delay(600);



      maestro.setTarget(1, 5500);
      delay(600);
      maestro.setTarget(1, 6000);
      delay(600);
      
      maestro.setTarget(1, 5300);
      delay(600);
      maestro.setTarget(1, 6000);
      delay(600);
      
      maestro.setTarget(1, 5500);
      delay(600);
      maestro.setTarget(1, 6000);
      delay(600);
      

      gs = AUM_CRY_REST;
    } break;

    case AUM_CRY_REST:{
      maestro.setTarget(1, 6000);
    } break;

    case AUM_CRY_STOP:{
      maestro.setTarget(1, 6000);
    } break;




    // --------------------------------------
    // MARKET
    // --------------------------------------
    case AUNTY_SHOW:{
      maestro.setTarget(2, 6000);
      delay(6000);

      maestro.setTarget(2, 4100);
      delay(600);

      gs = AUNTY_REST;
    } break;

    case AUNTY_REST:{
      
    } break;

    case AUNTY_HIDE:{
      maestro.setTarget(2, 7100);
    } break;




    // --------------------------------------
    // TELEPHONE
    // --------------------------------------
    case PHONE_RING:{
      // PHONE: 4000 - phone down | 5500 - phone up

      // 1. phone ring
      maestro.setTarget(3, 4000);
      delay(300);
      
      maestro.setTarget(3, 4300);
      delay(200);

      maestro.setTarget(3, 4000);
      delay(350);

      maestro.setTarget(3, 4500);
      delay(250);

      maestro.setTarget(3, 4000);
      delay(300);

      maestro.setTarget(3, 4500);
      delay(250);

      maestro.setTarget(3, 4100);
      delay(300);

      // 2. phone raised
      maestro.setTarget(3, 5500);

      // rest
      gs = PHONE_REST;
    } break;

    case PHONE_REST:{
      // do nothing
    } break;

    case PHONE_HIDE:{
      maestro.setTarget(3, 4000);
    } break;





    // --------------------------------------
    // LED GOOGLE MAP
    // --------------------------------------
    case LED_MAP_SHOW:{
      for(int i=0; i<35; i++) {
        leds_map[i] = CRGB::Blue;
        delay(20);
        FastLED.show();
      }
      
      for(int i=35; i<NUM_LEDS_ledmap; i++) {
        leds_map[i] = CRGB::Blue;
        delay(20);
        FastLED.show();
      }
      
      
      // show BK market sign
      maestro.setTarget(4, 4000);
      delay(350);
      maestro.setTarget(4, 4500);
      delay(350);

      maestro.setTarget(4, 4000);
      delay(350);
      maestro.setTarget(4, 4500);
      delay(350);

      maestro.setTarget(4, 4000);
      delay(350);
      maestro.setTarget(4, 4500);
      delay(350);

      maestro.setTarget(4, 4000);
      delay(350);
      maestro.setTarget(4, 4500);
      delay(350);

      maestro.setTarget(4, 4000);
      delay(350);
      maestro.setTarget(4, 4500);
      delay(350);

      maestro.setTarget(4, 4000);

      gs = LED_MAP_REST;
    } break;

    case LED_MAP_REST:{
      maestro.setTarget(4, 4500);
    } break;


    case LED_MAP_HIDE:{
      // black out led map
      for(int i=0; i<NUM_LEDS_ledmap; i++) {
        leds_map[i] = 0;
      }
      FastLED.show();

      // hide BK market sign
      maestro.setTarget(4, 8000);

      gs = LED_MAP_HIDE_REST;
    } break;


    case LED_MAP_HIDE_REST:{
      // do nothing
    } break;








    // --------------------------------------
    // LED LOGO
    // --------------------------------------
    case LED_LOGO_SHOW:{
      
      frontalLED_brightnessNow -= 3;
      if (frontalLED_brightnessNow < 0) { frontalLED_brightnessNow = 0; }
      
      for(int i=0; i<NUM_LEDS_ledartwork; i++) {
        leds_artwork[i] = CHSV(28,160,   frontalLED_brightnessNow);
      }
      delay(1);
      FastLED.show();

      if (frontalLED_brightnessNow <= 0) { 
        frontalLED_brightnessNow=0;

        gs = LED_LOGO_SHOW_NEXT;
      }

    } break;
    

    
    case LED_LOGO_SHOW_NEXT:{  
      if (millis() - OT_logo > interval_logo) {
        OT_logo = millis();


        // When the first red had filled the back, tell other mega to start lightup
        if (inform_SecMega) {
          inform_SecMega = false;
         
          //tempc++;
          //Serial.println(tempc);
          
          // trigger pin 7 data pin
          digitalWrite(ledfront_datapin_show, HIGH);
          digitalWrite(ledfront_datapin_hide, LOW);
        }
        


        // 1. start RED color
        if (count_main > 5) {

          if (count_logoR < ledfrontled_idx) {
            
            for(int i=0; i<numLeds_aniFirstSpeed; i++) {
              leds_logo_back[count_logoR] = CHSV(0, 255, 255);            
              count_logoR++;
            }
            
          } else {
          }
          
        }


        // 2. start YELLOW color
        if (count_main > 35) {
          
          if (count_logoY < ledfrontled_idx) {

            for(int j=0; j<numLeds_aniRestSpeed; j++) {
              leds_logo_back[count_logoY] = CHSV(64, 255, 255);
              count_logoY++;
            }
            
          } else {
          }
          
        }


        // 3. start GREEN color
        if (count_main > 80) {
          
          if (count_logoG < ledfrontled_idx) {

            for(int k=0; k<numLeds_aniRestSpeed; k++) {
              leds_logo_back[count_logoG] = CHSV(100, 255, 255);
              count_logoG++;
            }
            
          } else {
          }
          
        }


        // 4. start BLUE color
        if (count_main > 130) {
          
          if (count_logoB < ledfrontled_idx) {

            for(int l=0; l<numLeds_aniRestSpeed; l++) {
              leds_logo_back[count_logoB] = CHSV(160, 255, 255);
              count_logoB++;
            }

          } else {
            
            // **** once green color is done, means logo is all done ****
            gs = LED_LOGO_SHOW_DONE;
          }
          
        }


        // ** logo artowrk led to follow the back led
        for(int i=0; i<NUM_LEDS_ledlogoartwork; i++) {
          leds_logoartwork[NUM_LEDS_ledlogoartwork-i] = leds_logo_back[i];
        }

        FastLED.show();
        count_main++;
      }
       
    } break;



    case LED_LOGO_SHOW_DONE:{
      // do nothing for now
      delay(2000);
      digitalWrite(ledfront_datapin_show, LOW);
      digitalWrite(ledfront_datapin_hide, LOW);
    } break;

    




    case LED_LOGO_HIDE:{
      // init vars
      inform_SecMega = true;
      count_main = 0;

      count_logoR = 0;
      count_logoY = 0;
      count_logoG = 0;
      count_logoB = 0;

      OT_logo = millis();
      
      // clear LOGO BACK
      for(int i=0; i<NUM_LEDS_ledback; i++) {
          leds_logo_back[i] = 0;
      }
      
      // ** logo artowrk led to follow the back led
      for(int i=0; i<NUM_LEDS_ledlogoartwork; i++) {
        leds_logoartwork[i] = 0;
      }
      FastLED.show();


      // trigger pin 7 data pin - low
      digitalWrite(ledfront_datapin_hide, HIGH);
      digitalWrite(ledfront_datapin_show, LOW);
      delay(500);
      digitalWrite(ledfront_datapin_hide, LOW);
      digitalWrite(ledfront_datapin_show, LOW);
    } break;

    
  }


  
}






/*
// ----------------------------------------------------
// . HELPER
void split(String data, char separator, String* temp) {
  int cnt = 0;
  int get_index = 0;

  String copy = data;
  
  while(true) {
    get_index = copy.indexOf(separator);

    if(-1 != get_index) {
      temp[cnt] = copy.substring(0, get_index);

      copy = copy.substring(get_index + 1);
    } else {
      temp[cnt] = copy.substring(0, copy.length());
      break;
    }
    ++cnt;
    
  }
  
}
*/

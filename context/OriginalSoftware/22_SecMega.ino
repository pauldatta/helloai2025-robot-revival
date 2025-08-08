#include <FastLED.h>



// ----------------------------
// Alive LED
boolean aliveState = false;
unsigned int aliveInterval = 600;
unsigned long aliveLED_OT = 0;




// Time
unsigned long OT = 0;
unsigned long sceneOT = 0;




// ----------------------------
// LEDs
// logo LEDs | total bulbs -> 1080
#define NUM_LEDS_ledfront 1080
#define DATA_PIN_ledfront 2
CRGB leds_logo_front[NUM_LEDS_ledfront];


// LOGO FRONT - its a data pin
int ledfront_datapinIn_Show = 3;
int ledfront_datapinIn_Hide = 4;

boolean fromMainMega_frontLED_showState = false;
boolean fromMainMega_frontLED_hideState = false;


// Logo color count
// red | yellow | green | blue
int count_logoR = 0;
int count_logoY = 0;
int count_logoG = 0;
int count_logoB = 0;

int count_main = 0;

// Logo end color index
int endIdx_logoR = NUM_LEDS_ledfront; // last bulb
int endIdx_logoY = 725;
int endIdx_logoG = 550;
int endIdx_logoB = 187;


// Logo Leds
// speed of filling up the logoleds
int numLeds_aniFirstSpeed = 8;
int numLeds_aniRestSpeed = 7;

unsigned long interval_logo = 1; // interval of update
unsigned long OT_logo = 0;


int ledfrontled_idx = 360;//359;
int ledDim_value = 130;

// Data
boolean allowData = true;
boolean allowAnimate = false;





void setup() {
  Serial.begin(9600);

  // Alive pin
  pinMode(13, OUTPUT);  

  // LOGO FRONT - data pin
  pinMode(ledfront_datapinIn_Show, INPUT);
  pinMode(ledfront_datapinIn_Hide, INPUT);

  // LEDs
  // 1. Logo Front
  FastLED.addLeds<WS2812B, DATA_PIN_ledfront, GRB>(leds_logo_front, 0, NUM_LEDS_ledfront);
  FastLED.clear();
  FastLED.show();

  Serial.begin(9600);
  

  // init vars
  fromMainMega_frontLED_showState = false;
  fromMainMega_frontLED_hideState = false;
  OT_logo = millis();


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
  
  

  fromMainMega_frontLED_showState = digitalRead(ledfront_datapinIn_Show);
  fromMainMega_frontLED_hideState = digitalRead(ledfront_datapinIn_Hide);

  if (fromMainMega_frontLED_showState == true && fromMainMega_frontLED_hideState == false) {
    allowAnimate = true;
  }

/*
  Serial.print(fromMainMega_frontLED_showState);
  Serial.print(" : ");
  Serial.print(fromMainMega_frontLED_hideState);
  Serial.print(" | ");
  Serial.print(allowAnimate);
  Serial.print(" | ");
  Serial.println(count_logoR);
*/

  if (allowAnimate) {
         
      // show LED FRONT
      if (millis() - OT_logo > interval_logo) {
          OT_logo = millis();
  
  
          // 1. start RED color
          if (count_main > 5) {
            
            if (count_logoR < (endIdx_logoR + ledfrontled_idx)) {
              
              for(int i=0; i<numLeds_aniFirstSpeed; i++) {
                int idxR = count_logoR - ledfrontled_idx;
                if (idxR < 0) { idxR = 0; }
                
                leds_logo_front[idxR] = CHSV(0, 255, ledDim_value);            
                count_logoR++;
                //Serial.print(" | ");
                //Serial.println(idxR);
              }
              
            } 
            
          }

  
  
          // 2. start YELLOW color
          if (count_main > 28) {
            
            if (count_logoY < (endIdx_logoY + ledfrontled_idx)) {
  
              for(int j=0; j<numLeds_aniRestSpeed; j++) {
                int idxY = count_logoY - ledfrontled_idx;
                if (idxY < 0) { idxY = 0; }
                
                leds_logo_front[idxY] = CHSV(64, 255, ledDim_value);
                count_logoY++;              
              }
              
            } 
            
          }
          
  
  
          // 3. start GREEN color
          if (count_main > 60) {
            
            if (count_logoG < (endIdx_logoG + ledfrontled_idx)) {
              
              for(int k=0; k<numLeds_aniRestSpeed; k++) {

                int idxG = count_logoG - ledfrontled_idx;
                if (idxG < 0) { idxG = 0; }
                
                leds_logo_front[idxG] = CHSV(100, 255, ledDim_value);
                count_logoG++;
              }
              
            } 
            
          }
  
  
          // 4. start BLUE color
          if (count_main > 100) {
            
            if (count_logoB < (endIdx_logoB + ledfrontled_idx)) {
  
              for(int l=0; l<numLeds_aniRestSpeed; l++) {
                int idxB = count_logoB - ledfrontled_idx;
                if (idxB < 0) { idxB = 0; }
                
                leds_logo_front[idxB] = CHSV(160, 255, ledDim_value);
                count_logoB++;
              }
  
            } else {
              
              // **** once green color is done, means logo is all done ****
              allowAnimate = false;
            }
            
          }
  
  
          FastLED.show();
          count_main++;
      }


  }


   
  if (fromMainMega_frontLED_hideState == true && fromMainMega_frontLED_showState == false) {
      
      // hide LED FRONT
      for(int i=0; i<NUM_LEDS_ledfront; i++) {
          leds_logo_front[i] = 0;
      }
      FastLED.show();
  
  
      // init vars
      count_main = 0;
      
      count_logoR = 0;
      count_logoY = 0;
      count_logoG = 0;
      count_logoB = 0;
  
      OT_logo = millis();
  
      allowAnimate = false;
      
  }



}

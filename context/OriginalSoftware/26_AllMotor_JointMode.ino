// upload to openCR without the arduino Serial panel open
//
// give 14v to openCR

#include <DynamixelWorkbench.h>

// ID10 Primary Motor
// ID11 Secondary Motor
// ID21 iPad Rotate

#define BAUDRATE  57600
#define DXL_ID10    10
#define DXL_ID11    11

#define DXL_ID21    21

DynamixelWorkbench dxl_wb;



// -------------------------------------
// Vars
#define STRING_BUF_NUM 64
String cmd[STRING_BUF_NUM];

int commandNum = -1;

// trace angles
boolean allowReadBack = true;

// Alive LED
boolean aliveState = false;
int aliveDuration = 600;



// Time
unsigned long OT = 0;
unsigned long aliveLED_OT = 0;



void setup() {
  Serial.begin(57600);
  // while(!Serial); // Open a Serial Monitor

  // Set Baudrate
  dxl_wb.begin("", BAUDRATE);

  // Init Servos
  dxl_wb.ping(DXL_ID10); // pri arm
  dxl_wb.ping(DXL_ID11); // sec arm
  dxl_wb.ping(DXL_ID21); // ipad rotation


  // joint mode
  dxl_wb.jointMode(DXL_ID10, 20, 5); // pri arm
  dxl_wb.jointMode(DXL_ID11, 20, 6); // sec arm
  dxl_wb.jointMode(DXL_ID21, 20, 5); // ipad rotation


  // Zeroing
  // Zero Primary and Secondary Armature
  // 1. if 0, 0, 4095 -> pri is porinting up, sec is pointing down - for tighting arm from behind
  // 2. if 2048, 1950, 4095 -> whole arm is pointing down 
  dxl_wb.goalPosition(DXL_ID10, 2048); // vertically point down
  dxl_wb.goalPosition(DXL_ID11, 0); // vertically point up, was 0 // down is 1950
  dxl_wb.goalPosition(DXL_ID21, 3960); // ?? to be determine // was 2048 // was 3950
  

  // init bulk write | read
  dxl_wb.initBulkWrite();
  dxl_wb.initBulkRead();

  // add buld read first
  dxl_wb.addBulkReadParam(DXL_ID10, "Present_Position");
  dxl_wb.addBulkReadParam(DXL_ID11, "Present_Position");
  dxl_wb.addBulkReadParam(DXL_ID21, "Present_Position"); 

  delay(1000);
}




void loop() {

  // alive led
  if (millis() - aliveLED_OT > aliveDuration) {
    aliveLED_OT = millis();
    
    if (aliveState) {
      digitalWrite(BDPIN_LED_USER_1, LOW);
    } else {
      digitalWrite(BDPIN_LED_USER_1, HIGH);
    }

    aliveState = !aliveState;
  }

  
  
 
  if (Serial.available()) {

    // read command
    String read_string = Serial.readStringUntil('\n');

    // trim ending white spaces
    read_string.trim();

    // split commands to array
    split(read_string, ' ', cmd);

    
    commandNum = cmd[0].toInt();
    
    Serial.print("commandNum > ");
    Serial.println(commandNum);

  }



  


  switch(commandNum) {

    case 1:{

      // Set Servos Torque OFF
      dxl_wb.itemWrite(DXL_ID10, "Torque_Enable", 0);
      dxl_wb.itemWrite(DXL_ID11, "Torque_Enable", 0);
      dxl_wb.itemWrite(DXL_ID21, "Torque_Enable", 0);
      
    } break;


    case 2:{

      // Set Servos Torque ON
      dxl_wb.itemWrite(DXL_ID10, "Torque_Enable", 1);
      dxl_wb.itemWrite(DXL_ID11, "Torque_Enable", 1);
      dxl_wb.itemWrite(DXL_ID21, "Torque_Enable", 1);
      
    } break;



    case 3:{
      // 3 = moving command

      // pointing bottom
      // 3 50 50 50 5 5 5 2048 2130 3072
      
      
      // convert String to Int
      // Vel
      uint16_t pri_vel = cmd[1].toInt();
      uint16_t sec_vel = cmd[2].toInt();
      uint16_t ipadRotate_vel = cmd[3].toInt();
  
      // Accel
      uint16_t pre_Accel = cmd[4].toInt();
      uint16_t sec_Accel = cmd[5].toInt();
      uint16_t ipadRotate_Accel = cmd[6].toInt();
      
      // Angle Pos - needs to be INT, cause got +ve and -ve
      int32_t pri_Pos = cmd[7].toInt();
      int32_t sec_Pos = cmd[8].toInt();
      int32_t ipadRotate_Pos = cmd[9].toInt();


      // =============================================================
      dxl_wb.addBulkWriteParam(DXL_ID10, "Torque_Enable", 1);
      dxl_wb.addBulkWriteParam(DXL_ID11, "Torque_Enable", 1);
      dxl_wb.addBulkWriteParam(DXL_ID21, "Torque_Enable", 1);
      // bulk write
      dxl_wb.bulkWrite();


      // Set Motor Vel + Accel 
      dxl_wb.addBulkWriteParam(DXL_ID10, "Profile_Velocity", pri_vel);
      dxl_wb.addBulkWriteParam(DXL_ID11, "Profile_Velocity", sec_vel);
      dxl_wb.addBulkWriteParam(DXL_ID21, "Profile_Velocity", ipadRotate_vel);
      // bulk write
      dxl_wb.bulkWrite();


      dxl_wb.addBulkWriteParam(DXL_ID10, "Profile_Acceleration", pre_Accel); 
      dxl_wb.addBulkWriteParam(DXL_ID11, "Profile_Acceleration", sec_Accel);  
      dxl_wb.addBulkWriteParam(DXL_ID21, "Profile_Acceleration", ipadRotate_Accel); 
      
      // bulk write
      dxl_wb.bulkWrite();
      // =============================================================


      // Try writing in another way - item write way
      // Move Motor        
      dxl_wb.addBulkWriteParam(DXL_ID10, "Goal_Position", pri_Pos);
      dxl_wb.addBulkWriteParam(DXL_ID11, "Goal_Position", sec_Pos);
      dxl_wb.addBulkWriteParam(DXL_ID21, "Goal_Position", ipadRotate_Pos);

      // bulk write
      dxl_wb.bulkWrite();


      commandNum = -1;
   
    } break;



    case 4:{

      // Angle Pos - needs to be INT, cause got +ve and -ve
      int32_t pri_Pos = cmd[1].toInt();
      int32_t sec_Pos = cmd[2].toInt();
      int32_t ipadRotate_Pos = cmd[3].toInt();


      // Try writing in another way - item write way
      // Move Motor        
      dxl_wb.itemWrite(DXL_ID10, "Goal_Position", pri_Pos);
      dxl_wb.itemWrite(DXL_ID11, "Goal_Position", sec_Pos);
      dxl_wb.itemWrite(DXL_ID21, "Goal_Position", ipadRotate_Pos);


      commandNum = -1;
      
    } break;


    

    
  } // switch







  // read Servo Angles
  if (allowReadBack) {
    

    if (millis() - OT > 10) {
      OT = millis(); 

      // Read back - need to be in INT, cause got +ve and -ve
      int32_t pri_pos =     dxl_wb.bulkRead(DXL_ID10, "Present_Position");
      int32_t sec_pos =     dxl_wb.bulkRead(DXL_ID11, "Present_Position");
      int32_t ipad_rotate = dxl_wb.bulkRead(DXL_ID21, "Present_Position");

      dxl_wb.setBulkRead();

      Serial.print("angle:");
      Serial.print(pri_pos);
      Serial.print("|");
      Serial.print(sec_pos);
      Serial.print("|");
      Serial.print(ipad_rotate);
      Serial.println("");

       
    }

  }

  

}




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

import sys
import signal
import time
from pixy import *
from ctypes import *
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
import Adafruit_BBIO.ADC as ADC

#define pins

WEIGHT = "P9_33"
L_ENC = "P9_23"
R_ENC = "P9_24"

#define motor output pins
LEFT_DIR	=  "P9_13"
RIGHT_DIR	=  "P9_15"
DRUM	    =      "P9_21"
LEFT_PWM	=  "P9_14"
RIGHT_PWM	=  "P9_16"

#sensors are numbered with 1 being the lower left side and going CW around perimeter
#define sensor pins
pin1trigger = "P8_9"
pin1echo    = "P8_10"
pin2trigger = "P8_11"
pin2echo    = "P8_12"
pin3trigger = "P8_13"
pin3echo    = "P8_14"
pin4trigger = "P8_15"
pin4echo    = "P8_16"
pin5trigger = "P8_17"
pin5echo    = "P8_18"
pin6trigger = "P9_25"
pin6echo    = "P9_26"
pin7trigger = "P8_7"
pin7echo    = "P8_8"

#GLOBAL VARIABLES
capture_time     = 3
capture_y	 = 180
turn_time	 = 1
turn_time_search	 = 2
safe_dist_search	= 30
avoid_time_search	= 2

PIXY_MIN_X            =    0
PIXY_MAX_X            =  319
PIXY_MIN_Y            =    0
PIXY_MAX_Y            =  199

PIXY_X_CENTER         =  ((PIXY_MAX_X-PIXY_MIN_X) / 2)
PIXY_Y_CENTER         =  ((PIXY_MAX_Y-PIXY_MIN_Y) / 2)

PIXY_X_1              =  ((PIXY_MAX_X-PIXY_MIN_X) / 5)
PIXY_X_2              =  (2 * (PIXY_MAX_X-PIXY_MIN_X) / 5)
PIXY_X_3              =  (3 * (PIXY_MAX_X-PIXY_MIN_X) / 5)
PIXY_X_4              =  (4 * (PIXY_MAX_X-PIXY_MIN_X) / 5)


BLOCK_BUFFER_SIZE     =    1


# Globals #

run_flag = True


class Blocks (Structure):
  _fields_ = [ ("type", c_uint),
               ("signature", c_uint),
               ("x", c_uint),
               ("y", c_uint),
               ("width", c_uint),
               ("height", c_uint),
               ("angle", c_uint) ]


def handle_SIGINT(signal, frame):
  global run_flag
  run_flag = False

########################################################

def FireSensor (DistThresTurn, TriggerPin, EchoPin):  #input=sensor pins and thres; output=true or false; this is for firing only one sensor at a time to check while turning

  objectdistance = FindObjectdistance (TriggerPin, EchoPin)
  
  if objectdistance <= DistThresTurn: #if object is too close; below threshold
    AboveThreshold = True
  else:
    AboveThreshold = False
  
  return AboveThreshold  

##########################################################
def FindObjectdistance(GPIO_TRIGGER, GPIO_ECHO):

  timeout = 0 
 
  GPIO.output(GPIO_TRIGGER, GPIO.LOW)
  time.sleep(0.5)


  GPIO.output(GPIO_TRIGGER, GPIO.HIGH) #trigger to high

  time.sleep(0.00001)
  GPIO.output(GPIO_TRIGGER, GPIO.LOW) #trigger to low after 0.01 ms

  while GPIO.input(GPIO_ECHO) == 0 and timeout < 10000:
    timeout += 1

  StartTime = time.time()

  while GPIO.input(GPIO_ECHO) == 1 and timeout < 10000:
    timeout += 1

  StopTime = time.time() #time of arrival

  if timeout < 10000:
    TimeElapsed = StopTime - StartTime
    objectdistance = (TimeElapsed * 34300)/ 2 #distance in cm
  else:
    objectdistance = 1000


  return objectdistance



####################################################
def TurnRobot (turnDir): #code for turning 
#direction for turning: 0=no turn, 1=right, 2=left, 3=backup
  
  PWM.set_duty_cycle(LEFT_PWM, 0)
  PWM.set_duty_cycle(RIGHT_PWM, 0)
  GPIO.output(LEFT_DIR, False)
  GPIO.output(RIGHT_DIR, False)
 
  if turnDir == 1: #turn right
    enc_move(False, 100, True, 0, 49, 2)

  elif turnDir == 2: #turn left
    enc_move(True, 0, False, 100, 49, 2)
  
  elif turnDir == 3:
    enc_move(True, 0, True, 0, 36, 3)

##########################################3

def collision_avoidance ():  

  #threshold must be large enough to make 360 turn
  DistThres = 40 #threshold in cm greater than a 360 turn incase boxed in
  DistThresTurn = 40 #threshold for when turning
  #direction for turning: 0=no turn, 1=right, 2=left, 3=backup

  AboveThreshold = False  #false if no object within thres distance;true if object within thres and need to turn 
  RobotTurned = False #set to true after turning
  TurnDir = 0
 
  AboveThreshold = FireSensor (DistThres, GPIO_TRIGGER_3, GPIO_ECHO_3) #firing sensors front sensors to check
  if AboveThreshold == False:
    time.sleep(0.00001) #time delay of 0.01ms so waves don't interfere 
    AboveThreshold = FireSensor (DistThres, GPIO_TRIGGER_4, GPIO_ECHO_4)
   
  if AboveThreshold == True:  #obj in front; need to turn
    AboveThreshold = FireSensor (DistThresTurn, GPIO_TRIGGER_2, GPIO_ECHO_2) #check left
    if AboveThreshold == False:
      TurnRobot(2) #turn left
      RobotTurned = True
    else: 
      AboveThreshold = FireSensor (DistThresTurn, GPIO_TRIGGER_5, GPIO_ECHO_5) #check right
      if AboveThreshold == False:
        TurnRobot(1) #turn right
        RobotTurned = True
      else: 
        AboveThreshold = FireSensor (DistThresTurn, GPIO_TRIGGER_7, GPIO_ECHO_7) #check back
        TurnRobot(3) #back up ***will try to back up if boxed in
        RobotTurned = True
    
  return RobotTurned

####################################################################

def enc_move(l_dir, l_speed, r_dir, r_speed, count_max, time_max)

  #handles movements which run for a set distance using encoder feedback

  count_l = 0
  count_r = 0
  start = time.time()
  stop = time.time()
  l_stop = 0
  r_stop = 0

  GPIO.add_event_detect(L_ENC)
  GPIO.add_event_detect(R_ENC)

  GPIO.output(LEFT_DIR, l_dir)
  GPIO.output(RIGHT_DIR, r_dir)
  PWM.start(LEFT_PWM, l_speed)
  PWM.start(RIGHT_PWM, r_speed)

  while count_l < count_max and count_r < count_max and (stop - start) < time_max:
    if GPIO.event_detected(L_ENC):
      count_l += 1
    if GPIO.event_detected(R_ENC):
      count_r += 1
    stop = time.time()
    if count_l > count_max and not l_stop:
      GPIO.output(LEFT_DIR, GPIO.LOW) 
      PWM.set_duty_cycle(LEFT_PWM,0)
      l_stop = 1
    if count_r > 23 and not r_stop:
      GPIO.output(RIGHT_DIR, GPIO.LOW)
      PWM.set_duty_cycle(RIGHT_PWM,0)
      r_stop = 1

  GPIO.output(LEFT_DIR, GPIO.LOW)
  GPIO.output(RIGHT_DIR, GPIO.LOW)
  PWM.start(LEFT_PWM, 0)
  PWM.start(RIGHT_PWM, 0)

  GPIO.remove_event_detect(L_ENC)
  GPIO.remove_event_detect(R_ENC)  


####################################################################

def main():
  global run_flag

  #setup pins
  GPIO.setup(LEFT_DIR, GPIO.OUT)
  GPIO.setup(RIGHT_DIR, GPIO.OUT)
  GPIO.setup(pin1trigger, GPIO.OUT)
  GPIO.setup(pin2trigger, GPIO.OUT)
  GPIO.setup(pin3trigger, GPIO.OUT)
  GPIO.setup(pin4trigger, GPIO.OUT)
  GPIO.setup(pin5trigger, GPIO.OUT)
  GPIO.setup(pin6trigger, GPIO.OUT)
  GPIO.setup(pin7trigger, GPIO.OUT)
  GPIO.setup(pin1echo, GPIO.IN)
  GPIO.setup(pin2echo, GPIO.IN)
  GPIO.setup(pin3echo, GPIO.IN)
  GPIO.setup(pin4echo, GPIO.IN)
  GPIO.setup(pin5echo, GPIO.IN)
  GPIO.setup(pin6echo, GPIO.IN)
  GPIO.setup(pin7echo, GPIO.IN)
  GPIO.setup(L_ENC, GPIO.IN)
  GPIO.setup(R_ENC, GPIO.IN)
  ADC.setup()


  # Initialize Pixy Interpreter thread #
  pixy_init_status = pixy_init()

  if pixy_init_status != 0:
    pixy_error(pixy_init_status)
    return

  # Initialize block #
  block       = Block()
  frame_index = 0

  signal.signal(signal.SIGINT, handle_SIGINT)
  
  balls = 0

  # Run until we receive the INTERRUPT signal #
  while run_flag:

    # Do nothing until a new block is available #
    while not pixy_blocks_are_new() and run_flag:
        safe = True
        sensed_object = [False,False,False,False,False,False,False]

        sensed_object[0] = FireSensor (safe_dist_search, pin1trigger, pin1echo)
	time.sleep(0.00001)
        sensed_object[1] = FireSensor (safe_dist_search, pin2trigger, pin2echo)
        time.sleep(0.00001)
	sensed_object[2] = FireSensor (safe_dist_search, pin3trigger, pin3echo)
        time.sleep(0.00001)
	sensed_object[3] = FireSensor (safe_dist_search, pin4trigger, pin4echo)
        time.sleep(0.00001)
	sensed_object[4] = FireSensor (safe_dist_search, pin5trigger, pin5echo)
        time.sleep(0.00001)
	sensed_object[5] = FireSensor (safe_dist_search, pin6trigger, pin6echo)
        time.sleep(0.00001)
	sensed_object[6] = FireSensor (safe_dist_search, pin7trigger, pin7echo)
        
        for x in xrange(6):
          if sensed_object[x]:
            safe = False
            break
        if safe:
          enc_move(False, 100, True, 0, 24, turn_time)
          continue

        #if not move away from obstacle
        elif (sensed_object[2] or sensed_object[3]) and not sensed_object[6]:
          enc_move(True, 0, True, 0, 36, avoid_time_search)
          continue

        elif not (sensed_object[2] or sensed_object[3]) and sensed_object[6]:
          enc_move(False, 100, False, 100, 36, avoid_time_search)
          continue

        elif not (sensed_object[0] or sensed_object[1]) and (sensed_object[4] or sensed_object[5]):
          enc_move(True, 0, False, 100, 49, turn_time_search)
          continue

        elif (sensed_object[0] or sensed_object[1]) and not (sensed_object[4] or sensed_object[5]):
          enc_move(False, 100, True, 0, 49, turn_time_search)
          continue

        elif (sensed_object[0] or sensed_object[1]) and (sensed_object[4] or sensed_object[5]):

          if not (sensed_object[2] or sensed_object[3]):
            enc_move(False, 100, False, 100, 36, avoid_time_search)
            continue

          elif not sensed_object[6]:
            enc_move(True, 0, True, 0, 36, avoid_time_search)
            continue

        elif (sensed_object[2] or sensed_object[3]) and sensed_object[6]:

          if not (sensed_object[0] or sensed_object[1]):
            enc_move(True, 0, False, 100, 49, turn_time_search)
            continue

          elif not (sensed_object[4] or sensed_object[5]):
            enc_move(False, 100, True, 0, 49, turn_time_search)
            continue

    # Grab a block #
    count = pixy_get_blocks(BLOCK_BUFFER_SIZE, block)

    # Was there an error? #
    if count < 0:
      pixy_error(count)
      sys.exit(1)

    if count > 0:
      # We found a block #
      print("Found")
      lost = 0
      turned = False

      #Collision Avoidance
      turned = collision_avoidance()
      if turned:
        continue

      #set motors forward

      GPIO.output(LEFT_DIR, GPIO.LOW)
      GPIO.output(RIGHT_DIR, GPIO.LOW)
      PWM.start(LEFT_PWM, 80)
      PWM.start(RIGHT_PWM, 80)
      l_speed = 80
      r_speed = 80

      #while loop for following, y/height for condition
      while block.y < capture_y:

        #collision avoidance
        turned = collision_avoidance()

        if turned:
          break

	  	  #Adjust motor speeds
        if block.x < PIXY_X_1:
          l_speed -= 5
	        if l_speed < 0:
	          l_speed = 0
          r_speed += 5
	        if r_speed > 100:
	          r_speed = 100
	        PWM.set_duty_cycle(LEFT_PWM, l_speed)
          PWM.set_duty_cycle(RIGHT_PWM, r_speed)

        elif block.x < PIXY_X_2:
          l_speed -= 2
	        if l_speed < 0:
	          l_speed = 0
          r_speed += 2
	        if r_speed > 100:
	          r_speed = 100
	        PWM.set_duty_cycle(LEFT_PWM, l_speed)
          PWM.set_duty_cycle(RIGHT_PWM, r_speed)

        elif block.x < PIXY_X_3:
          l_speed = 80
          r_speed = 80
          PWM.set_duty_cycle(LEFT_PWM, 80)
      	  PWM.set_duty_cycle(RIGHT_PWM, 80)

        elif block.x < PIXY_X_4:
          l_speed += 2
	        if l_speed > 100:
	          l_speed = 100
	        r_speed -= 2
	        if r_speed < 0:
	          r_speed = 0
	        PWM.set_duty_cycle(LEFT_PWM, l_speed)
          PWM.set_duty_cycle(RIGHT_PWM, r_speed)

        else:
          l_speed += 5
	        if l_speed > 100:
	          l_speed = 100
	        r_speed -= 5
	        if r_speed < 60:
	          r_speed = 0
	        PWM.set_duty_cycle(LEFT_PWM, l_speed)
          PWM.set_duty_cycle(RIGHT_PWM, r_speed)


        # Grab a block #
    	  count = pixy_get_blocks(BLOCK_BUFFER_SIZE, block)

        #if statement to see if block got lost, if so quit loop, flag for lost block
        if count == 0:
          lost = 1
          PWM.start(LEFT_PWM, 0)
          PWM.start(RIGHT_PWM, 0)
          PWM.start(DRUM, 0)
          break

      #end of track loop

      # if flag is false, turn on drum motor, move forward until weight change is sensed, then stop
      if not lost:
        GPIO.output(LEFT_DIR, GPIO.LOW)
        GPIO.output(RIGHT_DIR, GPIO.LOW)
        PWM.start(LEFT_PWM, 80)
      	PWM.start(RIGHT_PWM, 80)
        PWM.start(DRUM, 100)
        
        start = time.time()
        stop = time.time()
        v_in = ADC.read(WEIGHT)
        old_balls = balls
        
        while balls <= old_balls and (stop - start) < 5:
          v_in = ADC.read(WEIGHT)
          balls = 20*(1.8-v_in)/0.765
          stop = time.time()
        
        if balls >= 120:
          PWM.cleanup()
          GPIO.cleanup()
          pixy_close() 

      PWM.start(LEFT_PWM, 0)
      PWM.start(RIGHT_PWM, 0)
      PWM.start(DRUM, 0)

  pixy_close()

if __name__ == "__main__":
  main()

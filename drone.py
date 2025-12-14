import threading 
import time
from pymavlink import mavutil
import math
from dataclasses import dataclass, field

class Drone:
    drone_conected = False
        # how to pair run sudo rfcomm bind /dev/rfcomm0 <mack adress of raido>
    # sudo rfcomm bind /dev/rfcomm0 04:24:11:19:05:77
    #  sudo rfcomm release all # to remove all connnectons

    # path_to_uav = "/dev/rfcomm24" # connect via mlrs blutooth 2.4 ghz module
    # path_to_uav = "/dev/rfcomm90" # connect via mlrs blutooth 900 mhz module

    # I found the videos from Intelligent Quads helpfull
    # https://www.youtube.com/watch?v=kecnaxlUiTY
    # https://www.youtube.com/watch?v=6M7e7DDLTQc
    # https://www.youtube.com/watch?v=NTjEcHmqmu4

    def __init__(self,path_to_uav=None):
        #  this is to running of the program without a drone connecred
        self.mode_mapping = {'STABILIZE': 0,'ACRO': 1,'ALT_HOLD': 2,'AUTO': 3,'GUIDED': 4,'LOITER': 5,'RTL': 6,'CIRCLE': 7,'OF_LOITER': 10,'DRIFT': 11,'SPORT': 13,'FLIP': 14,'AUTOTUNE': 15,'POSHOLD': 16,'BRAKE': 17,'THROW': 18,'AVOID_ADSB': 19,'GUIDED_NOGPS': 20,'SMART_RTL': 21,'FLOWHOLD': 22,'FOLLOW': 23,'ZIGZAG': 24,'SYSTEMIDLE': 25,'AUTOTUNE': 26,'RALLY': 27}
        
        if path_to_uav == None:
            self.connection = None 
        # else:
        #     self.connect(path_to_uav)           

        @dataclass
        class DroneData:
            # TODO: not working but doen't matter for now
            position: dict = field(default_factory=lambda: {"lat": -35.3628875, "lon": 149.1651714})
            mode: str = "NOT_CONNECTED"
            yaw: float = 0.0
            battery_voltage: float = 10.2
            battery_mah_left: int = 5000
            battery_capacity: int = 5000
            alt_abs: float = 0.0
            home: dict = field(default_factory=lambda: {"lat": -35.3628875, "lon": 149.1651714})

            def message_passer(self, msg):
                if int(time.time()) % 100 == 0:
                    print("make a actual passer in drone.py line 41")

        self.drone_state = DroneData()

        self.questions =  {} # {"question:ans="?"or acceped or denied}
        self._questions_lock = threading.Lock()
        self.questions_history = {}

    def start_automatic_message_passer(self,update_rate=1):
        self.set_a_message_interval("GLOBAL_POSITION_INT", interval=update_rate)
        self.set_a_message_interval("ATTITUDE", interval=update_rate)
        self.set_a_message_interval("BATTERY_STATUS", interval=update_rate)
        self.set_a_message_interval("HEARTBEAT", interval=update_rate)


        def message_in(message):
            self.drone_state.message_passer(message)
            self.add_question(message)
            
        def passer():
            while True:
                    msg = self.connection.recv_msg()
                    if msg: message_in(msg)
        threading.Thread(target=passer,daemon=True).start() 

    def add_question(self,message):
        if message._type == "STATUSTEXT" and "drone:" in message.text:
            message = message.text
            question = message.replace("drone:","")
            print(f"adding question {question} this ind in drone.py")
            with self._questions_lock:
                self.questions[question] = "?"
        
    def get_unanswerd_question(self):
        for i in self.questions.keys():
            with self._questions_lock:
                if self.questions[i] == "?":
                    return i
        return None

    def answer_question(self,question,answer):
        answer = answer.lower()
        if answer not in ["accepted","rejected"]: raise ValueError(f"you made a typo {answer = } is not valid")

        self.questions_history[str(int(time.time()))] = {question: answer}
        with self._questions_lock:
            del(self.questions[question])

        message = str([question,answer])
        def send_question(message):
            if len(message) <= 47:
                self.send_text_message(message)
                return None
            else:
                raise ValueError("work out how to split question over manny trasmition")

        threading.Thread(target=send_question,args=(message,),daemon=True).start() # use theding not to slow the program if sennding reeeeeeely long questions                   

    def send_text_message(self,message:str):
        if len(message) > 50-4:
            raise ValueError("the send text message must be under 50 chars")
        self.connection.mav.statustext_send(
        mavutil.mavlink.MAV_SEVERITY_INFO, 
        f"gc: {message}".encode("utf-8")
        # b"gc:" + message
        )

    def connect(self,path_to_uav):
        """connect to the droen and also act like a init for the Telmerty class like redefing the update class"""
        if not Drone.drone_conected:
            self.connection = mavutil.mavlink_connection(path_to_uav, baud=115200)
            self.connection.wait_heartbeat()
            self.start_automatic_message_passer()
        else:
            print("tryed to open drone conection twice")
        
    def disconnect(self):
        self.connection = None
        
    def set_a_message_interval(self,message_name,interval=1):
        """interval in sec"""
        # https://mavlink.io/en/mavgen_python/howto_requestmessages.html
        interval *= 1000000
        message = self.connection.mav.command_long_encode(
            self.connection.target_system,  # Target system ID
            self.connection.target_component,  # Target component ID
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # ID of command to send
            0,  # Confirmation
            eval(f"mavutil.mavlink.MAVLINK_MSG_ID_{message_name}"),  # param1: Message ID to be streamed
            interval, # param2: Interval in microseconds
            0,0,0,0,0)
 
drone = Drone()
time.sleep(1)
drone.connect("/dev/rfcomm0")
# while True:
    # drone.connection


# question_lock = threading.Lock()

# questions = []
# def check_drone_question():
#         with question_lock:
#             if questions != []:
#                 return questions.pop()
#         return "None"

# def add_question():
#     while True:
#         new_q = input("add question")
#         with question_lock:
#             questions.append(new_q)

# threading.Thread(target=add_question).start()

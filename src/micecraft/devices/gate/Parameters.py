MIN_BALANCE_WEIGHT_GRAPH = -10  # min balance of the graph
MAX_BALANCE_WEIGHT_GRAPH = 60   # max balance of the graph
    
# Gate
    
MAX_GATE_WEIGHT_LIST_SIZE = 10  # number of sample of weight kept in weight list
NB_VALUE_TO_COMPUTE_MEAN_WEIGHT = 4 # number of sample to compute the mean weight in the gate

OPENED_DOOR_POSITION_MOUSE = 110
CLOSED_DOOR_POSITION_MOUSE = 290
    
OPENED_DOOR_POSITION_RAT = 50 #90  # FIXME : faudra se mettre d'accord la dessus un moment
CLOSED_DOOR_POSITION_RAT = 235 #245
    
NB_OBSERVATION_WEIGHT = 4 # number of measurement for check one animal or no animal
NB_OBSERVATION_RFID = 100 # number of measurement to check RFID of the animal
    
# Doors
    
DEFAULT_TORQUE_AND_SPEED_LIMIT_MOUSE = 110 # 120 # 150
    
DEFAULT_SPEED_LIMIT_RAT = 30 # 120 # 150
DEFAULT_TORQUE_LIMIT_RAT = 400 # 120 # 150
    
RE_CLOSING_THRESHOLD_PERCENTAGE = 95
OPEN_CLOSE_SENSITIVITY_PERCENTAGE = 98 
DURATION_OF_LIDAR_CLOSE_TEST = 2

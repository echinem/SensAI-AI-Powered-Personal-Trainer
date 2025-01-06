import cv2
import mediapipe as mp
import numpy as np
import time
from datetime import timedelta
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculate_angle(a,b,c):
    a = np.array(a) # First
    b = np.array(b) # Mid
    c = np.array(c) # End
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle >180.0:
        angle = 360-angle
        
    return angle 

cap = cv2.VideoCapture(0)

# Curl counter variables
counter = 0 
stage = None
instr=None
starting_time=time.time()

## Setup mediapipe instance
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():

        ret, frame = cap.read()
        
        # Recolor image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
      
        # Make detection
        results = pose.process(image)
        elapsed_time=time.time()-starting_time
        # Recolor back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Extract landmarks
        try:
            landmarks = results.pose_landmarks.landmark
            
            # Get coordinates
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

            left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]

            shoulderr = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            elbowr = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            wristr = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

            # Calculate angle
            angle = calculate_angle(shoulder, elbow, wrist)
            angle_not=calculate_angle(elbow,shoulder,left_hip)
            #angler = calculate_angle(shoulderr, elbowr, wristr)
            
            cv2.putText(image, str(angle), tuple(np.multiply(elbow, [640, 480]).astype(int)), 
                           cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
                                )
            cv2.putText(image, str(angle_not), tuple(np.multiply(shoulder, [640, 480]).astype(int)), 
                           cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
                                )
            
            

            if angle > 170:
                instr=" "
                stage = "down"
                uptime=time.time()

            if angle < 30 and stage =='down':
                
                stage="up"
                instr=" "
                counter +=1
                downtime=time.time()

            if angle_not>20:
                # stage=" "
                instr="wrong"
            elif abs(uptime-downtime)<0.3:
                instr="do slow"
            elif abs(uptime-downtime)>5:
                instr="do little fast"
            elif abs(uptime-downtime)>0.5 and abs(uptime-downtime)<5:
                instr=" "
            # Visualize angle
            
                       
        except:
            pass
        
        # Render curl counter
        # Setup status box
        cv2.rectangle(image, (0,0), (110,50), (255,0,127), -1)
        
        # Rep data
        cv2.putText(image, 'REPS', (5,15), 
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, str(counter), 
                    (5,40), 
                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)
        
        # Stage data
        cv2.putText(image, 'STAGE', (50,15), 
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, stage, 
                    (30,40), 
                    cv2.FONT_HERSHEY_COMPLEX, 0.8, (255,255,255), 1, cv2.LINE_AA)
        
        cv2.rectangle(image, (200,0), (310,50), (255,0,127), -1)
        
        # Rep data
        cv2.putText(image, 'INSTRUCTION', (200,15), 
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        cv2.putText(image, str(instr), 
                    (200,40), 
                    cv2.FONT_HERSHEY_COMPLEX, 0.8, (255,255,255), 1, cv2.LINE_AA)
        
        
        # Render detections
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
                                mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2) 
                                 )               
        cv2.namedWindow("Resized_Window", cv2.WINDOW_NORMAL) 
  
        # Using resizeWindow() 
        cv2.resizeWindow("Resized_Window", 2000, 2000)
        cv2.imshow('Resized_Window', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
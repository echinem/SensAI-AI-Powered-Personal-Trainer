import json
import pdb
from flask import Flask,render_template,request,redirect,url_for, flash, Response,jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,date
from flask import session 
from werkzeug.security import generate_password_hash, check_password_hash
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

app=Flask(__name__)
app.secret_key = "xyz"
counter=0
wrong_counters=0
starting_time=None
total_time=None
def generate_video_feed():
    cap = cv2.VideoCapture(0)
    global counter,wrong_counters,starting_time,total_time
    # Curl counter variables
    counter = 0 
    stage = None
    instr=None
    wrong_counters = 0 
    starting_time=time.time()

    ## Setup mediapipe instance
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():

            ret, frame = cap.read()
            if not ret:
                break
            
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

                if angle < 30 and stage =='down' and angle_not<20:
                    
                    stage="up"
                    instr=" "
                    counter +=1
                    downtime=time.time()

                if angle_not>20:
                    # stage=" "
                    wrong_counters=1
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

            ret, buffer = cv2.imencode('.jpg', image)
            if not ret:
                continue
            
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        cap.release()
        cv2.destroyAllWindows()
        total_time=time.time()-starting_time

        def log_progress(user_id, exercise_name, repetitions, wrong_counter, total_time):
            new_progress = exercise_progress(
            user_id=user_id,
            exercise_name=exercise_name,
            repetitions=repetitions,
            wrong_count=wrong_counter,
            total_time=total_time,
            date=date.today()
            )
            db.session.add(new_progress)
            db.session.commit()

        # Example in generate_video_feed():
        if counter > 0:
            log_progress(session['user_id'], 'Curls', counter, wrong_counters, elapsed_time)

    return {
        'repetitions': counter,
        'wrong_counter': wrong_counters,
        'total_time': time.time() - starting_time
    }

def generate_video_feeds():
    cap = cv2.VideoCapture(0)
    # Curl counter variables
    counter = 0 
    stage = None
    ## Setup mediapipe instance
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
        
            # Recolor image to RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
      
            # Make detection
            results = pose.process(image)
    
            # Recolor back to BGR
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
            # Extract landmarks
            try:
                landmarks = results.pose_landmarks.landmark
            
                # Get coordinates
                shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                verticalhips = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,0]
                verticalknee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,0]
                verticalankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,0]

                # Calculate angle
                angleatback = calculate_angle(verticalhips, hip, shoulder)
                angleatknee = calculate_angle(verticalknee, knee, hip)
                angleatankle = calculate_angle(verticalankle, ankle, knee)

                cv2.putText(image, str(angleatback), tuple(np.multiply(hip, [640, 480]).astype(int)), 
                           cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
                                )
                cv2.putText(image, str(angleatknee), tuple(np.multiply(knee, [640, 480]).astype(int)), 
                           cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
                               )
                cv2.putText(image, str(angleatankle), tuple(np.multiply(ankle, [640, 480]).astype(int)), 
                           cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
                               )
           
                if angleatback < 25 or angleatknee < 85 :
                    stage = "move down"
                if angleatback >=25 and stage == 'move down':
                    stage="move up"
                    counter +=1
            

            # Visualize angle
            
            except:
                pass
        
            # Render curl counter
            # Setup status box
            cv2.rectangle(image, (0,0), (160,73), (255,0,127), -1)
        
            # Rep data
            cv2.putText(image, 'REPS', (15,12), 
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(image, str(counter), 
                    (10,60), 
                    cv2.FONT_HERSHEY_COMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)
        
            # Stage data
            cv2.putText(image, 'STAGE', (65,12), 
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(image, stage, 
                    (60,60), 
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,255,255), 2, cv2.LINE_AA)
        
        
            # Render detections
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
                                mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2) 
                                 )               
        
            cv2.imshow('Mediapipe Feed', image)
            ret, buffer = cv2.imencode('.jpg', image)
            if not ret:
                continue
            
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
        cap.release()
        cv2.destroyAllWindows()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Single SQLAlchemy instance with multiple database paths
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users1.db'
app.config['SQLALCHEMY_BINDS'] = {
    'progress': 'sqlite:///progress.db'
}

# Single SQLAlchemy instance
db = SQLAlchemy(app)
# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    ph_no = db.Column(db.String(15))

# Exercise Progress model for tracking user activities
class exercise_progress(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    exercise_name = db.Column(db.String(100), nullable=False)
    repetitions = db.Column(db.Integer, nullable=False)
    wrong_counter = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Float, default=0.0)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, exercise_name, repetitions, wrong_counter, total_time,date=None):
        self.exercise_name = exercise_name
        self.repetitions = repetitions
        self.wrong_counter = wrong_counter
        self.total_time = total_time
        self.date = date if date else datetime.utcnow()


@app.route('/',methods=['GET','POST'])
def hello_world():
    return render_template('baseh.html')

@app.route('/home',methods=['GET','POST'])
def home():
    user_initial = session.get('user_initial', 'U')  # Default to 'U' if not logged in
    return render_template('index.html', user_initial=user_initial)

@app.route('/about_us')
def about_us():
    user_initial = session.get('user_initial', 'U')  # Default to 'U' if not logged in
    return render_template('aboutUs.html', user_initial=user_initial)

@app.route('/login', methods=['GET', 'POST'])
def login():
    print("Login route accessed")  # Debug

    if request.method == 'POST':
        print("POST request received")  # Debug
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        print(f"Input Username: {username}, Input Password: {password}")  # Debug

        user = User.query.filter(User.username == username).first()
        session['user_initial']=username[0].upper()
        if user:
            print(f"User Found: {user.username}, Password in DB: {user.password}")  # Debug
        else:
            print("User not found.")  # Debug

        if user and user.password == password:
            print("Login successful")  # Debug
            flash("Login successful!")
            session['user_id'] = user.id  # Add user ID to session
            return redirect("/home")
        else:
            print("Invalid credentials")  # Debug
            flash("Invalid credentials. Please try again.")
            return redirect("/login")

    return render_template('login.html')


@app.route('/end_exercise', methods=['GET','POST'])
def end_exercise():
    
    try:
        global counter, wrong_counters, starting_time,total_time

        print('1')
        data = request.get_json()
        exercise_name = data.get('exercise_name','Curls')
        repetitions = data.get('repetitions', 0)
        wrong_counter = data.get('wrong_counter', 0)
        total_time = data.get('total_time', 0.0)

        # Debugging Logs
        print(f"Received Data: {data}")

        # Create a new progress entry
        progress_entry = exercise_progress(
            exercise_name='curls',
            repetitions=counter,
            wrong_counter=wrong_counters,
            total_time=time.time()-starting_time,
            date=datetime.utcnow()
        )

        # Add to the database
        db.session.add(progress_entry)
        db.session.commit()
        counter = 0
        wrong_counters = 0
        starting_time = None
        total_time=None

        #return jsonify({"message": "Exercise details successfully stored."}), 200
    except Exception as e:
        print(f"Error: {e}")
        #return jsonify({"message": "Failed to store exercise details."}), 500
    

    #return jsonify({'message': 'Exercise data saved successfully!'})
    return redirect('/home')

@app.route('/curls')
def curls():
    return render_template('curls.html')

@app.route('/squats')
def squats():
    return render_template('squats.html')

@app.route('/pushup')
def pushup():
    return render_template('pushups.html')

@app.route('/video_feedc')
def video_feedc():
    return Response(generate_video_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feeds')
def video_feeds():
    return Response(generate_video_feeds(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/leaderboard')
def leaderboard():
    user_initial = session.get('user_initial', 'U')  # Default to 'U' if not logged in
    
    return render_template('leaderboard.html', user_initial=user_initial)
    
@app.route('/myprogress')
def myprogress():
    user_initial = session.get('user_initial', 'U')  # Default to 'U' if not logged in
    
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to view your progress.")
        return redirect('/login')

    # Fetch progress data
    progress_data = exercise_progress.query.filter_by(user_id=user_id).all()

    # Prepare data for charts
    exercises = {}
    date_to_reps = {}

    for entry in progress_data:
        exercises.setdefault(entry.exercise_name, []).append({
            'reps': entry.repetitions,
            'date': entry.date.strftime('%Y-%m-%d')
        })
        
        date_str = entry.date.strftime('%Y-%m-%d')
        date_to_reps[date_str] = date_to_reps.get(date_str, 0) + entry.repetitions
    # Pass data as JSON
    exercises_json = json.dumps(exercises)
    dates = list(date_to_reps.keys())
    reps = list(date_to_reps.values())

    return render_template(
        'myprogress.html',
        exercises_json=exercises_json,
        dates=dates,
        reps=reps, user_initial=user_initial
    )

@app.route('/diet')
def diet():
    user_initial = session.get('user_initial', 'U')  # Default to 'U' if not logged in
    return render_template('mydiet.html', user_initial=user_initial)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("hello_world"))


@app.route('/signup', methods=['GET', 'POST'])
def sign():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        ph_no=request.form['ph_no']  # Store password as plain text

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("User already exists. Please login.")
            return redirect("/login")

        # Add new user to the database
        new_user = User(username=username, email=email, password=password,ph_no=ph_no)
        db.session.add(new_user)
        db.session.commit()
        flash("Sign-up successful. Please log in.")
        return redirect("/login")

    return render_template('signup.html')


if __name__=="__main__":
    #with app.app_context():
    #    db.create_all()
    app.run(debug=True)
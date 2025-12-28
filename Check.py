# Import required libraries  
import cv2
import os
import pickle
import face_recognition
import numpy as np
import cvzone
import json
from supabase import create_client, Client
import time
import requests
from datetime import datetime

# Load Supabase credentials from JSON file            
with open("supabase_admin.json") as f:
    config = json.load(f)

SUPABASE_URL = config["project_url"]
SUPABASE_SERVICE_KEY = config["service_role_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)  
print("✅ Supabase client initialized!")

# Create unauthorized folder if it doesn't exist
if not os.path.exists("unauthorized"):
    os.makedirs("unauthorized")

# Function to update student attendance (grant count)
def update_attendance(student_id):
    try:
        current_data = supabase.table("students").select("total_grants").eq("id", student_id).single().execute()
        if current_data.data:
            current_grants = current_data.data["total_grants"]
            response = supabase.table("students").update({
                "total_grants": current_grants + 1,
                "last_granting_time": datetime.utcnow().isoformat()
            }).eq("id", student_id).execute()
            if response.data:
                print(f"✅ Grant count updated for student ID {student_id}")
                return "success"
        return "fail"
    except Exception as e:
        print(f"❌ Error updating grants: {e}")
        return "error"

# Load student image from local or URL
def load_student_image(student):
    local_path = os.path.join("Images", f"{student['id']}.png")
    if os.path.exists(local_path):
        return cv2.imread(local_path)
    elif student.get("image_url"):
        try:
            response = requests.get(student["image_url"], timeout=5)
            img_array = np.frombuffer(response.content, np.uint8)
            return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"⚠ Failed to fetch image from URL for {student['id']}: {e}")
    return np.zeros((216, 216, 3), dtype=np.uint8)  # Return blank image if unavailable

# Draw status text inside webcam feed
def draw_status_text_on_webcam(img, status, color):
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, f"Status: {status}", (10, 470), font, 0.8, color, 2, cv2.LINE_AA)

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Width
cap.set(4, 480)  # Height

# Load UI elements
imgBackground = cv2.imread('Resources/background.png')
folderModePath = 'Resources/Modes'
imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in os.listdir(folderModePath)]
mode_active = cv2.imread(os.path.join(folderModePath, 'active.png'))
marked_screen = cv2.imread(os.path.join(folderModePath, 'marked_screen.png'))

# Load face encodings
print("Loading Encode File...")
with open('EncodeFile.p', 'rb') as file:
    encodeListKnown, studentIds = pickle.load(file)
print("✅ Encode File Loaded")

# Initialize variables for app logic
modeType = 0
counter = 0
id = -1
imgStudent = []
status_message = "Scanning"
status_color = (0, 255, 255)
last_attendance_time = {}
attendance_delay = 10  # Minimum time between re-grants per student

detected_students = set()
student = None

# Logic control flags
last_action_time = 0
action_cooldown = 5  # Seconds between actions
unauth_frame_count = 0
unauth_threshold = 7  # Frames to confirm unauthorized face
unknown_face_detected = False
unknown_face_location = None
unknown_face_image = None
face_distance_threshold = 0.5
unknown_distance_threshold = 0.7

show_marked_screen = False  # UI flag

# Start processing webcam frames
while True:
    success, img = cap.read()
    if not success:
        print("❌ Failed to capture image!")
        break

    current_time = time.time()

    # Resize frame for faster face recognition
    small_img = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
    small_img_rgb = cv2.cvtColor(small_img, cv2.COLOR_BGR2RGB)

    # Detect face(s)
    faceCurFrame = face_recognition.face_locations(small_img_rgb)
    encodeCurFrame = face_recognition.face_encodings(small_img_rgb, faceCurFrame)

    # Draw webcam feed on UI background
    imgBackground[162:162 + 480, 55:55 + 640] = img
    status_message = "Scanning..."
    status_color = (0, 255, 255)

    # Show marked screen during cooldown
    if current_time - last_action_time < action_cooldown and show_marked_screen:
        imgBackground[44:44 + 633, 808:808 + 414] = marked_screen

    # No face detected
    elif len(faceCurFrame) == 0:
        imgBackground[44:44 + 633, 808:808 + 414] = mode_active
        student = None
        unknown_face_detected = False
        unauth_frame_count = 0

    # Cooldown in progress
    elif current_time - last_action_time < action_cooldown:
        status_message = "Processing..."
        status_color = (200, 200, 0)
        if show_marked_screen:
            imgBackground[44:44 + 633, 808:808 + 414] = marked_screen

    # Face detected, process recognition
    else:
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
        show_marked_screen = False

        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis) if faceDis.size > 0 else -1

            y1, x2, y2, x1 = [val * 4 for val in faceLoc]
            bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
            imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

            # Known face detected
            if matchIndex != -1 and matches[matchIndex] and faceDis[matchIndex] < face_distance_threshold:
                unknown_face_detected = False
                unauth_frame_count = 0
                student_id = studentIds[matchIndex]

                if student_id not in detected_students:
                    detected_students.add(student_id)
                    if student_id not in last_attendance_time or (current_time - last_attendance_time[student_id] >= attendance_delay):
                        result = update_attendance(student_id)
                        last_attendance_time[student_id] = current_time
                        if result == "success":
                            status_message = "Access Granted"
                            status_color = (0, 200, 0)
                            modeType = 1
                            show_marked_screen = True
                        else:
                            status_message = "Access Failed"
                            status_color = (0, 0, 255)

                id = student_id
                counter = 1
                last_action_time = time.time()

            # Unknown face confirmed
            elif faceDis.size > 0 and faceDis[matchIndex] > unknown_distance_threshold:
                if not unknown_face_detected:
                    unknown_face_detected = True
                    unknown_face_location = (x1, y1, x2, y2)
                    unknown_face_image = img[y1:y2, x1:x2]
                    unauth_frame_count = 0
                elif (x1, y1, x2, y2) == unknown_face_location:
                    unauth_frame_count += 1
                    if unauth_frame_count >= unauth_threshold:
                        print("🚨 Unauthorized face confirmed!")
                        unauth_img_path = f"unauthorized/{int(current_time)}.jpg"
                        cv2.imwrite(unauth_img_path, unknown_face_image)
                        status_message = "Unauthorized"
                        status_color = (0, 0, 255)
                        imgBackground = cvzone.cornerRect(imgBackground, (55 + x1, 162 + y1, x2 - x1, y2 - y1), rt=0, colorC=(0, 0, 255))
                        student = None
                        id = -1
                        counter = 0
                        modeType = 0
                        imgStudent = []
                        last_action_time = current_time
                        unknown_face_detected = False
                        unauth_frame_count = 0
                        imgBackground[44:44 + 633, 808:808 + 414] = mode_active
                        break
                else:
                    unknown_face_detected = True
                    unknown_face_location = (x1, y1, x2, y2)
                    unknown_face_image = img[y1:y2, x1:x2]
                    unauth_frame_count = 1

    # Display student info on UI if recognized
    if counter != 0:
        if counter == 1:
            studentInfo = supabase.table("students").select("*").eq("id", id).single().execute()
            student = studentInfo.data
            if student:
                imgStudent = load_student_image(student)
                imgStudent = cv2.resize(imgStudent, (216, 216))

        modeType = 1 if 1 <= counter <= 10 else 2 if 10 < counter <= 30 else 0
        counter = 0
        detected_students.clear()

        if student is not None and id != -1:
            cv2.putText(imgBackground, str(student['total_grants']), (861, 125), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
            cv2.putText(imgBackground, str(student['technical_department']), (1006, 550), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(imgBackground, str(student['id']), (1006, 493), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            (w, h), _ = cv2.getTextSize(student['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
            offset = (414 - w) // 2
            cv2.putText(imgBackground, str(student['name']), (808 + offset, 445), cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)
            imgBackground[175:175 + 216, 909:909 + 216] = imgStudent

    # Draw final status
    draw_status_text_on_webcam(imgBackground[162:162 + 480, 55:55 + 640], status_message, status_color)

    # Show result
    cv2.imshow("Face Attendance", imgBackground)

    time.sleep(0.05)  # Delay for ~20 FPS                

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("🛑 Stopping the webcam...")
        break

cap.release()
cv2.destroyAllWindows()                                                     
import cv2
import face_recognition
import pickle
import os

# Path to student images
folderPath = 'Images'
pathList = os.listdir(folderPath)

# Filter only image files (e.g., jpg, jpeg, png)
valid_exts = ('.jpg', '.jpeg', '.png')
pathList = [file for file in pathList if file.lower().endswith(valid_exts)] 

print("Found image files:", pathList)

imgList = []
studentIds = []

for path in pathList:
    img_path = os.path.join(folderPath, path)
    img = cv2.imread(img_path)

    # Check for valid image read
    if img is None:
        print(f"⚠️ Warning: Could not read image: {img_path}")
        continue

    imgList.append(img)
    studentIds.append(os.path.splitext(path)[0])  # Remove extension to get ID

print("Student IDs:", studentIds)

def findEncodings(imagesList):
    encodeList = []
    for index, img in enumerate(imagesList):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img_rgb)

        if encodings:
            encodeList.append(encodings[0])
        else:
            print(f"⚠️ Warning: No face found in image for ID: {studentIds[index]}")

    return encodeList

print("🔍 Encoding Started...")
encodeListKnown = findEncodings(imgList)

# Final data structure to save
encodeListKnownWithIds = [encodeListKnown, studentIds]
print("✅ Encoding Complete")

# Save to file
with open("EncodeFile.p", "wb") as file:
    pickle.dump(encodeListKnownWithIds, file)

print("💾 Encodings saved to EncodeFile.p")

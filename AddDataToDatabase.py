import os
import json
from supabase import create_client, Client

#  Load credentials
with open("supabase_admin.json") as f:
    config = json.load(f)

#  Supabase project  
SUPABASE_URL = config["project_url"]
SUPABASE_SERVICE_KEY = config["service_role_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) 
print("✅ Supabase client initialized successfully!")

#  Define student records
student_data = [
    {
        "id": "321654",
        "name": "Sourav Nandi",
        "technical_department": "Robotics",
        "total_grants": 0,
        "last_granting_time": "2025-04-19 00:54:34"   
    },
    {
        "id": "852741",
        "name": "Avay Mallick",
        "technical_department": "Robotics",
        "total_grants": 0,
        "last_granting_time": "2025-04-19 00:54:59" 
    },
    {
        "id": "963852",
        "name": "Vishal Prasad Gupta",
        "technical_department": "Robotics",
        "total_grants": 0,
        "last_granting_time": "2025-04-19 00:54:51"
    },
]

#  Insert or update students in Supabase DB
response = supabase.table("students").upsert(student_data).execute()    
if response.data:
    print("🎉 Students added/updated successfully:")
    for student in response.data:
        print(student)
else:
    print("❌ Operation failed:", response)

#  Upload images and update image URLs
bucket_name = "student-images"
image_folder = r"C:\Users\hp\OneDrive\Desktop\Sourav.python\Images"
allowed_extensions = [".jpg", ".jpeg", ".png"]

for student in student_data:
    student_id = student["id"]
    image_path = None

    # Detect the correct image file extension
    for ext in allowed_extensions:
        candidate_path = os.path.join(image_folder, f"{student_id}{ext}")
        if os.path.exists(candidate_path):
            image_path = candidate_path
            break

    if not image_path:
        print(f"⚠️ Image not found for student ID {student_id}")
        continue

    # Set file extension and MIME type
    file_ext = os.path.splitext(image_path)[1].lower()
    mime_type = "image/jpeg" if file_ext in [".jpg", ".jpeg"] else "image/png"  
    storage_path = f"{student_id}{file_ext}"

    # Check if the file already exists in Supabase Storage
    try:
        files = supabase.storage.from_(bucket_name).list()
        existing_files = [file['name'] for file in files]
        
        if storage_path in existing_files:
            print(f"⚠️ Image for student ID {student_id} already exists in storage, skipping upload.")
            continue
    except Exception as e:
        print(f"❌ Error checking if file exists for {student_id}: {e}")

    # Read image bytes
    with open(image_path, "rb") as f:
        file_bytes = f.read()

    # Upload to Supabase Storage
    try:
        supabase.storage.from_(bucket_name).upload(
            storage_path, file_bytes, {
                "content-type": mime_type
            }
        )
        print(f"📤 Uploaded image for student ID {student_id}")
    except Exception as e:
        print(f"❌ Failed to upload image for {student_id}: {e}")
        continue

    # Generate public URL
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{storage_path}"

    # Update database with image_url
    update_response = supabase.table("students").update({"image_url": public_url}).eq("id", student_id).execute()
    if update_response.data:
        print(f"🔗 Linked image to student {student_id}: {public_url}")
    else:
        print(f"❌ Failed to update student {student_id} with image URL")

print("✅ All done!")

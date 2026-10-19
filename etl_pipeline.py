from __future__ import annotations
import json
import os
from dotenv import load_dotenv  # optional if using .env file
from google import genai
from google.genai import types
import pandas as pd

load_dotenv()

# 1. Initialize Gemini client using the modern SDK
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def clean_row_with_gemini(dirty_data_string):
  """Sends a dirty row of data to Gemini to be cleaned and formatted."""
  prompt = f"""
    You are an expert data cleaning assistant. I will give you a row of student data that contains errors, typos, improper casing, or missing values.
    
    Clean the data and return it strictly as a JSON object with these exact keys:
    - "Student_ID": Keep as-is or fix formatting if broken.
    - "Name": Fix typos, capitalize properly (e.g., "john doe" -> "John Doe").
    - "Email": Convert to strictly lowercase and ensure valid formatting.
    - "Phone": Standardize format if possible, or leave clean string.
    - "Course": Standardize name if there are obvious typos.
    - "Fee_Paid": Ensure it's a clean number or standardized currency representation.
    - "City": Capitalize properly (e.g., "new york" -> "New York").
    - "Enrolled_Date": Standardize to YYYY-MM-DD format if possible.
    - "Email_Valid": Evaluate if the email looks logically valid (True/False).

    Dirty Data: {dirty_data_string}
    """

  try:
    # Use modern Gemini generate_content syntax with the active model
    response = client.models.generate_content(
        model="gemini-3.8-flash",  # Updated to active standard endpoint
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",  # Forces Gemini to return valid JSON
            temperature=0.1,
        ),
    )

    # Parse and return the JSON response
    cleaned_json = json.loads(response.text)
    return cleaned_json
  except Exception as e:
    print(f"Error cleaning data: {e}")
    return None


def run_etl(input_file, output_file):
  # --- STEP 1 & 2: Load and Read the File ---
  print(f"🔄 Loading {input_file}...")
  if not os.path.exists(input_file):
    print(f"❌ Error: {input_file} not found in directory.")
    return

  df = pd.read_csv(input_file)
  cleaned_rows = []

  # --- STEP 3: Clean the Data with Gemini ---
  print("🧠 Cleaning data with Gemini (this might take a moment)...")
  for index, row in df.iterrows():
    dirty_string = row.to_dict()

    print(f"Processing row {index + 1}/{len(df)}...")
    cleaned_data = clean_row_with_gemini(dirty_string)

    if cleaned_data:
      cleaned_rows.append(cleaned_data)
    else:
      # Fallback if API fails: keep original data
      cleaned_rows.append(dirty_string)

  # --- STEP 4: Create the Final CSV File ---
  print(f"💾 Saving cleaned data to {output_file}...")
  cleaned_df = pd.DataFrame(cleaned_rows)
  cleaned_df.to_csv(output_file, index=False)

  print("✅ ETL Pipeline Completed Successfully!")


if __name__ == "__main__":
  # Replace these with your actual file paths
  INPUT_CSV = "student_enrollment_raw.csv"
  OUTPUT_CSV = "clean_students.csv"

  run_etl(INPUT_CSV, OUTPUT_CSV)
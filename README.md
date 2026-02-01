Instructions to Setup and Run Locally

Clone the GitHub Repository
git clone https://github.com/ej6139/TTB

Create Virtual Environment
python -m venv venv
venv\Scripts\activate

Install dependencies
pip install -r requirements.txt

Create a Microsoft Azure account to get API key and endpoint URL

Create .env file with the following:
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

Run app
python app.py


Usage Instructions

Single Label Verification
Enter Application Data - The information from the COLA form:

Brand Name (e.g., "OLD TOM DISTILLERY")
Class/Type (e.g., "Kentucky Straight Bourbon Whiskey")
Alcohol Content (e.g., "45% Alc./Vol. (90 Proof)")
Net Contents (e.g., "750 mL")

Upload Label Image - Click or drag-and-drop
Click "Verify Label"
Review Results - Each field shows:

Extracted value from label
Match/mismatch status
Overall APPROVED/REJECTED decision


Batch Processing

Upload Multiple Labels - Select or drag multiple images
Add Application Data - CSV format, one row per label:

OLD TOM DISTILLERY, Kentucky Straight Bourbon Whiskey, 45% Alc./Vol., 750 mL

Click "Process Batch" - View summary and individual results

import os
import base64
import json
import io
import traceback

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from PIL import Image
from openai import AzureOpenAI

load_dotenv()

app = Flask(__name__)
CORS(app)

AZURE_DEPLOYMENT_NAME = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')

client = AzureOpenAI(
    api_key=os.environ.get('AZURE_OPENAI_API_KEY'),
    api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
    azure_endpoint=os.environ.get('AZURE_OPENAI_ENDPOINT')
)

# Standard government warning
STANDARD_WARNING = """GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."""

def verify_label_with_gpt4_vision(image_data, application_data):
    """Use Azure OpenAI GPT-4o to extract and verify label information."""
    try:
        prompt = f"""You are an expert TTB (Alcohol and Tobacco Tax and Trade Bureau) compliance agent reviewing an alcohol beverage label.

Extract the following information from the label image:
1. Brand Name
2. Class/Type (e.g., "Kentucky Straight Bourbon Whiskey", "Vodka", "Red Wine")
3. Alcohol Content (e.g., "45% Alc./Vol.", "90 Proof")
4. Net Contents (e.g., "750 mL")
5. Government Warning Statement (look for text starting with "GOVERNMENT WARNING:")

Then compare what you extracted with the application data provided below:
{json.dumps(application_data, indent=2) if application_data else "No application data provided"}

For each field:
- Indicate if it matches the application data
- Be flexible with minor formatting differences (e.g., "STONE'S THROW" vs "Stone's Throw")
- For the Government Warning, it MUST be word-for-word exact, with "GOVERNMENT WARNING:" in all caps and bold

Provide your response in the following JSON format:
{{
    "extracted": {{
        "brand_name": "extracted value or null",
        "class_type": "extracted value or null",
        "alcohol_content": "extracted value or null",
        "net_contents": "extracted value or null",
        "government_warning_present": true/false,
        "government_warning_correct": true/false
    }},
    "verification": {{
        "brand_name_match": true/false,
        "class_type_match": true/false,
        "alcohol_content_match": true/false,
        "net_contents_match": true/false,
        "government_warning_valid": true/false
    }},
    "issues": [
        "List any compliance issues found"
    ],
    "overall_status": "APPROVED" or "REJECTED",
    "confidence": 0-100,
    "notes": "Any additional observations"
}}

Be strict about the Government Warning - it must be exact. Be reasonable about other fields - minor formatting differences are acceptable."""

        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip()
        
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(result_text)
        return result
        
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse AI response",
            "extracted": {},
            "verification": {},
            "issues": ["AI response format error - try uploading a clearer image"],
            "overall_status": "ERROR",
            "confidence": 0
        }
    except Exception as e:
        error_message = str(e)
        print(f"Azure OpenAI API Error: {error_message}")
        traceback.print_exc()
        
        if "AuthenticationError" in error_message or "401" in error_message:
            error_detail = "Azure OpenAI authentication failed. Check AZURE_OPENAI_API_KEY."
        elif "NotFoundError" in error_message or "404" in error_message:
            error_detail = "Deployment not found. Check AZURE_OPENAI_DEPLOYMENT_NAME and AZURE_OPENAI_ENDPOINT."
        elif "RateLimitError" in error_message or "429" in error_message:
            error_detail = "Rate limit exceeded. Please wait and try again."
        else:
            error_detail = error_message
            
        return {
            "error": f"Azure OpenAI API Error: {error_detail}",
            "extracted": {},
            "verification": {},
            "issues": [f"API Error: {error_detail}"],
            "overall_status": "ERROR",
            "confidence": 0
        }


def process_image(image_file):
    """Read and process an image file, returning base64-encoded JPEG."""
    image_bytes = image_file.read()
    img = Image.open(io.BytesIO(image_bytes))
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    max_size = 2048
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=95)
    return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/verify-label', methods=['POST'])
def verify_label():
    """Verify a single label."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        try:
            image_base64 = process_image(image_file)
        except Exception as e:
            return jsonify({'error': f'Invalid image file: {str(e)}'}), 400
        
        application_data = {}
        if 'application_data' in request.form:
            try:
                application_data = json.loads(request.form['application_data'])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid application data JSON'}), 400
        
        result = verify_label_with_gpt4_vision(image_base64, application_data)
        return jsonify(result)
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/verify-batch', methods=['POST'])
def verify_batch():
    """Verify multiple labels."""
    try:
        if 'images[]' not in request.files:
            return jsonify({'error': 'No image files provided'}), 400
        
        image_files = request.files.getlist('images[]')
        if len(image_files) == 0:
            return jsonify({'error': 'No images selected'}), 400
        
        applications_data = []
        if 'applications_data' in request.form:
            try:
                applications_data = json.loads(request.form['applications_data'])
            except json.JSONDecodeError:
                pass
        
        while len(applications_data) < len(image_files):
            applications_data.append({})
        
        results = []
        
        # Process each image sequentially
        for idx, image_file in enumerate(image_files):
            try:
                image_base64 = process_image(image_file)
                app_data = applications_data[idx] if idx < len(applications_data) else {}
                
                result = verify_label_with_gpt4_vision(image_base64, app_data)
                result['filename'] = image_file.filename
                result['index'] = idx
                results.append(result)
    
            except Exception as e:
                results.append({
                    'filename': image_file.filename,
                    'index': idx,
                    'error': str(e),
                    'overall_status': 'ERROR'
                })
        
        return jsonify({'results': results})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
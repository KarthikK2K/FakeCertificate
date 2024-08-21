import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# JSON file to store details
details_file = 'details.json'

# Ensure the details file exists
if not os.path.exists(details_file):
    with open(details_file, 'w') as f:
        json.dump([], f)

# Function to load details from the JSON file
def load_details():
    with open(details_file, 'r') as f:
        return json.load(f)

# Function to save details to the JSON file
def save_details(details):
    with open(details_file, 'w') as f:
        json.dump(details, f)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Dummy classifier for example
def classify_document(image_path):
    # Load image and process it as per your model requirements
    # This is a placeholder function. Replace with your actual classification logic.
    image = cv2.imread(image_path)
    features = cv2.resize(image, (224, 224)) / 255.0
    features = np.expand_dims(features, axis=0)
    
    model = load_model('model.h5')
    result = model.predict(features)
    result = (result > 0.5).astype(int)
    return result[0][0]

# Route for home page
@app.route('/')
def home():
    return render_template('home.html')

# Route for uploading a new file
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        name = request.form['name']
        branch = request.form['branch']
        email = request.form['email']
        subject = request.form['subject']
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Store the details
            details = load_details()
            details.append({
                'name': name,
                'branch': branch,
                'email': email,
                'subject': subject,
                'filename': filename
            })
            save_details(details)

            # Classify the document
            label = classify_document(filepath)
            label = "Real" if label == 1 else "Fake"

            return redirect(url_for('uploaded_file', label=label, filename=filename))
    return render_template('index.html')

@app.route('/uploads/<label>/<filename>')
def uploaded_file(label, filename):
    return render_template('result.html', label=label, filename=filename)

# Route for view certificates page
@app.route('/view')
def view_certificates():
    details = load_details()
    return render_template('view.html', details=details)

# Route to delete a certificate
@app.route('/delete/<int:index>', methods=['POST'])
def delete_certificate(index):
    details = load_details()
    if 0 <= index < len(details):
        # Remove the file from the filesystem
        filename = details[index]['filename']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)

        # Remove the entry from the details list
        del details[index]
        save_details(details)
    return redirect(url_for('view_certificates'))

# Route for about us page
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)

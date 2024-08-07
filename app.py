import os
from flask import Flask, redirect, render_template, request, url_for, jsonify
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Azure Blob Storage configuration
ACCOUNT_NAME = 'storagefordocuments'
ACCOUNT_KEY = 'iJUk9AcoGQpU8gn2GS8HQcG+XrxvRuIdCMSUvGe71thokS78AF25CbVAtSBJF+E3WbrILxptu3GW+AStlKRHCg=='
AZURE_STORAGE_CONNECTION_STRING = (
    f'DefaultEndpointsProtocol=https;'
    f'AccountName={ACCOUNT_NAME};'
    f'AccountKey={ACCOUNT_KEY};'
    f'BlobEndpoint=https://{ACCOUNT_NAME}.blob.core.windows.net/;'
)
CONTAINER_NAME = 'pdfstorage'

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/process_file', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Upload to Azure Blob Storage
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=filename)
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        os.remove(file_path)
        return jsonify({'message': 'File successfully uploaded', 'filename': filename})

    return jsonify({'error': 'File upload failed'}), 500

@app.route('/chat')
def chat():
    return render_template('chat.html')

if __name__ == '__main__':
    app.run(debug=True)

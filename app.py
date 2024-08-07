import os
from flask import Flask, redirect, render_template, request, url_for, jsonify, send_from_directory
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Key Vault Configuration
key_vault_name = "documentqa"
kv_uri = f"https://{key_vault_name}.vault.azure.net"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=kv_uri, credential=credential)

def get_secret(secret_name):
    try:
        secret = client.get_secret(secret_name)
        return secret.value
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {e}")
        return None

# Retrieve Azure Blob Storage connection details from Key Vault
ACCOUNT_NAME = get_secret("azure-storage-account-name")
ACCOUNT_KEY = get_secret("azure-storage-account-key")
AZURE_STORAGE_CONNECTION_STRING = get_secret("azure-storage-connection-string")
CONTAINER_NAME = get_secret("azure-storage-container-name")

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
    try:
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

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/chat')
def chat():
    return render_template('chat.html')

if __name__ == '__main__':
    app.run(debug=True)

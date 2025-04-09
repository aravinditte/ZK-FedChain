import requests
import os
from dotenv import load_dotenv
import json
import sys

class IPFSHandler:
    def __init__(self, api_url=None):
        # Load environment variables
        load_dotenv()
        
        # Set default API URL if not provided
        self.api_url = api_url or os.getenv('IPFS_API_URL', 'http://127.0.0.1:5001')

    def add_file(self, file_path):
        """
        Add a file to IPFS and return its CID (Content Identifier).
        """
        try:
            with open(file_path, 'rb') as f:
                response = requests.post(
                    f"{self.api_url}/api/v0/add",
                    files={'file': f}
                )
            response.raise_for_status()
            return response.json()['Hash']
        except Exception as e:
            raise RuntimeError(f"Failed to add file to IPFS: {e}")

    def add_json(self, json_data):
        """
        Add JSON data to IPFS and return its CID.
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/v0/add",
                files={'file': ('data.json', json.dumps(json_data), 'application/json')}
            )
            response.raise_for_status()
            return response.json()['Hash']
        except Exception as e:
            raise RuntimeError(f"Failed to add JSON to IPFS: {e}")

    def get_file(self, file_hash, output_path):
        """
        Retrieve a file from IPFS using its CID and save it to the specified output path.
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/v0/cat",
                params={'arg': file_hash}
            )
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve file from IPFS: {e}")

    def get_json(self, file_hash):
        """
        Retrieve JSON data from IPFS using its CID.
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/v0/cat",
                params={'arg': file_hash}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve JSON from IPFS: {e}")

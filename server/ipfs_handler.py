import ipfshttpclient
import json
import os
from dotenv import load_dotenv

load_dotenv()

class IPFSHandler:
    def __init__(self, api_url=None):
        # Use environment variable if not provided
        self.api_url = api_url or os.getenv('IPFS_API_URL', '/ip4/127.0.0.1/tcp/5001')
        self.client = ipfshttpclient.connect(self.api_url)

    def add_file(self, file_path):
        res = self.client.add(file_path)
        return res['Hash']

    def add_json(self, json_data):
        res = self.client.add_json(json_data)
        return res

    def get_file(self, file_hash, output_path):
        self.client.get(file_hash, output_path)

    def get_json(self, json_hash):
        return self.client.get_json(json_hash)

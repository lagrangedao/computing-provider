import logging
import os
from pathlib import Path

from flask import render_template, Blueprint, jsonify
from eth_keys import keys

views_blueprint = Blueprint("views", __name__)


@views_blueprint.get("/")
def home():
    return render_template("index.html")


@views_blueprint.route('/boot', methods=['GET'])
def generate_key():
    private_key_path = Path(".swan_node/private_key")

    # Check if the private key file exists
    if private_key_path.is_file():
        # Read the private key from the file
        with open(private_key_path, "r") as f:
            hex_private_key = f.readline().strip()
        private_key_bytes = bytes.fromhex(hex_private_key)
        logging.info("Found key in %s" % private_key_path)
    else:
        logging.info("Created key in %s" % private_key_path)
        # Generate a new private key
        private_key_bytes = os.urandom(32)

        # Get the hexadecimal representation of the private key
        hex_private_key = private_key_bytes.hex()

        # Write the private key to a file
        private_key_path.parent.mkdir(parents=True, exist_ok=True)
        with open(private_key_path, "w") as f:
            f.write(hex_private_key)

    # Create a PrivateKey object from the private key bytes
    private_key = keys.PrivateKey(private_key_bytes)

    # Derive the node ID using the public key in hexadecimal format
    node_id = private_key.public_key.to_hex()

    logging.info("Node id: %s" % node_id)
    return jsonify({'node_id': node_id})

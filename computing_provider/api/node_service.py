import logging
import os
from pathlib import Path

from eth_keys import keys
import hashlib


def generate_node_id():
    private_key_path = Path(".swan_node/private_key")
    # Check if the private key storage exists
    if private_key_path.is_file():
        # Read the private key from the storage
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

        # Write the private key to a storage
        private_key_path.parent.mkdir(parents=True, exist_ok=True)
        with open(private_key_path, "w") as f:
            f.write(hex_private_key)
    # Create a PrivateKey object from the private key bytes
    private_key = keys.PrivateKey(private_key_bytes)
    # Derive the node ID using the public key in hexadecimal format
    node_id = private_key.public_key.to_hex()
    peer_id = hash_public_key(private_key.public_key).hex()
    return node_id, peer_id


def hash_public_key(public_key) -> bytes:
    # Convert the public key to bytes and hash it using SHA256
    public_key_bytes = public_key.to_bytes()
    hash_obj = hashlib.sha256()
    hash_obj.update(public_key_bytes)
    hash_digest = hash_obj.digest()

    # Return the hash digest as the peer ID
    return hash_digest

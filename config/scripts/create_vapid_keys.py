import base64
import os

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from py_vapid import Vapid

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
webpush_dir = os.path.join(PROJECT_ROOT, "keys", "webpush")

os.makedirs(os.path.join(PROJECT_ROOT, "keys", "webpush"))

# Generate VAPID key pair
vapid = Vapid()
vapid.generate_keys()

# Get public and private keys for the vapid key pair
vapid.save_public_key(os.path.join(webpush_dir, "public_key.pem"))
public_key_bytes = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)

vapid.save_key(os.path.join(PROJECT_ROOT, "keys", "webpush", "private_key.pem"))


# Convert the public key to applicationServerKey format
application_server_key = base64.urlsafe_b64encode(public_key_bytes).replace(b"=", b"").decode("utf8")

with open(os.path.join(webpush_dir, "ApplicationServerKey.key"), "w", encoding="utf-8") as f:
    f.write(application_server_key)

# Verify keys created
if not os.path.exists(webpush_dir):
    print("Error occurred creating vapid keys")
    exit(1)
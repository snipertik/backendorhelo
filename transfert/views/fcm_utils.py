import os
import logging
from pathlib import Path
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)

TOKEN_FILE_PATH = os.path.join(settings.BASE_DIR, "token_admin.txt")

# 🔹 Initialisation Firebase
try:
    cred_path = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS",
        os.path.join(settings.BASE_DIR, "backendorhelo/firebase-key.json")
    )

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
except Exception as e:
    logger.error(f"Erreur initialisation Firebase : {e}")

# 🔹 Envoi de notification à l'admin
def envoyer_notification_fcm(titre, corps):
    try:
        token_path = Path(TOKEN_FILE_PATH)
        if not token_path.exists():
            logger.warning("Aucun token admin enregistré")
            return

        with open(token_path, "r") as f:
            token_admin = f.read().strip()

        message = messaging.Message(
            notification=messaging.Notification(
                title=titre,
                body=corps
            ),
            token=token_admin
        )

        response = messaging.send(message)
        logger.info(f"Notification envoyée : {response}")

    except Exception as e:
        logger.error(f"Erreur envoi FCM : {e}")

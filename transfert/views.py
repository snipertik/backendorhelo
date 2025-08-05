from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.contrib.auth.hashers import make_password, check_password
from .models import Utilisateur, DemandeTransfert
from rest_framework.generics import ListAPIView
import firebase_admin
from firebase_admin import credentials, messaging
import os
from django.conf import settings
from pathlib import Path
import logging

# 📌 Logger pour enregistrer les erreurs en prod
logger = logging.getLogger(__name__)

# 📌 Fichier local pour sauvegarder le token admin (utiliser la base en prod)
TOKEN_FILE_PATH = os.path.join(settings.BASE_DIR, "token_admin.txt")


# 📦 API pour enregistrer le token admin FCM
class EnregistrerTokenAdminView(APIView):
    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token manquant"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with open(TOKEN_FILE_PATH, "w") as f:
                f.write(token.strip())
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du token : {e}")
            return Response({"error": "Impossible d'enregistrer le token"}, status=500)

        return Response({"message": "Token enregistré avec succès"})


# 📌 Chargement clé Firebase
try:
    cred_path = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS",
        os.path.join(settings.BASE_DIR, "backendorhelo/firebase-key.json")  # chemin local dev
    )

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
except Exception as e:
    logger.error(f"Erreur initialisation Firebase : {e}")


# 📦 API d'inscription
class InscriptionView(APIView):
    def post(self, request):
        data = request.data
        nom_complet = data.get('nom_complet')
        numero = data.get('numero')
        pin = data.get('pin')
        confirmation_pin = data.get('confirmation_pin')

        # ✅ Validation des champs
        if not nom_complet or not numero or not pin or not confirmation_pin:
            return Response({"error": "Tous les champs sont requis."}, status=status.HTTP_400_BAD_REQUEST)

        if not pin.isdigit():
            return Response({"error": "Le code PIN doit contenir uniquement des chiffres."}, status=400)

        if len(pin) != 4:
            return Response({"error": "Le code PIN doit contenir exactement 4 chiffres."}, status=status.HTTP_400_BAD_REQUEST)

        if pin != confirmation_pin:
            return Response({"error": "Les deux codes PIN ne correspondent pas."}, status=status.HTTP_400_BAD_REQUEST)

        # ❌ Vérifier si le numéro est déjà pris
        if Utilisateur.objects.filter(numero=numero).exists():
            return Response({"error": "Ce numéro est déjà inscrit."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Création utilisateur
        utilisateur = Utilisateur.objects.create(
            nom_complet=nom_complet,
            numero=numero,
            code_pin=make_password(pin)
        )

        return Response({"message": "Inscription réussie !", "id": utilisateur.id}, status=status.HTTP_201_CREATED)


# 🔐 API de connexion
class ConnexionView(APIView):
    def post(self, request):
        data = request.data
        numero = data.get('numero')
        pin = request.data.get('pin')

        if not numero or not pin:
            return Response({"error": "Numéro et PIN requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            utilisateur = Utilisateur.objects.get(numero=numero)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)

        if not check_password(pin, utilisateur.code_pin):
            return Response({"error": "Code PIN incorrect."}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"message": "Connexion réussie.", "id": utilisateur.id, "nom": utilisateur.nom_complet}, status=status.HTTP_200_OK)


# 🔓 API de déverrouillage
class DeverrouillageView(APIView):
    def post(self, request):
        data = request.data
        id_utilisateur = data.get('id_utilisateur')
        pin = data.get('pin')

        if not id_utilisateur or not pin:
            return Response({"error": "ID utilisateur et PIN requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            utilisateur = Utilisateur.objects.get(id=id_utilisateur)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)

        if not check_password(pin, utilisateur.code_pin):
            return Response({"error": "Code PIN incorrect."}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"message": "Déverrouillage réussi."}, status=status.HTTP_200_OK)


# 📨 Soumission d'une demande de transfert
class SoumissionTransfertView(APIView):
    def post(self, request):
        data = request.data
        id_utilisateur = data.get('id_utilisateur')
        numero_destinataire = data.get('numero_destinataire')
        reseau = data.get('reseau')
        montant = data.get('montant')
        numero_wave = data.get('numero_wave')
        methode_paiement = data.get('methode_paiement')

        # ✅ Validation stricte (montant peut être 0 donc != all([...]))
        if not id_utilisateur or not numero_destinataire or not reseau or montant is None or not numero_wave or not methode_paiement:
            return Response({"error": "Tous les champs sont obligatoires."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            montant = int(montant)
            if montant <= 0:
                return Response({"error": "Le montant doit être supérieur à 0."}, status=400)
        except ValueError:
            return Response({"error": "Montant invalide."}, status=400)

        try:
            utilisateur = Utilisateur.objects.get(id=id_utilisateur)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)

        demande = DemandeTransfert.objects.create(
            utilisateur=utilisateur,
            numero_destinataire=numero_destinataire,
            reseau=reseau.lower(),
            montant=montant,
            numero_wave=numero_wave,
            methode_paiement=methode_paiement.lower(),
            statut='en_attente'
        )

        # 🔔 Notification admin
        self.envoyer_notification_fcm(
            titre="Nouvelle demande",
            corps=f"{reseau.upper()} - {montant} F pour {numero_destinataire}"
        )

        return Response({"message": "Demande enregistrée avec succès.", "id_demande": demande.id}, status=status.HTTP_201_CREATED)

    def envoyer_notification_fcm(self, titre, corps):
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


# 🎯 Sérialiseur
class DemandeTransfertSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeTransfert
        fields = '__all__'


# 📡 Liste demandes en attente (admin)
class DemandesEnAttenteView(ListAPIView):
    queryset = DemandeTransfert.objects.filter(statut='en_attente').order_by('-date_creation')
    serializer_class = DemandeTransfertSerializer


# ✅ Validation demande (admin)
class ValidationDemandeView(APIView):
    def post(self, request):
        data = request.data
        id_demande = data.get('id_demande')
        code_ussd = data.get('code_ussd', None)

        if not id_demande:
            return Response({"error": "ID de la demande requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            demande = DemandeTransfert.objects.get(id=id_demande)
        except DemandeTransfert.DoesNotExist:
            return Response({"error": "Demande introuvable."}, status=status.HTTP_404_NOT_FOUND)

        demande.statut = 'valide'
        if code_ussd:
            demande.code_ussd = code_ussd
        demande.save()

        return Response({"message": "Demande validée avec succès."}, status=status.HTTP_200_OK)

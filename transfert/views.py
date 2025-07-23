from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
from .models import Utilisateur, DemandeTransfert
from rest_framework.generics import ListAPIView
from rest_framework import serializers


# 📦 API d'inscription
class InscriptionView(APIView):
    def post(self, request):
        """
        Reçoit :
        - nom_complet
        - numero
        - pin
        - confirmation_pin

        Retourne :
        - Succès ou erreur avec message
        """

        data = request.data
        nom_complet = data.get('nom_complet')
        numero = data.get('numero')
        pin = data.get('pin')
        confirmation_pin = data.get('confirmation_pin')

        # ✅ Validation des champs
        if not nom_complet or not numero or not pin or not confirmation_pin:
            return Response({"error": "Tous les champs sont requis."}, status=status.HTTP_400_BAD_REQUEST)

        if len(pin) != 4 or not pin.isdigit():
            return Response({"error": "Le code PIN doit contenir exactement 4 chiffres."}, status=status.HTTP_400_BAD_REQUEST)

        if pin != confirmation_pin:
            return Response({"error": "Les deux codes PIN ne correspondent pas."}, status=status.HTTP_400_BAD_REQUEST)

        # ❌ Vérifier si ce numéro est déjà utilisé
        if Utilisateur.objects.filter(numero=numero).exists():
            return Response({"error": "Ce numéro est déjà inscrit."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Créer l’utilisateur avec PIN hashé
        utilisateur = Utilisateur.objects.create(
            nom_complet=nom_complet,
            numero=numero,
            code_pin=make_password(pin)
        )

        return Response({"message": "Inscription réussie !", "id": utilisateur.id}, status=status.HTTP_201_CREATED)


# 🔐 API de connexion
class ConnexionView(APIView):
    def post(self, request):
        """
        Reçoit :
        - numero
        - pin

        Retourne :
        - Succès ou erreur
        """

        data = request.data
        numero = data.get('numero')
        pin = data.get('pin')

        if not numero or not pin:
            return Response({"error": "Numéro et PIN requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            utilisateur = Utilisateur.objects.get(numero=numero)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)

        # Vérification du PIN
        if not check_password(pin, utilisateur.code_pin):
            return Response({"error": "Code PIN incorrect."}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"message": "Connexion réussie.", "id": utilisateur.id, "nom": utilisateur.nom_complet}, status=status.HTTP_200_OK)


# 🔓 API de déverrouillage
class DeverrouillageView(APIView):
    def post(self, request):
        """
        Reçoit :
        - id_utilisateur
        - pin

        Retourne :
        - Succès ou erreur
        """
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
        """
        Reçoit :
        - id_utilisateur
        - numero_destinataire
        - reseau
        - montant
        - numero_wave
        - methode_paiement

        Retourne :
        - Succès ou erreur avec ID de la demande
        """
        data = request.data

        # 🎯 Récupération des champs envoyés
        id_utilisateur = data.get('id_utilisateur')
        numero_destinataire = data.get('numero_destinataire')
        reseau = data.get('reseau')
        montant = data.get('montant')
        numero_wave = data.get('numero_wave')
        methode_paiement = data.get('methode_paiement')

        # ✅ Vérification des champs
        if not all([id_utilisateur, numero_destinataire, reseau, montant, numero_wave, methode_paiement]):
            return Response({"error": "Tous les champs sont obligatoires."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            utilisateur = Utilisateur.objects.get(id=id_utilisateur)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Création de la demande
        demande = DemandeTransfert.objects.create(
            utilisateur=utilisateur,
            numero_destinataire=numero_destinataire,
            reseau=reseau.lower(),
            montant=montant,
            numero_wave=numero_wave,
            methode_paiement=methode_paiement.lower()
        )

        return Response({"message": "Demande enregistrée avec succès.", "id_demande": demande.id}, status=status.HTTP_201_CREATED)


# 🎯 Sérialiseur pour formater les données envoyées au frontend (ex : Flutter admin)
class DemandeTransfertSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeTransfert
        fields = '__all__'


# 📡 Vue pour afficher toutes les demandes en attente à l'app admin (Otransous)
class DemandesEnAttenteView(ListAPIView):
    """
    Cette vue est utilisée par l'application administrateur Flutter
    Elle retourne une liste de toutes les demandes avec statut="en_attente"
    """
    queryset = DemandeTransfert.objects.filter(statut='en_attente').order_by('-date_creation')
    serializer_class = DemandeTransfertSerializer



# ✅ Vue pour valider une demande (appelée par l'app admin)
class ValidationDemandeView(APIView):
    def post(self, request):
        """
        Reçoit :
        - id_demande
        - code_ussd (optionnel)

        Retourne :
        - Message de succès ou erreur
        """
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

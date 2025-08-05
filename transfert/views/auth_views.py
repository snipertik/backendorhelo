from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
from ..models import Utilisateur

# 📦 API d'inscription
class InscriptionView(APIView):
    def post(self, request):
        data = request.data
        nom_complet = data.get('nom_complet')
        numero = data.get('numero')
        pin = data.get('pin')
        confirmation_pin = data.get('confirmation_pin')

        if not nom_complet or not numero or not pin or not confirmation_pin:
            return Response({"error": "Tous les champs sont requis."}, status=status.HTTP_400_BAD_REQUEST)

        if not pin.isdigit():
            return Response({"error": "Le code PIN doit contenir uniquement des chiffres."}, status=400)

        if len(pin) != 4:
            return Response({"error": "Le code PIN doit contenir exactement 4 chiffres."}, status=status.HTTP_400_BAD_REQUEST)

        if pin != confirmation_pin:
            return Response({"error": "Les deux codes PIN ne correspondent pas."}, status=status.HTTP_400_BAD_REQUEST)

        if Utilisateur.objects.filter(numero=numero).exists():
            return Response({"error": "Ce numéro est déjà inscrit."}, status=status.HTTP_400_BAD_REQUEST)

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

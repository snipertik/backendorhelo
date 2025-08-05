from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Utilisateur, DemandeTransfert
from .fcm_utils import envoyer_notification_fcm

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

        envoyer_notification_fcm(
            titre="Nouvelle demande",
            corps=f"{reseau.upper()} - {montant} F pour {numero_destinataire}"
        )

        return Response({"message": "Demande enregistrée avec succès.", "id_demande": demande.id}, status=status.HTTP_201_CREATED)

# ✅ Validation demande
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

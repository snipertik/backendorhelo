import os
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from django.conf import settings
from ..models import DemandeTransfert
from ..serializers import DemandeTransfertSerializer

TOKEN_FILE_PATH = os.path.join(settings.BASE_DIR, "token_admin.txt")

# 📌 Enregistrement du token admin
class EnregistrerTokenAdminView(APIView):
    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token manquant"}, status=400)

        with open(TOKEN_FILE_PATH, "w") as f:
            f.write(token.strip())

        return Response({"message": "Token enregistré avec succès"})

# 📡 Liste demandes en attente
class DemandesEnAttenteView(ListAPIView):
    queryset = DemandeTransfert.objects.filter(statut='en_attente').order_by('-date_creation')
    serializer_class = DemandeTransfertSerializer

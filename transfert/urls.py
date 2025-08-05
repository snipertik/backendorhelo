from django.urls import path
from .views import InscriptionView, ConnexionView, DeverrouillageView, SoumissionTransfertView, DemandesEnAttenteView, ValidationDemandeView

urlpatterns = [
    path('inscription/', InscriptionView.as_view(), name='inscription'),
    path('connexion/', ConnexionView.as_view(), name='connexion'),
    path('deverrouillage/', DeverrouillageView.as_view(), name='deverrouillage'),
    path('transfert/', SoumissionTransfertView.as_view(), name='soumission_transfert'),  # << 🔥 API de soumission
    path('demandes/', DemandesEnAttenteView.as_view()),  # 👈 pour l’app admin
    path('demandes_en_attente/', DemandesEnAttenteView.as_view(), name='demandes_en_attente'),
    path('valider/', ValidationDemandeView.as_view()),  # ✅ nouvelle route pour valider
    path('enregistrer_token_admin/', EnregistrerTokenAdminView.as_view(), name='enregistrer_token_admin'),

]


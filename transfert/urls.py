from django.urls import path

# 📌 Importation depuis les fichiers séparés
from .views.auth_views import (
    InscriptionView,
    ConnexionView,
    DeverrouillageView
)

from .views.transfert_views import (
    SoumissionTransfertView,
    ValidationDemandeView
)

from .views.admin_views import (
    EnregistrerTokenAdminView,
    DemandesEnAttenteView
)

urlpatterns = [
    # 🔹 Authentification
    path('inscription/', InscriptionView.as_view(), name='inscription'),
    path('connexion/', ConnexionView.as_view(), name='connexion'),
    path('deverrouillage/', DeverrouillageView.as_view(), name='deverrouillage'),

    # 🔹 Transfert
    path('transfert/', SoumissionTransfertView.as_view(), name='soumission_transfert'),
    path('valider/', ValidationDemandeView.as_view(), name='valider_demande'),

    # 🔹 Admin
    path('demandes/', DemandesEnAttenteView.as_view(), name='demandes'),  
    path('demandes_en_attente/', DemandesEnAttenteView.as_view(), name='demandes_en_attente'),
    path('enregistrer_token_admin/', EnregistrerTokenAdminView.as_view(), name='enregistrer_token_admin'),
]

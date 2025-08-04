from django.db import models
from django.utils import timezone

class Utilisateur(models.Model):
    nom_complet = models.CharField(max_length=100)
    numero = models.CharField(max_length=20, unique=True)
    code_pin = models.CharField(max_length=6)  # 4 à 6 chiffres
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom_complet} ({self.numero})"




class DemandeTransfert(models.Model):
    # 🧍 Identifiant de l'utilisateur qui a soumis la demande
    utilisateur = models.ForeignKey("Utilisateur", on_delete=models.CASCADE)

    # ☎️ Numéro à recharger (celui du bénéficiaire)
    numero_destinataire = models.CharField(max_length=20)

    # 🌐 Réseau choisi (Orange, MTN, Moov)
    reseau = models.CharField(max_length=10)

    # 💰 Montant à transférer
    montant = models.DecimalField(max_digits=10, decimal_places=2)

    # 📱 Numéro Wave utilisé pour payer
    numero_wave = models.CharField(max_length=20)

    statut = models.CharField(max_length=50, default='en_attente')


    # 💳 Méthode de paiement choisie (Wave ou Points)
    methode_paiement = models.CharField(max_length=10, choices=[
        ('wave', 'Wave'),
        ('points', 'Points'),
    ])

    # ⏳ Statut de la demande
    statut = models.CharField(max_length=20, default='en_attente', choices=[
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('echec', 'Échec'),
    ])

    # 🕒 Date de création (auto-ajoutée)
    date_creation = models.DateTimeField(default=timezone.now)

    # 📞 Code USSD généré et exécuté côté admin
    code_ussd = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Transfert {self.id} - {self.numero_destinataire} ({self.statut})"
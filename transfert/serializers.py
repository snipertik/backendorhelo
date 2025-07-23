# serializers.py

from rest_framework import serializers
from .models import Utilisateur

# Serializer pour gérer l'inscription d'un utilisateur
class InscriptionSerializer(serializers.ModelSerializer):
    confirmation_pin = serializers.CharField(write_only=True)  # Champ utilisé uniquement pour valider le code PIN

    class Meta:
        model = Utilisateur
        fields = ['nom_complet', 'numero', 'code_pin', 'confirmation_pin']

    def validate(self, data):
        # Vérifie que le code PIN et sa confirmation sont identiques
        if data['code_pin'] != data['confirmation_pin']:
            raise serializers.ValidationError("Les deux codes PIN ne correspondent pas.")
        return data

    def create(self, validated_data):
        # Retire confirmation_pin du dictionnaire car il ne fait pas partie du modèle
        validated_data.pop('confirmation_pin')
        # noinspection PyUnresolvedReferences
        return Utilisateur.objects.create(**validated_data)


# Serializer pour la connexion d'un utilisateur
class ConnexionSerializer(serializers.Serializer):
    numero = serializers.CharField()
    code_pin = serializers.CharField()

    def validate(self, data):
        try:
            # noinspection PyUnresolvedReferences
            utilisateur = Utilisateur.objects.get(numero=data['numero'])
        # noinspection PyUnresolvedReferences
        except Utilisateur.DoesNotExist:
            raise serializers.ValidationError("Aucun compte trouvé avec ce numéro.")

        if utilisateur.code_pin != data['code_pin']:
            raise serializers.ValidationError("Code PIN incorrect.")

        return data


# Serializer pour le déverrouillage
class DeverrouillageSerializer(serializers.Serializer):
    code_pin = serializers.CharField()

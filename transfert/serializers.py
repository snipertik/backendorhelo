from rest_framework import serializers
from .models import Utilisateur, DemandeTransfert

# 🔹 Serializer pour gérer l'inscription d'un utilisateur
class InscriptionSerializer(serializers.ModelSerializer):
    confirmation_pin = serializers.CharField(write_only=True)

    class Meta:
        model = Utilisateur
        fields = ['nom_complet', 'numero', 'code_pin', 'confirmation_pin']

    def validate(self, data):
        if data['code_pin'] != data['confirmation_pin']:
            raise serializers.ValidationError("Les deux codes PIN ne correspondent pas.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirmation_pin')
        return Utilisateur.objects.create(**validated_data)


# 🔹 Serializer pour la connexion d'un utilisateur
class ConnexionSerializer(serializers.Serializer):
    numero = serializers.CharField()
    code_pin = serializers.CharField()

    def validate(self, data):
        try:
            utilisateur = Utilisateur.objects.get(numero=data['numero'])
        except Utilisateur.DoesNotExist:
            raise serializers.ValidationError("Aucun compte trouvé avec ce numéro.")

        if utilisateur.code_pin != data['code_pin']:
            raise serializers.ValidationError("Code PIN incorrect.")

        return data


# 🔹 Serializer pour le déverrouillage
class DeverrouillageSerializer(serializers.Serializer):
    code_pin = serializers.CharField()


# 🔹 Serializer pour les demandes de transfert (utilisé par l'admin)
class DemandeTransfertSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandeTransfert
        fields = '__all__'

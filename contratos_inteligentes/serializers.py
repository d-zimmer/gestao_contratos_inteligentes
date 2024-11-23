from rest_framework import serializers
from .models import RentalContract

class RentalContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalContract
        fields = "__all__"

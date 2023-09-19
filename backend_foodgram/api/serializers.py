from rest_framework import serializers
from rest_framework.relations import SlugRelatedField


from .models import Ingridient


class IngridientSerializer(serializers.ModelSerializer):
    

    class Meta:
        fields = 'id', 'ingridient', 'measurement_unit'
        model = Ingridient
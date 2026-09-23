import math
from rest_framework import serializers


class NearbyQuery(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lng = serializers.FloatField(min_value=-180, max_value=180)
    radius = serializers.FloatField(min_value=1, max_value=200, default=10)

    def validate(self, attrs):
        if not all(math.isfinite(value) for value in attrs.values()):
            raise serializers.ValidationError("Informe uma localização válida.")
        return attrs


def distance_km(lat, lng, target_lat, target_lng):
    lat, lng, target_lat, target_lng = map(math.radians, (lat, lng, float(target_lat), float(target_lng)))
    a = math.sin((target_lat - lat) / 2) ** 2 + math.cos(lat) * math.cos(target_lat) * math.sin((target_lng - lng) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(min(1, a)))

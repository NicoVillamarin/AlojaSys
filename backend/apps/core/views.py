from rest_framework import viewsets
from .models import Hotel
from .serializers import HotelSerializer

class HotelViewSet(viewsets.ModelViewSet):
    serializer_class = HotelSerializer
    def get_queryset(self):
        qs = Hotel.objects.select_related("city", "city__state", "city__state__country").order_by("name")
        city = self.request.query_params.get("city")
        state = self.request.query_params.get("state")
        country = self.request.query_params.get("country")
        if city and city.isdigit():
            qs = qs.filter(city_id=city)
        if state and state.isdigit():
            qs = qs.filter(city__state_id=state)
        if country:
            qs = qs.filter(city__state__country__code2=country.upper())
        return qs
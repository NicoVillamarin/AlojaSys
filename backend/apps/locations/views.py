from rest_framework import viewsets, filters
from .models import Country, State, City
from .serializers import CountrySerializer, StateSerializer, CitySerializer

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all().order_by("name")
    serializer_class = CountrySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code2", "code3"]
    ordering_fields = ["name", "code2", "created_at"]

class StateViewSet(viewsets.ModelViewSet):
    serializer_class = StateSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code", "country__name", "country__code2"]
    ordering_fields = ["name", "created_at"]
    def get_queryset(self):
        qs = State.objects.select_related("country").order_by("name")
        country = self.request.query_params.get("country")
        if country:
            if country.isdigit():
                qs = qs.filter(country_id=country)
            else:
                qs = qs.filter(country__code2=country.upper())
        return qs

class CityViewSet(viewsets.ModelViewSet):
    serializer_class = CitySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "state__name", "state__country__name"]
    ordering_fields = ["name", "created_at"]
    def get_queryset(self):
        qs = City.objects.select_related("state", "state__country").order_by("name")
        state = self.request.query_params.get("state")
        if state and state.isdigit():
            qs = qs.filter(state_id=state)
        return qs
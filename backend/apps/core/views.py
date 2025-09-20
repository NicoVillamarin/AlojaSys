from rest_framework import viewsets, filters
from .models import Hotel
from .serializers import HotelSerializer

class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all().order_by("name")
    serializer_class = HotelSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "city", "country", "legal_name"]
    ordering_fields = ["name", "city", "country", "created_at"]
from rest_framework import viewsets
from .models import Enterprise
from .serializers import EnterpriseSerializer


class EnterpriseViewSet(viewsets.ModelViewSet):
    serializer_class = EnterpriseSerializer

    def get_queryset(self):
        qs = Enterprise.objects.select_related("city", "city__state", "city__state__country").order_by("name")
        country = self.request.query_params.get("country")
        if country:
            qs = qs.filter(city__state__country__code2=country.upper())
        return qs



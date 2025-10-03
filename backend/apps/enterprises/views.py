from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import IntegrityError
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

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except IntegrityError as e:
            msg = str(e)
            if 'unique' in msg.lower() and 'name' in msg.lower():
                return Response({'name': ['Ya existe una empresa con ese nombre.']}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'detail': 'Error al crear la empresa. Verifica los datos.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Error al crear la empresa: {e}'}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except IntegrityError as e:
            msg = str(e)
            if 'unique' in msg.lower() and 'name' in msg.lower():
                return Response({'name': ['Ya existe una empresa con ese nombre.']}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'detail': 'Error al actualizar la empresa. Verifica los datos.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Error al actualizar la empresa: {e}'}, status=status.HTTP_400_BAD_REQUEST)



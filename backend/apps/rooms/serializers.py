from rest_framework import serializers
from .models import Room, RoomType
from django.utils import timezone
from apps.reservations.models import ReservationStatus
from apps.housekeeping.feature import is_housekeeping_enabled_for_hotel
from apps.core.models import Currency
from django.db.utils import OperationalError, ProgrammingError


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = [
            "id",
            "code",
            "name",
            "alias",
            "description",
            "sort_order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

class RoomSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source="hotel.name", read_only=True)
    base_currency_code = serializers.CharField(source="base_currency.code", read_only=True)
    base_currency_name = serializers.CharField(source="base_currency.name", read_only=True)
    secondary_currency_code = serializers.CharField(source="secondary_currency.code", read_only=True)
    secondary_currency_name = serializers.CharField(source="secondary_currency.name", read_only=True)
    current_reservation = serializers.SerializerMethodField()
    current_guests = serializers.SerializerMethodField()
    future_reservations = serializers.SerializerMethodField()
    room_type_name = serializers.SerializerMethodField()
    room_type_alias = serializers.SerializerMethodField()
    primary_image_url = serializers.SerializerMethodField()
    images_urls = serializers.SerializerMethodField()
    # Campos write-only para recibir imágenes en base64
    primary_image_base64 = serializers.CharField(write_only=True, required=False, allow_blank=True)
    primary_image_filename = serializers.CharField(write_only=True, required=False, allow_blank=True)
    images_base64 = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        write_only=True,
        required=False
    )
    images_to_delete = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    def validate_amenities_quantities(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("amenities_quantities debe ser un objeto (dict).")
        cleaned = {}
        for k, v in value.items():
            code = str(k).strip()
            if not code:
                continue
            try:
                iv = int(v)
            except Exception:
                raise serializers.ValidationError(f"Cantidad inválida para '{code}'.")
            if iv < 1:
                raise serializers.ValidationError(f"La cantidad de '{code}' debe ser >= 1.")
            cleaned[code] = iv
        return cleaned

    class Meta:
        model = Room
        fields = [
            "id",
            "hotel", 
            "hotel_name", 
            "name",
            "number", 
            "floor",
            "room_type", 
            "room_type_name",
            "room_type_alias",
            "capacity", 
            "max_capacity", 
            "extra_guest_fee", 
            "base_price", 
            "base_currency",
            "base_currency_code",
            "base_currency_name",
            "secondary_price",
            "secondary_currency",
            "secondary_currency_code",
            "secondary_currency_name",
            "status",
            "cleaning_status",
            "is_active", 
            "description", 
            "amenities",
            "amenities_quantities",
            "primary_image",
            "primary_image_url",
            "images",
            "images_urls",
            "primary_image_base64",
            "primary_image_filename",
            "images_base64",
            "images_to_delete",
            "created_at", 
            "updated_at",
            "current_reservation", 
            "current_guests",
            "future_reservations",
        ]
        
        read_only_fields = [
            "id", 
            "created_at", 
            "updated_at", 
            "current_reservation", 
            "current_guests",
            "future_reservations",
            "room_type_name",
            "room_type_alias",
            "primary_image_url",
            "images_urls"
        ]

    def get_room_type_name(self, obj):
        if not getattr(obj, "room_type", None):
            return None
        rt = RoomType.objects.only("name").filter(code=obj.room_type).first()
        return rt.name if rt else obj.room_type

    def get_room_type_alias(self, obj):
        if not getattr(obj, "room_type", None):
            return None
        try:
            rt = RoomType.objects.only("alias").filter(code=obj.room_type).first()
        except (ProgrammingError, OperationalError):
            # DB aún no migrada (columna alias inexistente) u otro problema de esquema
            return None
        return (rt.alias or None) if rt else None

    def validate_room_type(self, value):
        if not value:
            raise serializers.ValidationError("room_type es obligatorio.")
        if not RoomType.objects.filter(code=value, is_active=True).exists():
            raise serializers.ValidationError(f"Tipo de habitación inválido: '{value}'.")
        return value

    def get_future_reservations(self, obj):
        today = timezone.localdate()
        # Solo incluir reservas que NO están en current_reservation
        # (es decir, que no están activas hoy)
        # Excluir reservas canceladas, no-show y check-out
        excluded_statuses = [
            ReservationStatus.CANCELLED,
            ReservationStatus.NO_SHOW,
            ReservationStatus.CHECK_OUT,
        ]
        qs = (obj.reservations
              .filter(check_out__gt=today, check_in__gt=today)
              .exclude(status__in=excluded_statuses)
              .order_by("check_in")
              .values("id", "status", "guests_data", "check_in", "check_out")
        )
        # Procesar los resultados para extraer el nombre del huésped principal
        reservations = []
        for res in qs:
            guest_name = ""
            if res.get('guests_data') and isinstance(res['guests_data'], list):
                # Buscar el huésped principal
                primary_guest = next((guest for guest in res['guests_data'] if guest.get('is_primary', False)), None)
                if not primary_guest and res['guests_data']:
                    # Si no hay huésped principal marcado, tomar el primero
                    primary_guest = res['guests_data'][0]
                guest_name = primary_guest.get('name', '') if primary_guest else ''
            
            reservations.append({
                "id": res['id'],
                "status": res['status'],
                "guest_name": guest_name,
                "check_in": res['check_in'],
                "check_out": res['check_out']
            })
        return reservations

    def get_current_reservation(self, obj):
        today = timezone.localdate()
        # Consideramos ocupación si la reserva está confirmada o en check-in
        # Y que esté dentro del rango de fechas de la reserva
        active_status = ["confirmed", "check_in"]
        res = (obj.reservations
               .filter(check_in__lte=today, check_out__gt=today, status__in=active_status)
               .order_by("-status")
               .values("id", "status", "guests_data", "check_in", "check_out")
               .first())
        
        # Si no hay reserva activa en el rango de fechas, verificar si hay una reserva en CHECK_IN
        # que aún no haya hecho checkout manual (incluso si ya pasó la fecha de checkout)
        if not res:
            res = (obj.reservations
                   .filter(status="check_in", check_in__lte=today)
                   .order_by("-check_in")
                   .values("id", "status", "guests_data", "check_in", "check_out")
                   .first())
        
        if res:
            guest_name = ""
            if res.get('guests_data') and isinstance(res['guests_data'], list):
                # Buscar el huésped principal
                primary_guest = next((guest for guest in res['guests_data'] if guest.get('is_primary', False)), None)
                if not primary_guest and res['guests_data']:
                    # Si no hay huésped principal marcado, tomar el primero
                    primary_guest = res['guests_data'][0]
                guest_name = primary_guest.get('name', '') if primary_guest else ''
            
            return {
                "id": res['id'],
                "status": res['status'],
                "guest_name": guest_name,
                "check_in": res['check_in'],
                "check_out": res['check_out']
            }
        return None

    def get_current_guests(self, obj):
        today = timezone.localdate()
        # Consideramos ocupación si la reserva está confirmada o en check-in
        active_status = ["confirmed", "check_in"]
        reservation = (obj.reservations
                      .filter(check_in__lte=today, check_out__gt=today, status__in=active_status)
                      .first())
        
        # Si no hay reserva activa en el rango de fechas, verificar si hay una reserva en CHECK_IN
        # que aún no haya hecho checkout manual (incluso si ya pasó la fecha de checkout)
        if not reservation:
            reservation = (obj.reservations
                          .filter(status="check_in", check_in__lte=today)
                          .order_by("-check_in")
                          .first())
        
        if reservation:
            # Retornar el número real de huéspedes de la reserva
            return reservation.guests
        return 0

    def get_primary_image_url(self, obj):
        """Obtiene la URL completa de la imagen principal"""
        if obj.primary_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.primary_image.url)
            return obj.primary_image.url
        return None

    def get_images_urls(self, obj):
        """Obtiene las URLs completas de las imágenes adicionales"""
        if not obj.images or not isinstance(obj.images, list):
            return []
        
        request = self.context.get('request')
        urls = []
        for image_url in obj.images:
            if image_url:
                if request:
                    # Si es una URL relativa, construir la URL absoluta
                    if image_url.startswith('/'):
                        urls.append(request.build_absolute_uri(image_url))
                    else:
                        urls.append(image_url)
                else:
                    urls.append(image_url)
        return urls

    def validate(self, attrs):
        """
        Regla de negocio:
        - Si housekeeping está ACTIVADO (por plan), el cleaning_status NO se gestiona
          manualmente desde gestión de habitaciones para evitar inconsistencias.
        - Si housekeeping está DESACTIVADO, sí se permite editar cleaning_status.
        """
        # Default defensivo: si no mandan base_currency, usar ARS (solo en create)
        if getattr(self, "instance", None) is None and not attrs.get("base_currency"):
            ars, _ = Currency.objects.get_or_create(code="ARS", defaults={"name": "ARS"})
            attrs["base_currency"] = ars

        if "cleaning_status" in attrs:
            hotel = None
            # En updates, podemos tomar hotel desde la instancia (lo normal en gestión de rooms)
            if getattr(self, "instance", None) is not None:
                hotel = getattr(self.instance, "hotel", None)
            else:
                # En create, intentar resolver por hotel id (si vino)
                raw_hotel = attrs.get("hotel") or (self.initial_data.get("hotel") if isinstance(self.initial_data, dict) else None)
                hotel_id = getattr(raw_hotel, "id", None) or raw_hotel
                try:
                    from apps.core.models import Hotel
                    if hotel_id:
                        hotel = Hotel.objects.select_related("enterprise").filter(id=hotel_id).first()
                except Exception:
                    hotel = None

            if hotel and is_housekeeping_enabled_for_hotel(hotel):
                raise serializers.ValidationError(
                    {"cleaning_status": "No se puede modificar manualmente cuando housekeeping está habilitado."}
                )

        return super().validate(attrs)

    def create(self, validated_data):
        """Crear habitación con imágenes desde base64"""
        primary_image_base64 = validated_data.pop('primary_image_base64', None)
        primary_image_filename = validated_data.pop('primary_image_filename', None)
        images_base64 = validated_data.pop('images_base64', [])
        images_to_delete = validated_data.pop('images_to_delete', [])
        
        room = super().create(validated_data)
        
        # Guardar imagen principal
        if primary_image_base64 and primary_image_filename:
            self._save_image_from_base64(room, primary_image_base64, primary_image_filename, is_primary=True)
        
        # Guardar imágenes adicionales
        if images_base64:
            saved_urls = []
            for img_data in images_base64:
                if img_data.get('base64') and img_data.get('filename'):
                    saved_url = self._save_image_from_base64(
                        room, 
                        img_data['base64'], 
                        img_data['filename'], 
                        is_primary=False
                    )
                    if saved_url:
                        saved_urls.append(saved_url)
            
            # Actualizar el campo images con las nuevas URLs
            room.images = saved_urls
            room.save(update_fields=['images'])
        
        return room

    def update(self, instance, validated_data):
        """Actualizar habitación con imágenes desde base64"""
        primary_image_base64 = validated_data.pop('primary_image_base64', None)
        primary_image_filename = validated_data.pop('primary_image_filename', None)
        images_base64 = validated_data.pop('images_base64', [])
        images_to_delete = validated_data.pop('images_to_delete', [])
        
        room = super().update(instance, validated_data)
        
        # Guardar imagen principal si se proporcionó una nueva
        if primary_image_base64 and primary_image_filename:
            self._save_image_from_base64(room, primary_image_base64, primary_image_filename, is_primary=True)
        
        # Eliminar imágenes marcadas para eliminación
        if images_to_delete and isinstance(room.images, list):
            request = self.context.get('request')
            current_images = room.images.copy()
            
            for idx in sorted(images_to_delete, reverse=True):
                if 0 <= idx < len(current_images):
                    current_images.pop(idx)
            
            room.images = current_images
            room.save(update_fields=['images'])
        
        # Guardar nuevas imágenes adicionales
        if images_base64:
            saved_urls = room.images.copy() if isinstance(room.images, list) else []
            
            for img_data in images_base64:
                if img_data.get('base64') and img_data.get('filename'):
                    saved_url = self._save_image_from_base64(
                        room, 
                        img_data['base64'], 
                        img_data['filename'], 
                        is_primary=False
                    )
                    if saved_url:
                        saved_urls.append(saved_url)
            
            room.images = saved_urls
            room.save(update_fields=['images'])
        
        return room

    def _save_image_from_base64(self, room, image_base64, image_filename, is_primary=False):
        """Guarda una imagen desde base64"""
        try:
            import base64
            from django.core.files.base import ContentFile
            from django.core.files.storage import default_storage
            import os
            import uuid
            
            # Decodificar base64
            if ',' in image_base64:
                header, data = image_base64.split(',', 1)
            else:
                data = image_base64
            
            file_data = base64.b64decode(data)
            
            # Crear archivo
            file_obj = ContentFile(file_data, name=image_filename)
            
            if is_primary:
                # Guardar como imagen principal
                room.primary_image.save(image_filename, file_obj, save=True)
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(room.primary_image.url)
                return room.primary_image.url
            else:
                # Guardar como imagen adicional usando el mismo patrón que primary_image
                # Generar nombre único para evitar conflictos
                name, ext = os.path.splitext(image_filename)
                unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
                
                # Usar el mismo upload_to que primary_image
                from datetime import date
                today = date.today()
                upload_path = f"rooms/images/{today.year}/{today.month:02d}/{today.day:02d}/{unique_filename}"
                
                saved_path = default_storage.save(upload_path, file_obj)
                request = self.context.get('request')
                
                # Construir URL relativa (sin dominio) para guardar en JSONField
                # El frontend recibirá la URL completa desde get_images_urls
                url_path = default_storage.url(saved_path)
                if url_path.startswith('/'):
                    # Es una URL relativa, guardarla así
                    return url_path
                else:
                    # Es una URL absoluta, extraer la parte relativa si es posible
                    return url_path
                
        except Exception as e:
            print(f"Error guardando imagen desde base64: {e}")
            import traceback
            traceback.print_exc()
            return None
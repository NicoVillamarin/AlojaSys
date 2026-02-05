from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import Hotel
from apps.housekeeping.models import TaskTemplate, Checklist, ChecklistItem, TaskType


class Command(BaseCommand):
    help = "Agrega datos de ejemplo: plantillas de tareas y checklists"

    def add_arguments(self, parser):
        parser.add_argument(
            "hotel_id",
            type=int,
            nargs="?",
            default=None,
            help="ID del hotel (si no se especifica, usa el primero disponible)"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        hotel_id = options.get("hotel_id")
        
        if hotel_id:
            try:
                hotel = Hotel.objects.get(pk=hotel_id)
            except Hotel.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Hotel {hotel_id} no existe"))
                return
        else:
            hotel = Hotel.objects.first()
            if not hotel:
                self.stdout.write(self.style.ERROR("No hay hoteles disponibles"))
                return
        
        self.stdout.write(self.style.SUCCESS(f"Agregando datos de ejemplo para: {hotel.name}"))

        # Plantillas de tareas de ejemplo
        templates_data = [
            # Suite - Tareas diarias
            {
                "room_type": "suite",
                "task_type": TaskType.DAILY,
                "name": "Cambio de sábanas",
                "description": "Cambiar sábanas y fundas de almohadas",
                "estimated_minutes": 15,
                "is_required": True,
                "order": 1,
            },
            {
                "room_type": "suite",
                "task_type": TaskType.DAILY,
                "name": "Reposición de minibar",
                "description": "Verificar y reponer productos del minibar",
                "estimated_minutes": 10,
                "is_required": True,
                "order": 2,
            },
            {
                "room_type": "suite",
                "task_type": TaskType.DAILY,
                "name": "Limpieza de baño completo",
                "description": "Limpieza profunda de baño, sanitarios y espejos",
                "estimated_minutes": 20,
                "is_required": True,
                "order": 3,
            },
            {
                "room_type": "suite",
                "task_type": TaskType.DAILY,
                "name": "Aspirado y limpieza de pisos",
                "description": "Aspirar alfombras y limpiar pisos",
                "estimated_minutes": 15,
                "is_required": True,
                "order": 4,
            },
            # Suite - Checkout
            {
                "room_type": "suite",
                "task_type": TaskType.CHECKOUT,
                "name": "Limpieza profunda completa",
                "description": "Limpieza exhaustiva de toda la suite",
                "estimated_minutes": 45,
                "is_required": True,
                "order": 1,
            },
            {
                "room_type": "suite",
                "task_type": TaskType.CHECKOUT,
                "name": "Revisión de inventario",
                "description": "Verificar que todos los elementos estén presentes",
                "estimated_minutes": 10,
                "is_required": True,
                "order": 2,
            },
            # Double - Tareas diarias
            {
                "room_type": "double",
                "task_type": TaskType.DAILY,
                "name": "Cambio de sábanas",
                "description": "Cambiar sábanas y fundas",
                "estimated_minutes": 12,
                "is_required": True,
                "order": 1,
            },
            {
                "room_type": "double",
                "task_type": TaskType.DAILY,
                "name": "Limpieza de baño",
                "description": "Limpieza básica de baño",
                "estimated_minutes": 15,
                "is_required": True,
                "order": 2,
            },
            {
                "room_type": "double",
                "task_type": TaskType.DAILY,
                "name": "Aspirado",
                "description": "Aspirar habitación",
                "estimated_minutes": 10,
                "is_required": True,
                "order": 3,
            },
            # Single - Tareas diarias
            {
                "room_type": "single",
                "task_type": TaskType.DAILY,
                "name": "Cambio de sábanas",
                "description": "Cambiar sábanas",
                "estimated_minutes": 10,
                "is_required": True,
                "order": 1,
            },
            {
                "room_type": "single",
                "task_type": TaskType.DAILY,
                "name": "Limpieza de baño",
                "description": "Limpieza básica",
                "estimated_minutes": 12,
                "is_required": True,
                "order": 2,
            },
        ]

        created_templates = 0
        for template_data in templates_data:
            template, created = TaskTemplate.objects.get_or_create(
                hotel=hotel,
                room_type=template_data["room_type"],
                task_type=template_data["task_type"],
                name=template_data["name"],
                defaults=template_data
            )
            if created:
                created_templates += 1
                room_type_display = template.room_type
                try:
                    from apps.rooms.models import RoomType as RoomTypeModel
                    rt = RoomTypeModel.objects.only("name").filter(code=template.room_type).first()
                    if rt:
                        room_type_display = rt.name
                except Exception:
                    pass
                self.stdout.write(f"  ✓ Plantilla creada: {template.name} ({room_type_display})")

        self.stdout.write(self.style.SUCCESS(f"\n✓ {created_templates} plantillas de tareas creadas"))

        # Checklists de ejemplo
        checklists_data = [
            {
                "name": "Checklist de Limpieza Estándar",
                "description": "Checklist general para limpieza diaria",
                "room_type": None,
                "task_type": TaskType.DAILY,
                "is_default": True,
                "items": [
                    {"name": "Cambiar sábanas y fundas", "description": "Verificar y cambiar si es necesario", "order": 1, "is_required": True},
                    {"name": "Limpiar baño completo", "description": "Sanitarios, ducha, espejos y pisos", "order": 2, "is_required": True},
                    {"name": "Aspirar habitación", "description": "Incluir debajo de la cama", "order": 3, "is_required": True},
                    {"name": "Limpiar superficies", "description": "Mesas, escritorio, TV", "order": 4, "is_required": True},
                    {"name": "Reponer amenities", "description": "Jabón, shampoo, toallas", "order": 5, "is_required": True},
                    {"name": "Verificar funcionamiento", "description": "Luz, TV, aire acondicionado", "order": 6, "is_required": False},
                ]
            },
            {
                "name": "Checklist de Checkout - Suite",
                "description": "Checklist específico para limpieza de suites en checkout",
                "room_type": "suite",
                "task_type": TaskType.CHECKOUT,
                "is_default": False,
                "items": [
                    {"name": "Limpieza profunda de baño", "description": "Incluir jacuzzi si aplica", "order": 1, "is_required": True},
                    {"name": "Cambio completo de ropa de cama", "description": "Sábanas, fundas, colchas", "order": 2, "is_required": True},
                    {"name": "Reposición completa de minibar", "description": "Verificar inventario y reponer", "order": 3, "is_required": True},
                    {"name": "Limpieza de áreas comunes", "description": "Sala, comedor, cocina", "order": 4, "is_required": True},
                    {"name": "Aspirado profundo", "description": "Incluir sofás y cortinas", "order": 5, "is_required": True},
                    {"name": "Revisión de inventario completo", "description": "Verificar todos los elementos", "order": 6, "is_required": True},
                    {"name": "Verificar electrodomésticos", "description": "Microondas, cafetera, TV", "order": 7, "is_required": False},
                ]
            },
            {
                "name": "Checklist de Checkout - Habitación Estándar",
                "description": "Checklist para habitaciones simples y dobles en checkout",
                "room_type": None,
                "task_type": TaskType.CHECKOUT,
                "is_default": False,
                "items": [
                    {"name": "Limpieza completa de baño", "description": "Sanitarios, ducha, espejos", "order": 1, "is_required": True},
                    {"name": "Cambio de toda la ropa de cama", "description": "Sábanas, fundas, mantas", "order": 2, "is_required": True},
                    {"name": "Aspirado completo", "description": "Incluir áreas debajo de muebles", "order": 3, "is_required": True},
                    {"name": "Limpieza de todas las superficies", "description": "Mesas, escritorio, estantes", "order": 4, "is_required": True},
                    {"name": "Reposición completa de amenities", "description": "Toallas, jabones, papel higiénico", "order": 5, "is_required": True},
                    {"name": "Verificar funcionamiento", "description": "Luz, TV, aire, WiFi", "order": 6, "is_required": False},
                ]
            },
        ]

        created_checklists = 0
        for checklist_data in checklists_data:
            items_data = checklist_data.pop("items")
            checklist, created = Checklist.objects.get_or_create(
                hotel=hotel,
                name=checklist_data["name"],
                defaults=checklist_data
            )
            if created:
                created_checklists += 1
                # Crear items del checklist
                for item_data in items_data:
                    ChecklistItem.objects.create(
                        checklist=checklist,
                        **item_data
                    )
                self.stdout.write(f"  ✓ Checklist creado: {checklist.name} ({len(items_data)} items)")

        self.stdout.write(self.style.SUCCESS(f"\n✓ {created_checklists} checklists creados"))
        self.stdout.write(self.style.SUCCESS(f"\n✅ Datos de ejemplo agregados exitosamente para {hotel.name}"))


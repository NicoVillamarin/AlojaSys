from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('housekeeping', '0008_housekeepingconfig_daily_for_all_rooms'),
    ]

    operations = [
        migrations.AddField(
            model_name='housekeepingconfig',
            name='use_checklists',
            field=models.BooleanField(
                default=True,
                help_text='Si está activo, las tareas usarán checklists detallados. Si está desactivado, solo se usará descripción general.'
            ),
        ),
    ]



from django.db import migrations


def seed(apps, schema_editor):
    apps.get_model('spaces', 'PromotionPackage').objects.create(
        name='Destaque por 7 dias', price='29.90', days=7,
        instructions='Solicite o destaque e aguarde as instruções de pagamento da administração nesta página. Não há cobrança ou pagamento de aluguel pelo site.',
    )


class Migration(migrations.Migration):
    dependencies = [('spaces', '0005_notificationdelivery_space_availability_checked_at_and_more')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]

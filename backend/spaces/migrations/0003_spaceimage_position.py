from django.db import migrations, models


def migrate_cover_images(apps, schema_editor):
    Space = apps.get_model("spaces", "Space")
    SpaceImage = apps.get_model("spaces", "SpaceImage")
    for space in Space.objects.exclude(cover_image="").exclude(cover_image__isnull=True).iterator():
        existing = list(SpaceImage.objects.filter(space_id=space.pk).order_by("id"))
        for index, image in enumerate(existing, start=1):
            image.position = index
            image.save(update_fields=["position"])
        SpaceImage.objects.create(space_id=space.pk, image=space.cover_image.name, position=0)
        space.cover_image = None
        space.save(update_fields=["cover_image"])


class Migration(migrations.Migration):
    dependencies = [("spaces", "0002_spaceimage")]
    operations = [
        migrations.AddField(
            model_name="spaceimage",
            name="position",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterModelOptions(name="spaceimage", options={"ordering": ["position", "id"]}),
        migrations.RunPython(migrate_cover_images, migrations.RunPython.noop),
    ]

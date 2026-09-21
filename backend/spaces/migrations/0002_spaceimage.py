from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("spaces", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="SpaceImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="spaces/%Y/%m/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("space", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="spaces.space")),
            ],
            options={"ordering": ["id"]},
        ),
    ]

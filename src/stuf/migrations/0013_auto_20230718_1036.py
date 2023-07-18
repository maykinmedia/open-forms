# Generated by Django 3.2.20 on 2023-07-18 08:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("soap", "0001_initial"),
        ("stuf", "0012_auto_20220905_2218"),
        # The following 2 migrations are the ones that replace the link from StufBGConfig/StufZDSConfig and the SoapService.
        # So they need to have been applied before we can move the SoapService
        ("stuf_bg", "0003_auto_20211001_1300"),
        ("stuf_zds", "0006_auto_20211001_1300"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name="SoapService",
                ),
                migrations.AlterField(
                    model_name="stufservice",
                    name="soap_service",
                    field=models.OneToOneField(
                        help_text="The soap service this stuf service uses",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stuf_service",
                        to="soap.soapservice",
                    ),
                ),
            ],
            database_operations=[
                migrations.AlterModelTable(
                    name="SoapService",
                    table="soap_soapservice",
                ),
            ],
        ),
    ]

# Generated by Django 5.0.1 on 2024-01-22 15:04

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("station", "0004_alter_facility_name"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ticket",
            options={"ordering": ["trip", "seat"]},
        ),
    ]
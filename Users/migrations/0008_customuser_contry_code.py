# Generated by Django 5.1 on 2024-08-28 22:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0007_alter_customuser_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='contry_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
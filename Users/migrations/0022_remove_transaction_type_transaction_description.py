# Generated by Django 5.1 on 2024-09-27 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0021_transaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='type',
        ),
        migrations.AddField(
            model_name='transaction',
            name='description',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
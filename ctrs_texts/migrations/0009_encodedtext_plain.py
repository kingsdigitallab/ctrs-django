# Generated by Django 2.2.10 on 2020-04-16 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ctrs_texts', '0008_abstractedtext_locus'),
    ]

    operations = [
        migrations.AddField(
            model_name='encodedtext',
            name='plain',
            field=models.TextField(blank=True, null=True),
        ),
    ]
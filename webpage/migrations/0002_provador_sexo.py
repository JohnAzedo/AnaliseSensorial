# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-10-18 20:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webpage', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='provador',
            name='sexo',
            field=models.CharField(choices=[('1', 'Masculino'), ('2', 'Feminino')], default='1', max_length=1),
        ),
    ]

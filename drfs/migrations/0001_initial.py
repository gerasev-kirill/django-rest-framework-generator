# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-28 13:04
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='L10nFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta_data', jsonfield.fields.JSONField(default={})),
                ('title', models.CharField(blank=True, max_length=30)),
                ('description', models.CharField(blank=True, max_length=30)),
                ('thumbs', jsonfield.fields.JSONField(default=[])),
                ('file_data', models.FileField(upload_to=b'')),
            ],
        ),
    ]

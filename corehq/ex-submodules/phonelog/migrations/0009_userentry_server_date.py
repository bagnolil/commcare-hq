# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-13 13:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phonelog', '0008_devicelog_varchar_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='userentry',
            name='server_date',
            field=models.DateTimeField(db_index=True, null=True),
        ),
    ]
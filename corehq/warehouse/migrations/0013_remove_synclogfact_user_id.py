# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-11-07 11:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0012_add_synclog_fact'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='synclogfact',
            name='user_id',
        ),
    ]

# Generated by Django 3.1 on 2020-08-13 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UsuarioApp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('token_firebase', models.CharField(max_length=250)),
            ],
            options={
                'ordering': ('-id',),
            },
        ),
    ]

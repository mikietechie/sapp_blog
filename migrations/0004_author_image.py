# Generated by Django 4.2.4 on 2023-09-04 18:59

from django.db import migrations
import sapp.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sapp_blog', '0003_alter_author_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='image',
            field=sapp.models.fields.ImageField(blank=True, null=True, upload_to='blog_authors'),
        ),
    ]

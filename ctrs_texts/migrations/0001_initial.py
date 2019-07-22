# Generated by Django 2.2.2 on 2019-07-19 00:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AbstractedText',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(blank=True, max_length=200, null=True)),
                ('slug', models.SlugField(max_length=200, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AbstractedTextType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(blank=True, max_length=200, null=True)),
                ('slug', models.SlugField(max_length=200, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EncodedTextStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(blank=True, max_length=200, null=True)),
                ('slug', models.SlugField(max_length=200, unique=True)),
                ('sort_order', models.IntegerField(default=0, help_text='The order of this status in your workflow.')),
            ],
            options={
                'verbose_name': 'Text Status',
                'verbose_name_plural': 'Text Statuses',
            },
        ),
        migrations.CreateModel(
            name='EncodedTextType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(blank=True, max_length=200, null=True)),
                ('slug', models.SlugField(max_length=200, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Manuscript',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(blank=True, max_length=200, null=True)),
                ('slug', models.SlugField(max_length=200, unique=True)),
                ('shelfmark', models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(blank=True, max_length=200, null=True)),
                ('slug', models.SlugField(max_length=200, unique=True)),
                ('city', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ManuscriptText',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('short_name', models.CharField(blank=True, max_length=200, null=True)),
                ('slug', models.SlugField(max_length=200, unique=True)),
                ('abstracted_text', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='manuscript_texts', to='ctrs_texts.AbstractedText')),
                ('manuscript', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='manuscripts', to='ctrs_texts.Manuscript')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='manuscript',
            name='repository',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='manuscripts', to='ctrs_texts.Repository'),
        ),
        migrations.CreateModel(
            name='EncodedText',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('content', models.TextField(blank=True, null=True)),
                ('status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='text_content_xmls', to='ctrs_texts.EncodedTextStatus')),
                ('type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='text_content_xmls', to='ctrs_texts.EncodedTextType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='abstractedtext',
            name='encoded_texts',
            field=models.ManyToManyField(related_name='abstracted_texts', to='ctrs_texts.EncodedText'),
        ),
        migrations.AddField(
            model_name='abstractedtext',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='ctrs_texts.AbstractedText'),
        ),
        migrations.AddField(
            model_name='abstractedtext',
            name='type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='text_content_xmls', to='ctrs_texts.AbstractedTextType'),
        ),
    ]
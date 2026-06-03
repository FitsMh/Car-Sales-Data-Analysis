

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SpiderComment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='主键ID')),
                ('series_id', models.CharField(default='', max_length=50, verbose_name='汽车系列ID')),
                ('carname', models.CharField(default='', max_length=255, verbose_name='汽车名称')),
                ('username', models.CharField(default='', max_length=255, verbose_name='评论用户名')),
                ('user_profile_link', models.CharField(default='', max_length=500, verbose_name='用户主页链接')),
                ('content', models.TextField(default='', verbose_name='评论内容')),
                ('timestamp', models.CharField(default='', max_length=100, verbose_name='评论时间')),
                ('comments', models.CharField(default='0', max_length=50, verbose_name='评论数')),
                ('likes', models.CharField(default='0', max_length=50, verbose_name='点赞数')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='入库时间')),
            ],
            options={
                'verbose_name': '爬虫-汽车评论',
                'verbose_name_plural': '爬虫-汽车评论',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='id')),
                ('username', models.CharField(default='', max_length=255, verbose_name='用户名')),
                ('password', models.CharField(default='', max_length=255, verbose_name='密码')),
                ('sex', models.CharField(default='', max_length=255, verbose_name='性别')),
                ('address', models.CharField(default='', max_length=255, verbose_name='地址')),
                ('avatar', models.FileField(default='avatar/default.png', upload_to='avatar', verbose_name='头像')),
                ('textarea', models.CharField(default='这个人很懒，什么都没写...', max_length=255, verbose_name='个人简介')),
                ('createTime', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '前台用户',
                'verbose_name_plural': '前台用户',
            },
        ),
        migrations.CreateModel(
            name='CarInformation',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='id')),
                ('brand', models.CharField(max_length=100, verbose_name='品牌')),
                ('carname', models.CharField(max_length=100, verbose_name='汽车名称')),
                ('carimg', models.URLField(max_length=255, verbose_name='汽车图片链接')),
                ('salevolume', models.IntegerField(verbose_name='销售量')),
                ('price', models.CharField(max_length=100, verbose_name='价格')),
                ('manufacturer', models.CharField(max_length=100, verbose_name='制造商')),
                ('carmodel', models.CharField(max_length=50, verbose_name='车型')),
                ('energytype', models.CharField(max_length=50, verbose_name='能源类型')),
                ('marketime', models.CharField(max_length=50, verbose_name='上市时间')),
                ('insure', models.CharField(blank=True, max_length=100, verbose_name='保修信息')),
            ],
            options={
                'verbose_name': '汽车信息',
                'verbose_name_plural': '汽车信息',
                'unique_together': {('brand', 'carname')},
            },
        ),
        migrations.CreateModel(
            name='CarComment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='id')),
                ('content', models.TextField(verbose_name='评论内容')),
                ('score', models.IntegerField(choices=[(1, '1星'), (2, '2星'), (3, '3星'), (4, '4星'), (5, '5星')], verbose_name='评分')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='评论时间')),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.carinformation', verbose_name='汽车')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.user', verbose_name='用户')),
            ],
            options={
                'verbose_name': '汽车评论',
                'verbose_name_plural': '汽车评论',
                'ordering': ['-create_time'],
            },
        ),
    ]

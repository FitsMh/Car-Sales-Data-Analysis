from django.db import models

class User(models.Model):
    id = models.AutoField('id', primary_key=True)
    username = models.CharField('用户名', max_length=255, default='')
    password = models.CharField('密码', max_length=255, default='')
    sex = models.CharField('性别', max_length=255, default='')
    address = models.CharField('地址', max_length=255, default='')
    avatar = models.FileField('头像', upload_to='avatar', default='avatar/default.png')
    textarea = models.CharField('个人简介', max_length=255, default='这个人很懒，什么都没写...')
    createTime = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name_plural = "前台用户"
        verbose_name = "前台用户"

    def __str__(self):
        return str(self.username)

class CarInformation(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)

class SpiderCarComment(models.Model):
    id = models.AutoField('主键ID', primary_key=True)
    series_id = models.CharField('汽车系列ID', max_length=50, default='')
    carname = models.CharField('汽车名称', max_length=255, default='')
    username = models.CharField('评论用户名', max_length=255, default='')
    user_profile_link = models.CharField('用户主页链接', max_length=500, default='')
    content = models.TextField('评论内容', default='')
    timestamp = models.CharField('评论时间', max_length=100, default='')
    comments = models.CharField('评论数', max_length=10000, default='0')
    likes = models.CharField('点赞数', max_length=50, default='0')
    create_time = models.DateTimeField('入库时间', auto_now_add=True)

    class Meta:
        verbose_name_plural = "爬虫-汽车评论"
        verbose_name = "爬虫-汽车评论"

    def __str__(self):
        return f"{self.username}：{self.content[:80]}"


class CarComment(models.Model):
    id = models.AutoField('id', primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    car = models.ForeignKey(CarInformation, on_delete=models.CASCADE, verbose_name='汽车')
    content = models.TextField('评论内容')
    score = models.IntegerField('评分', choices=[(1, '1星'), (2, '2星'), (3, '3星'), (4, '4星'), (5, '5星')])
    create_time = models.DateTimeField('评论时间', auto_now_add=True)

    class Meta:
        verbose_name_plural = "汽车评论"
        verbose_name = "汽车评论"
        ordering = ['-create_time']

    def __str__(self):
        return f"{str(self.user)}对{str(self.car)}的评论"

class CarInformationOneMonth(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationTwoMonth(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationThreeMonth(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationFourMonth(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationFiveMonth(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationBeijing(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationChengdu(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationChongqing(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationGuangzhou(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationHangzhou(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationNanchang(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationNanjing(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationShanghai(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationShenzhen(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationSuzhou(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationTianjin(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationWuhan(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarInformationXian(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('品牌', max_length=100)
    carname = models.CharField('汽车名称', max_length=100)
    carimg = models.URLField('汽车图片链接', max_length=255)
    salevolume = models.IntegerField('销售量')
    price = models.CharField('价格', max_length=100)
    manufacturer = models.CharField('制造商', max_length=100)
    carmodel = models.CharField('车型', max_length=50)
    energytype = models.CharField('能源类型', max_length=50)
    marketime = models.CharField('上市时间', max_length=50)
    insure = models.CharField('保修信息', max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "汽车信息"
        verbose_name = "汽车信息"
        unique_together = [['brand', 'carname']]

    def __str__(self):
        return str(self.carname)


class CarBrand(models.Model):
    id = models.AutoField('id', primary_key=True)
    brand = models.CharField('汽车品牌名称', max_length=100, unique=True)
    brand_img = models.URLField('品牌图标链接', max_length=255)
    brand_id = models.CharField('品牌ID', max_length=50, blank=True)

    class Meta:
        verbose_name_plural = "汽车品牌"
        verbose_name = "汽车品牌"

    def __str__(self):
        return str(self.brand)

CAR_MONTH_MODELS = {
    "0": CarInformation,
    "1": CarInformationOneMonth,
    "2": CarInformationTwoMonth,
    "3": CarInformationThreeMonth,
    "4": CarInformationFourMonth,
    "5": CarInformationFiveMonth,
}

CAR_CITY_MODELS = {
    "all": CarInformation,
    "beijing": CarInformationBeijing,
    "chengdu": CarInformationChengdu,
    "chongqing": CarInformationChongqing,
    "guangzhou": CarInformationGuangzhou,
    "hangzhou": CarInformationHangzhou,
    "nanchang": CarInformationNanchang,
    "nanjing": CarInformationNanjing,
    "shanghai": CarInformationShanghai,
    "shenzhen": CarInformationShenzhen,
    "suzhou": CarInformationSuzhou,
    "tianjin": CarInformationTianjin,
    "wuhan": CarInformationWuhan,
    "xian": CarInformationXian,
}

CAR_PROVINCE_MODELS = {
    "beijing": CarInformationBeijing,
    "chengdu": CarInformationChengdu,
    "chongqing": CarInformationChongqing,
    "guangzhou": CarInformationGuangzhou,
    "hangzhou": CarInformationHangzhou,
    "nanchang": CarInformationNanchang,
    "nanjing": CarInformationNanjing,
    "shanghai": CarInformationShanghai,
    "shenzhen": CarInformationShenzhen,
    "suzhou": CarInformationSuzhou,
    "tianjin": CarInformationTianjin,
    "wuhan": CarInformationWuhan,
    "xian": CarInformationXian,
}

CAR_CITY_NAMES = {
    "all": "全国",
    "beijing": "北京",
    "chengdu": "成都",
    "chongqing": "重庆",
    "guangzhou": "广州",
    "hangzhou": "杭州",
    "nanchang": "南昌",
    "nanjing": "南京",
    "shanghai": "上海",
    "shenzhen": "深圳",
    "suzhou": "苏州",
    "tianjin": "天津",
    "wuhan": "武汉",
    "xian": "西安",
}
CAR_CITY_PROVINCE = {
    "beijing": "北京市",
    "shanghai": "上海市",
    "tianjin": "天津市",
    "chongqing": "重庆市",
    "guangzhou": "广东省",
    "shenzhen": "广东省",
    "chengdu": "四川省",
    "hangzhou": "浙江省",
    "suzhou": "江苏省",
    "nanjing": "江苏省",
    "wuhan": "湖北省",
    "xian": "陕西省",
    "nanchang": "江西省",
}
CAR_MONTH_NAMES = {
    "0": "1个月前",
    "1": "2个月前",
    "2": "3个月前",
    "3": "4个月前",
    "4": "5个月前",
    "5": "6个月前（半年）",
}

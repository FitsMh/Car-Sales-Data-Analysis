import json
import re
import os
import django
from django.db.models import Q, Count, Sum


os.environ.setdefault('DJANGO_SETTINGS_MODULE', '基于Django系统.settings')
django.setup()

from app.models import (
    CarInformation, CarInformationOneMonth, CarInformationTwoMonth,
    CarInformationThreeMonth, CarInformationFourMonth, CarInformationFiveMonth,
    CarInformationBeijing, CarInformationChengdu, CarInformationChongqing,
    CarInformationGuangzhou, CarInformationHangzhou, CarInformationNanchang,
    CarInformationNanjing, CarInformationShanghai, CarInformationShenzhen,
    CarInformationSuzhou, CarInformationTianjin, CarInformationWuhan,
    CarInformationXian
)





MONTH_MODELS = {
    0: CarInformation,
    1: CarInformationOneMonth,
    2: CarInformationTwoMonth,
    3: CarInformationThreeMonth,
    4: CarInformationFourMonth,
    5: CarInformationFiveMonth,
}

MONTH_LABELS = {
    0: "最近1个月（最新月）",
    1: "2个月前",
    2: "3个月前",
    3: "4个月前",
    4: "5个月前",
    5: "6个月前（半年前）",
}


CITY_MODELS = {
    '北京': CarInformationBeijing,
    '成都': CarInformationChengdu,
    '重庆': CarInformationChongqing,
    '广州': CarInformationGuangzhou,
    '杭州': CarInformationHangzhou,
    '南昌': CarInformationNanchang,
    '南京': CarInformationNanjing,
    '上海': CarInformationShanghai,
    '深圳': CarInformationShenzhen,
    '苏州': CarInformationSuzhou,
    '天津': CarInformationTianjin,
    '武汉': CarInformationWuhan,
    '西安': CarInformationXian,
}


def parse_month_from_question(question):
    q = question

    patterns = [
        (r'最近\s*1?\s*个?月|本月|这个月|最新|当前|现在', 0),
        (r'上个?月|1\s*个?月前|一个月前', 0),
        (r'2\s*个?月前|两个月前|两个月', 1),
        (r'3\s*个?月前|三个月前|三个月', 2),
        (r'4\s*个?月前|四个月前|四个月', 3),
        (r'5\s*个?月前|五个月前|五个月', 4),
        (r'半年前|6\s*个?月前|六个月前|六个月', 5),
        (r'第\s*(\d+)\s*个?月', None),
        (r'(\d+)\s*个?月前', None),
    ]
    for pattern, fixed_val in patterns:
        match = re.search(pattern, q)
        if match:
            if fixed_val is not None:
                return fixed_val

            try:
                group = match.group(1)
                month = int(group)
                if month == 1:
                    return 0
                elif 2 <= month <= 6:
                    return month - 1
                elif month > 6:
                    return 5
            except (IndexError, ValueError):
                pass
    return None


def parse_city_from_question(question):
    for city in CITY_MODELS.keys():
        if city in question:
            return city
    return None


def get_model(month=None, city=None):
    if city and city in CITY_MODELS:
        return CITY_MODELS[city]
    if month is not None and month in MONTH_MODELS:
        return MONTH_MODELS[month]
    return CarInformation


def get_data_source_label(month=None, city=None):
    if city and city in CITY_MODELS:
        label = f"{city}市"
        if month is not None and month in MONTH_LABELS:
            label += f"（{MONTH_LABELS[month]}）"
        return label
    if month is not None and month in MONTH_LABELS:
        return MONTH_LABELS[month]
    return "全国（最近1个月）"






def get_top_sales_cars(month=None, city=None, top_n=10):
    Model = get_model(month, city)
    cars = Model.objects.all().order_by('-salevolume')[:top_n]
    return list(cars)


def get_brand_sales_ranking(month=None, city=None, top_n=10):
    Model = get_model(month, city)
    brand_sales = Model.objects.values('brand')\
        .annotate(total_sales=Sum('salevolume'))\
        .order_by('-total_sales')[:top_n]
    return list(brand_sales)


def get_energy_type_analysis(month=None, city=None):
    Model = get_model(month, city)
    energy_stats = Model.objects.values('energytype')\
        .annotate(count=Count('id'), total_sales=Sum('salevolume'))\
        .order_by('-total_sales')
    return list(energy_stats)


def get_car_by_energy_type(energy_type, month=None, city=None, top_n=10):
    Model = get_model(month, city)

    cars = Model.objects.filter(energytype__icontains=energy_type)\
        .order_by('-salevolume')[:top_n]
    return list(cars)


def get_car_price_range_analysis(price_min=None, price_max=None, month=None, city=None):
    Model = get_model(month, city)
    cars = Model.objects.all()
    result = []
    for car in cars:
        try:
            price_list = json.loads(car.price)
            if isinstance(price_list, list):
                avg_price = sum(float(p) for p in price_list) / len(price_list)
            else:
                avg_price = float(price_list)
        except (json.JSONDecodeError, TypeError, ValueError):
            try:
                avg_price = float(car.price)
            except (TypeError, ValueError):
                continue

        if price_min is not None and avg_price < price_min:
            continue
        if price_max is not None and avg_price > price_max:
            continue

        result.append({
            'brand': car.brand,
            'carname': car.carname,
            'price': car.price,
            'avg_price': avg_price,
            'salevolume': car.salevolume,
            'energytype': car.energytype,
            'manufacturer': car.manufacturer,
        })

    return sorted(result, key=lambda x: x['salevolume'], reverse=True)[:10]


def get_car_by_brand(brand_name, month=None, city=None, top_n=10):
    Model = get_model(month, city)
    cars = Model.objects.filter(brand__icontains=brand_name)\
        .order_by('-salevolume')[:top_n]
    return list(cars)


def get_all_brands(month=None, city=None):
    Model = get_model(month, city)
    brands = Model.objects.values_list('brand', flat=True).distinct()
    return list(set(brands))


def get_all_energy_types(month=None, city=None):
    Model = get_model(month, city)
    types = Model.objects.values_list('energytype', flat=True).distinct()
    return list(set(types))


def get_all_car_names(month=None, city=None):
    Model = get_model(month, city)
    names = Model.objects.values('brand', 'carname', 'salevolume', 'price', 'energytype')\
        .order_by('-salevolume')
    return list(names)


def get_car_model_type_analysis(month=None, city=None):
    Model = get_model(month, city)
    stats = Model.objects.values('carmodel')\
        .annotate(count=Count('id'), total_sales=Sum('salevolume'))\
        .order_by('-total_sales')
    return list(stats)


def get_car_detail(car_name, month=None, city=None):
    Model = get_model(month, city)
    cars = Model.objects.filter(carname__icontains=car_name)[:5]
    return list(cars)


def search_cars(keyword, month=None, city=None, top_n=10):
    Model = get_model(month, city)
    cars = Model.objects.filter(
        Q(brand__icontains=keyword) | Q(carname__icontains=keyword)
    ).order_by('-salevolume')[:top_n]
    return list(cars)






def _should_query(question):

    skip_keywords = ['天气', '笑话', '翻译', '算数', '计算', '编程', '代码',
                     'python', 'java', '英语', '数学', '历史', '地理',
                     '做饭', '菜谱', '旅游攻略', '电影']
    for kw in skip_keywords:
        if kw in question:
            return False


    car_keywords = [
        '车', '汽车', '车型', '品牌', '销量', '价格', '新能源', '电动',
        '燃油', '混动', '推荐', '买', 'SUV', '轿车', 'MPV', '面包车',
        '制造商', '厂家', '保修', '上市', '哪个', '什么车', '排行榜',
        '排行', '前十', '多少', '万', '性价比', '保值', '优惠',
        '比亚迪', '特斯拉', '大众', '丰田', '本田', '宝马', '奔驰',
        '奥迪', '吉利', '长安', '哈弗', '五菱', '蔚来', '理想', '小鹏',
        '哪吒', '零跑', '问界', '小米', '华为', '极氪', '深蓝',
        '领克', '红旗', '奇瑞', '广汽', '一汽', '东风', '上汽',
        '比亚迪', '特斯拉', '保时捷', '沃尔沃', '福特', '日产',
    ]
    for kw in car_keywords:
        if kw in question:
            return True

    return False


def _car_to_dict(car):
    return {
        'brand': car.brand,
        'carname': car.carname,
        'price': car.price,
        'salevolume': car.salevolume,
        'energytype': car.energytype,
        'manufacturer': car.manufacturer,
        'carmodel': car.carmodel,
        'marketime': car.marketime,
        'insure': car.insure,
    }


def _cars_to_context(cars, title):
    lines = [title]
    for i, car in enumerate(cars, 1):
        lines.append(
            f"{i}. 品牌：{car.brand}，车型：{car.carname}，"
            f"销量：{car.salevolume}辆，价格：{car.price}，"
            f"能源类型：{car.energytype}，车型级别：{car.carmodel}，"
            f"制造商：{car.manufacturer}"
        )
    return "\n".join(lines)


def _cars_to_answer(cars, title):
    lines = [title]
    for i, car in enumerate(cars, 1):
        lines.append(f"{i}. {car.brand} {car.carname} - 销量：{car.salevolume}辆，价格：{car.price}")
    return "\n".join(lines)


def query_database_for_question(question):
    result = {
        'can_answer': False,
        'data': None,
        'answer': '',
        'context': ''
    }


    if not _should_query(question):
        return result

    month = parse_month_from_question(question)
    city = parse_city_from_question(question)
    label = get_data_source_label(month, city)
    context_parts = []


    is_recommend = any(kw in question for kw in [
        '推荐', '有哪些', '有什么车', '什么车好', '哪些车', '选什么',
        '买什么', '买哪', '哪款好', '哪个好', '值得买', '求推荐',
    ])


    is_energy_query = any(kw in question for kw in [
        '新能源', '电动', '纯电', '插电', '混动', '增程', '燃料电池',
    ])

    energy_filter = None
    if is_energy_query:
        if '混动' in question or '插电' in question or '增程' in question:
            energy_filter = '混'
        elif '纯电' in question:
            energy_filter = '纯电'
        elif '燃料' in question:
            energy_filter = '氢'

        if '电动' in question or '纯电' in question:
            if energy_filter is None:
                energy_filter = '电'


    is_sales_query = any(kw in question for kw in [
        '销量最高', '销量排行', '卖得最好', '最受欢迎', '销量第一',
        '排行榜', '排名', '前十', 'TOP', 'top',
    ])


    is_brand_query = any(kw in question for kw in [
        '品牌排行', '哪个品牌', '品牌销量', '品牌推荐',
    ])

    mentioned_brand = None
    brand_names = [
        '比亚迪', '特斯拉', '大众', '丰田', '本田', '宝马', '奔驰',
        '奥迪', '吉利', '长安', '哈弗', '五菱', '蔚来', '理想', '小鹏',
        '哪吒', '零跑', '问界', '小米', '华为', '极氪', '深蓝',
        '领克', '红旗', '奇瑞', '广汽', '一汽', '东风', '上汽',
        '保时捷', '沃尔沃', '福特', '日产', '现代', '起亚', '标致',
        '雪铁龙', '别克', '雪佛兰', '凯迪拉克', '雷克萨斯', '英菲尼迪',
        '路虎', '捷豹', '玛莎拉蒂', '兰博基尼', '法拉利', '宾利',
        '劳斯莱斯', '阿维塔', '智己', '飞凡', '腾势', '魏牌',
        '坦克', '捷途', '星途', '岚图', '极狐', '埃安', '传祺',
    ]
    for b in brand_names:
        if b in question:
            mentioned_brand = b
            break


    is_price_query = any(kw in question for kw in [
        '价格', '价位', '多少钱', '预算', '万', '性价比', '便宜',
        '贵', '划算', '高性价比',
    ])
    price_min = price_max = None
    if is_price_query:
        price_patterns = [
            r'(\d+)\s*[-到至~]\s*(\d+)\s*万',
            r'(\d+)\s*万(?:以[下内])?',
            r'(?:预算|价位|价格)\s*(\d+)',
        ]
        for pattern in price_patterns:
            match = re.search(pattern, question)
            if match:
                groups = match.groups()
                if len(groups) == 2 and groups[1]:
                    price_min = int(groups[0])
                    price_max = int(groups[1])
                else:
                    price = int(groups[0])
                    price_max = price
                break

        if price_max and not price_min:
            price_min = 0


    car_model_type = None
    for t in ['SUV', 'suv', '轿车', 'MPV', 'mpv', '面包车', '皮卡', '跑车', '微型车', '小型车', '紧凑型', '中型', '中大型', '大型']:
        if t in question:
            car_model_type = t.upper() if t.lower() in ['suv', 'mpv'] else t
            break


    is_specific_car = False
    if mentioned_brand and any(kw in question for kw in ['怎么样', '如何', '好不好', '配置', '参数', '详情', '介绍']):
        is_specific_car = True


    is_city_query = city is not None


    is_energy_analysis = any(kw in question for kw in ['能源类型', '能源分析', '能源占比', '能源分布'])


    is_model_analysis = any(kw in question for kw in ['车型分析', '车型级别', '车型占比', '车型分布', 'SUV占比', '轿车占比'])


    is_list_all = any(kw in question for kw in ['所有品牌', '全部品牌', '有哪些品牌', '品牌列表', '有什么品牌'])


    is_trend = any(kw in question for kw in ['趋势', '变化', '对比', '涨幅', '跌幅', '增长', '下滑', '同比下降', '环比', '各月'])




    matched = False


    if is_recommend and not mentioned_brand and not is_energy_query and not is_price_query:

        cars = get_top_sales_cars(month=month, city=city, top_n=10)
        if cars:
            context_parts.append(_cars_to_context(cars, f"根据{label}数据，以下是最畅销的车型："))
            matched = True


    if is_energy_query and (is_recommend or not is_energy_analysis):
        if energy_filter:
            cars = get_car_by_energy_type(energy_filter, month=month, city=city, top_n=10)
        else:

            cars = get_car_by_energy_type('电', month=month, city=city, top_n=10)
            cars2 = get_car_by_energy_type('新', month=month, city=city, top_n=10)

            seen = set()
            merged = []
            for c in cars + cars2:
                key = (c.brand, c.carname)
                if key not in seen:
                    seen.add(key)
                    merged.append(c)
            cars = merged[:10]

        if cars:
            context_parts.append(_cars_to_context(cars, f"根据{label}数据，以下是新能源相关车型（按销量排序）："))
            matched = True


    if is_energy_query and mentioned_brand:
        Model = get_model(month, city)
        cars = Model.objects.filter(
            Q(brand__icontains=mentioned_brand) & (Q(energytype__icontains='电') | Q(energytype__icontains='新') | Q(energytype__icontains='混'))
        ).order_by('-salevolume')[:10]
        if cars:
            context_parts.append(_cars_to_context(list(cars), f"根据{label}数据，{mentioned_brand}的新能源车型："))
            matched = True


    if is_energy_query and is_price_query and price_max:
        Model = get_model(month, city)
        all_cars = Model.objects.filter(
            Q(energytype__icontains='电') | Q(energytype__icontains='新') | Q(energytype__icontains='混')
        )
        price_cars = []
        for car in all_cars:
            try:
                price_list = json.loads(car.price)
                if isinstance(price_list, list):
                    avg = sum(float(p) for p in price_list) / len(price_list)
                else:
                    avg = float(car.price)
            except:
                try:
                    avg = float(car.price)
                except:
                    continue
            if price_min is not None and avg < price_min:
                continue
            if price_max is not None and avg > price_max:
                continue
            price_cars.append((car, avg))
        price_cars.sort(key=lambda x: x[1])
        cars = [c[0] for c in price_cars[:10]]
        if cars:
            context_parts.append(_cars_to_context(cars, f"根据{label}数据，{price_min or 0}-{price_max}万的新能源车型："))
            matched = True


    if is_sales_query:
        cars = get_top_sales_cars(month=month, city=city, top_n=10)
        if cars:
            context_parts.append(_cars_to_context(cars, f"根据{label}数据，销量排行如下："))
            matched = True


    if is_brand_query:
        ranking = get_brand_sales_ranking(month=month, city=city, top_n=10)
        if ranking:
            lines = [f"根据{label}数据，品牌销量排行："]
            for i, item in enumerate(ranking, 1):
                lines.append(f"{i}. {item['brand']}：总销量{item['total_sales']}辆")
            context_parts.append("\n".join(lines))
            matched = True


    if mentioned_brand and not is_specific_car and not is_energy_query:
        cars = get_car_by_brand(mentioned_brand, month=month, city=city, top_n=10)
        if cars:
            context_parts.append(_cars_to_context(cars, f"根据{label}数据，{mentioned_brand}品牌车型："))
            matched = True


    if is_specific_car and mentioned_brand:
        Model = get_model(month, city)
        cars = Model.objects.filter(brand__icontains=mentioned_brand)[:10]
        if cars:
            lines = [f"根据{label}数据，{mentioned_brand}品牌车型详情："]
            for i, car in enumerate(cars, 1):
                lines.append(
                    f"{i}. {car.brand} {car.carname}\n"
                    f"   销量：{car.salevolume}辆，价格：{car.price}\n"
                    f"   能源类型：{car.energytype}，车型级别：{car.carmodel}\n"
                    f"   制造商：{car.manufacturer}，上市时间：{car.marketime}\n"
                    f"   保修：{car.insure}"
                )
            context_parts.append("\n".join(lines))
            matched = True


    if is_price_query and not is_energy_query and price_max is not None:
        cars = get_car_price_range_analysis(price_min=price_min, price_max=price_max,
                                            month=month, city=city)
        if cars:
            lines = [f"根据{label}数据，{price_min or 0}-{price_max}万价格区间的车型："]
            for i, car in enumerate(cars, 1):
                lines.append(
                    f"{i}. {car['brand']} {car['carname']}，"
                    f"均价{car['avg_price']:.1f}万，销量{car['salevolume']}辆，"
                    f"能源类型：{car['energytype']}"
                )
            context_parts.append("\n".join(lines))
            matched = True


    if car_model_type:
        Model = get_model(month, city)
        cars = Model.objects.filter(carmodel__icontains=car_model_type)\
            .order_by('-salevolume')[:10]
        if cars:
            context_parts.append(_cars_to_context(list(cars), f"根据{label}数据，{car_model_type}车型："))
            matched = True


    if is_city_query and not is_sales_query and not is_recommend:
        cars = get_top_sales_cars(month=month, city=city, top_n=10)
        if cars:
            context_parts.append(_cars_to_context(cars, f"根据{city}数据，销量最高车型："))
            matched = True


    if is_energy_analysis:
        stats = get_energy_type_analysis(month=month, city=city)
        if stats:
            lines = [f"根据{label}数据，能源类型分析："]
            for item in stats:
                lines.append(f"- {item['energytype']}：{item['count']}款车型，总销量{item['total_sales']}辆")
            context_parts.append("\n".join(lines))
            matched = True


    if is_model_analysis:
        stats = get_car_model_type_analysis(month=month, city=city)
        if stats:
            lines = [f"根据{label}数据，车型级别分析："]
            for item in stats:
                lines.append(f"- {item['carmodel']}：{item['count']}款车型，总销量{item['total_sales']}辆")
            context_parts.append("\n".join(lines))
            matched = True


    if is_list_all:
        brands = get_all_brands(month=month, city=city)
        if brands:
            lines = [f"根据{label}数据，数据库中所有品牌（共{len(brands)}个）："]
            for i, b in enumerate(sorted(brands), 1):
                lines.append(f"{i}. {b}")
            context_parts.append("\n".join(lines))
            matched = True


    if is_trend:
        trend_lines = ["各月份数据对比（仅展示销量TOP5）："]
        for m in range(6):
            Model = MONTH_MODELS[m]
            top5 = list(Model.objects.all().order_by('-salevolume')[:5])
            if top5:
                trend_lines.append(f"\n【{MONTH_LABELS[m]}】")
                for i, car in enumerate(top5, 1):
                    trend_lines.append(f"  {i}. {car.brand} {car.carname} - 销量：{car.salevolume}辆")
        context_parts.append("\n".join(trend_lines))
        matched = True





    if not matched and _should_query(question):

        all_cars = get_all_car_names(month=month, city=city)[:30]
        if all_cars:
            lines = [f"根据{label}数据，数据库中的车型（按销量排序前30）："]
            for i, car in enumerate(all_cars, 1):
                lines.append(
                    f"{i}. 品牌：{car['brand']}，车型：{car['carname']}，"
                    f"销量：{car['salevolume']}辆，价格：{car['price']}，"
                    f"能源类型：{car['energytype']}"
                )
            context_parts.append("\n".join(lines))
            matched = True




    if matched and context_parts:
        result['can_answer'] = True
        result['context'] = "\n\n".join(context_parts)
    else:
        result['can_answer'] = False

    return result


def format_context_for_ai(question, db_result):
    """
    将数据库查询结果格式化为 AI 的上下文（system prompt + 数据）
    """
    if not db_result or not db_result.get('can_answer'):
        return None

    context = f"""你是一个专业的汽车销售数据分析助手。你可以访问到真实的汽车销售数据库，数据库包含以下信息：

【数据库结构说明】
- 每条车型记录包含：品牌(brand)、汽车名称(carname)、图片链接(carimg)、销售量(salevolume)、价格(price)、制造商(manufacturer)、车型级别(carmodel)、能源类型(energytype)、上市时间(marketime)、保修信息(insure)
- 时间维度：共有6个月份的数据表
  · CarInformation = 最近1个月（最新月）数据
  · CarInformationOneMonth = 2个月前数据
  · CarInformationTwoMonth = 3个月前数据
  · CarInformationThreeMonth = 4个月前数据
  · CarInformationFourMonth = 5个月前数据
  · CarInformationFiveMonth = 6个月前（半年前）数据
- 地域维度：全国数据 + 13个城市（北京、上海、广州、深圳、成都、重庆、杭州、苏州、南京、天津、武汉、西安、南昌）的数据
- 另外还有用户评论数据(CarComment, SpiderCarComment)和品牌数据(CarBrand)

【回答规则】
1. 必须严格基于下方提供的真实数据库数据来回答，不得编造任何数据
2. 如果用户问的问题超出了数据库能提供的范围，诚实说明，但可以基于已有数据做合理分析
3. 回答要专业、有数据支撑、有条理
4. 如果数据中包含多款车型，用编号列表展示
5. 可以基于数据趋势给出你的专业分析和建议

用户问题：{question}

{db_result.get('context', '')}

请根据以上真实数据库数据回答用户问题。如果数据不足以完全回答，可以说明数据范围并基于已有数据进行分析。
"""
    return context

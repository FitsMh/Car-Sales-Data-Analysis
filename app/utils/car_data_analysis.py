from datetime import datetime
import numpy as np
from django.db.models import Count, Sum
from app.models import CarBrand
from app.models import CarInformation, CAR_PROVINCE_MODELS
from app.models import CarInformationOneMonth, CarInformationTwoMonth
from app.models import CarInformationThreeMonth, CarInformationFourMonth, CarInformationFiveMonth


def get_car_model_by_month_and_city(month, city):
    from app.models import CAR_MONTH_MODELS, CAR_CITY_MODELS
    if city != 'all':
        month = '0'
    base_model = CAR_MONTH_MODELS.get(month, CAR_MONTH_MODELS['0'])
    city_model = CAR_CITY_MODELS.get(city, CAR_CITY_MODELS['all'])
    return city_model


class CarDataAnalysis:
    @staticmethod
    def get_time_label(month_key):
        today = datetime.now()
        current_year = today.year
        current_month = today.month

        month_offset = int(month_key)
        target_month = current_month - month_offset - 1
        target_year = current_year

        while target_month < 1:
            target_year -= 1
            target_month += 12

        return f"{target_year}年{target_month:02d}月"

    @staticmethod
    def get_month_options():
        return [
            {"key": "0", "label": CarDataAnalysis.get_time_label("0")},
            {"key": "1", "label": CarDataAnalysis.get_time_label("1")},
            {"key": "2", "label": CarDataAnalysis.get_time_label("2")},
            {"key": "3", "label": CarDataAnalysis.get_time_label("3")},
            {"key": "4", "label": CarDataAnalysis.get_time_label("4")},
            {"key": "5", "label": CarDataAnalysis.get_time_label("5")},
        ]

    @staticmethod
    def get_city_options():
        from app.models import CAR_CITY_NAMES
        return [
            {"key": k, "label": v}
            for k, v in CAR_CITY_NAMES.items()
        ]

    @staticmethod
    def get_model_by_params(city="all", month="0"):
        from app.models import CAR_CITY_MODELS, CAR_MONTH_MODELS
        if city != "all":
            month = "0"
        month_model = CAR_MONTH_MODELS.get(month, CarInformation)
        city_model = CAR_CITY_MODELS.get(city, CarInformation)
        return city_model if city != "all" else month_model

    @staticmethod
    def get_top_brands_by_sales(limit=10, city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        result = model.objects.values('brand').annotate(
            total_sales=Sum('salevolume')
        ).order_by('-total_sales')[:limit]
        brand_list = []
        total_sales_all = model.objects.aggregate(total=Sum('salevolume'))['total'] or 1
        for item in result:
            brand_name = item['brand']
            sales = item['total_sales']
            brand_obj = CarBrand.objects.filter(brand=brand_name).first()
            brand_img = brand_obj.brand_img if brand_obj else ""
            rate = round(sales / total_sales_all * 100, 2)
            brand_list.append({
                'brand': brand_name,
                'sales': sales,
                'brand_img': brand_img,
                'rate': rate
            })
        return brand_list

    @staticmethod
    def get_top_cars_by_sales(limit=10, city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        results = model.objects.all().order_by('-salevolume')[:limit]
        car_list = []
        for car in results:
            car_list.append({
                'car_name': f"{car.brand} {car.carname}",
                'sale_volume': car.salevolume,
                'car_img': car.carimg
            })
        return car_list

    @staticmethod
    def get_energy_type_distribution(city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        result = model.objects.values('energytype').annotate(
            count=Count('id')
        ).order_by('-count')
        return {
            'energy_types': [item['energytype'] for item in result],
            'counts': [item['count'] for item in result]
        }

    @staticmethod
    def get_car_model_distribution(city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        result = model.objects.values('carmodel').annotate(
            count=Count('id')
        ).order_by('-count')
        return {
            'car_models': [item['carmodel'] for item in result],
            'counts': [item['count'] for item in result]
        }

    @staticmethod
    def get_sales_by_energy_type(city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        result = model.objects.values('energytype').annotate(
            total_sales=Sum('salevolume')
        ).order_by('-total_sales')
        return {
            'energy_types': [item['energytype'] for item in result],
            'sales': [item['total_sales'] for item in result]
        }

    @staticmethod
    def get_top_selling_cars(limit=10, city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        result = model.objects.all().order_by('-salevolume')[:limit]
        return {
            'car_names': [f"{car.brand} {car.carname}" for car in result],
            'sales': [car.salevolume for car in result],
            'images': [car.carimg for car in result]
        }

    @staticmethod
    def get_manufacturer_market_share(city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        total_sales = model.objects.aggregate(total=Sum('salevolume'))['total'] or 1
        result = model.objects.values('manufacturer', 'brand').annotate(
            total_sales=Sum('salevolume')
        ).order_by('-total_sales')
        manufacturers = []
        market_shares = []
        brand_imgs = []
        for item in result:
            manufacturer_name = item['manufacturer']
            brand_name = item['brand']
            sales = item['total_sales']
            share = round((sales / total_sales) * 100, 2)
            brand_obj = CarBrand.objects.filter(brand=brand_name).first()
            brand_img = brand_obj.brand_img if brand_obj else ""
            manufacturers.append(manufacturer_name)
            market_shares.append(share)
            brand_imgs.append(brand_img)
        return {
            'manufacturers': manufacturers,
            'market_shares': market_shares,
            'brand_imgs': brand_imgs
        }

    @staticmethod
    def get_price_range_distribution(city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        cars = model.objects.all()
        price_ranges = {
            '10万以下': 0,
            '10-15万': 0,
            '15-20万': 0,
            '20-30万': 0,
            '30-50万': 0,
            '50万以上': 0
        }
        for car in cars:
            try:
                price_str = car.price.strip('[]').split(',')
                if len(price_str) >= 2:
                    min_price = float(price_str[1])
                    if min_price < 10:
                        price_ranges['10万以下'] += 1
                    elif 10 <= min_price < 15:
                        price_ranges['10-15万'] += 1
                    elif 15 <= min_price < 20:
                        price_ranges['15-20万'] += 1
                    elif 20 <= min_price < 30:
                        price_ranges['20-30万'] += 1
                    elif 30 <= min_price < 50:
                        price_ranges['30-50万'] += 1
                    else:
                        price_ranges['50万以上'] += 1
            except:
                continue
        return {
            'price_ranges': list(price_ranges.keys()),
            'counts': list(price_ranges.values())
        }

    @staticmethod
    def get_price_boxplot_data(city="all", month="0"):
        """
        获取价格箱线图数据
        过滤规则：
        1. 最低价格小于等于1万的视为0元/天价异常数据，予以过滤
        2. 最高价格大于等于500万的视为天价车，予以过滤
        3. 只保留最低价格在合理范围内的数据

        返回分组后的最低价格数据，按能源类型分组
        """
        model = CarDataAnalysis.get_model_by_params(city, month)
        cars = model.objects.all()

                       
        energy_price_map = {}
        energy_carname_map = {}                  
        filtered_count = 0
        total_count = 0

        for car in cars:
            total_count += 1
            try:
                price_str = car.price.strip('[]').split(',')
                if len(price_str) >= 2:
                    min_price = float(price_str[1])
                                              
                                                   
                    if min_price <= 1 or min_price >= 500:
                        filtered_count += 1
                        continue

                    energy_type = car.energytype if car.energytype else '其他'
                    if energy_type not in energy_price_map:
                        energy_price_map[energy_type] = []
                        energy_carname_map[energy_type] = []
                    energy_price_map[energy_type].append(min_price)
                                 
                    car_display_name = f"{car.brand} {car.carname}"
                    energy_carname_map[energy_type].append(car_display_name)
            except:
                filtered_count += 1
                continue

                 
        boxplot_categories = list(energy_price_map.keys())
        boxplot_data = [energy_price_map[cat] for cat in boxplot_categories]
        boxplot_carnames = [energy_carname_map[cat] for cat in boxplot_categories]           

                
        stats_info = {}
        for energy_type, prices in energy_price_map.items():
            if prices:
                sorted_prices = sorted(prices)
                n = len(sorted_prices)
                stats_info[energy_type] = {
                    'count': n,
                    'min': round(sorted_prices[0], 2),
                    'q1': round(sorted_prices[n // 4], 2),
                    'median': round(sorted_prices[n // 2], 2),
                    'q3': round(sorted_prices[3 * n // 4], 2),
                    'max': round(sorted_prices[-1], 2),
                    'mean': round(sum(prices) / n, 2)
                }

        return {
            'categories': boxplot_categories,
            'data': boxplot_data,
            'car_names': boxplot_carnames,           
            'stats': stats_info,
            'filtered_count': filtered_count,
            'total_count': total_count,
            'active_count': total_count - filtered_count
        }

    @staticmethod
    def get_new_energy_vs_traditional(city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        new_energy_types = ['纯电动', '插电式混合动力', '增程式', '油电混合']
        new_energy_count = model.objects.filter(energytype__in=new_energy_types).count()
        traditional_count = model.objects.exclude(energytype__in=new_energy_types).count()
        new_energy_sales = model.objects.filter(energytype__in=new_energy_types).aggregate(total=Sum('salevolume'))[
                               'total'] or 0
        traditional_sales = model.objects.exclude(energytype__in=new_energy_types).aggregate(total=Sum('salevolume'))[
                                'total'] or 0
        return {
            'counts': {
                'categories': ['新能源汽车', '传统燃油车'],
                'values': [new_energy_count, traditional_count]
            },
            'sales': {
                'categories': ['新能源汽车', '传统燃油车'],
                'values': [new_energy_sales, traditional_sales]
            }
        }

    @staticmethod
    def get_recent_market_trends(city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        cars = model.objects.all()
        year_counts = {}
        for car in cars:
            try:
                year = car.marketime.split('.')[0]
                year_counts[year] = year_counts.get(year, 0) + 1
            except:
                continue
        sorted_years = sorted(year_counts.keys())
        return {
            'years': sorted_years,
            'counts': [year_counts[year] for year in sorted_years]
        }

    @staticmethod
    def get_monthly_new_car_trend():
        from datetime import datetime
        MODEL_ORDER = [
            CarInformationFiveMonth,
            CarInformationFourMonth,
            CarInformationThreeMonth,
            CarInformationTwoMonth,
            CarInformationOneMonth,
            CarInformation
        ]
        today = datetime.now()
        current_year = today.year
        current_month = today.month
        month_labels = []
        for i in range(6):
            months_ago = i + 1
            year = current_year
            month = current_month - months_ago
            while month < 1:
                year -= 1
                month += 12
            month_labels.append(f"{year}年{month:02d}月")
        month_labels = month_labels[::-1]
        all_existing_cars = set()
        monthly_new_counts = []
        for i, model in enumerate(MODEL_ORDER):
            try:
                current_cars = set()
                for car in model.objects.all():
                    car_key = f"{car.brand}_{car.carname}"
                    current_cars.add(car_key)
                if i == 0:
                    new_count = 0
                    all_existing_cars.update(current_cars)
                else:
                    new_cars = current_cars - all_existing_cars
                    new_count = len(new_cars)
                    all_existing_cars.update(new_cars)
                monthly_new_counts.append(new_count)
            except Exception as e:
                monthly_new_counts.append(0)
        return {
            "months": month_labels,
            "counts": monthly_new_counts
        }

    @staticmethod
    def get_all_month_models():
        return [
            CarInformation,
            CarInformationOneMonth,
            CarInformationTwoMonth,
            CarInformationThreeMonth,
            CarInformationFourMonth,
            CarInformationFiveMonth
        ]

    @staticmethod
    def get_car_sales_history(carname):
        models = CarDataAnalysis.get_all_month_models()
        history = []
        for model in models:
            try:
                car = model.objects.filter(carname=carname).first()
                history.append(car.salevolume if car else 0)
            except:
                history.append(0)
        return history[::-1]

    @staticmethod
    def get_brand_sales_history(brand):
        models = CarDataAnalysis.get_all_month_models()
        history = []
        for model in models:
            try:
                total = model.objects.filter(brand=brand).aggregate(total=Sum('salevolume'))['total'] or 0
                history.append(total)
            except:
                history.append(0)
        return history[::-1]

    @staticmethod
    def get_season_factor(month_index):
        season = [1.2, 0.9, 1.1, 1.3, 1.5, 1.4]
        return season[month_index % 6]

                                                                
    @staticmethod
    def get_city_sales_list():
        city_map = {
            "beijing": "北京",
            "shanghai": "上海",
            "tianjin": "天津",
            "chongqing": "重庆",
            "chengdu": "成都",
            "guangzhou": "广州",
            "shenzhen": "深圳",
            "hangzhou": "杭州",
            "nanchang": "南昌",
            "nanjing": "南京",
            "suzhou": "苏州",
            "wuhan": "武汉",
            "xian": "西安"
        }
        city_sales = []
        for city_en, city_cn in city_map.items():
            try:
                model = CAR_PROVINCE_MODELS.get(city_en)
                sales = model.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                city_sales.append({"name": city_cn, "sales": sales})
            except:
                city_sales.append({"name": city_cn, "sales": 0})
        return sorted(city_sales, key=lambda x: x['sales'], reverse=True)

    @staticmethod
    def get_city_sales_for_map():
        province_sales = []
        province_map = {
            "beijing": "北京",
            "tianjin": "天津",
            "shanxi": "山西",
            "neimenggu": "内蒙古",
            "liaoning": "辽宁",
            "jilin": "吉林",
            "heilongjiang": "黑龙江",
            "shanghai": "上海",
            "jiangsu": "江苏",
            "zhejiang": "浙江",
            "anhui": "安徽",
            "fujian": "福建",
            "hebei": "河北",
            "taiwan": "台湾",
            "nanhaiszhudao": "南海诸岛",
            "jiangxi": "江西",
            "shandong": "山东",
            "henan": "河南",
            "hubei": "湖北",
            "hunan": "湖南",
            "guangdong": "广东",
            "guangxi": "广西",
            "hainan": "海南",
            "chongqing": "重庆",
            "sichuan": "四川",
            "guizhou": "贵州",
            "yunnan": "云南",
            "xizang": "西藏",
            "shanxi2": "陕西",
            "gansu": "甘肃",
            "qinghai": "青海",
            "ningxia": "宁夏",
            "xinjiang": "新疆"
        }
        for prov_en, prov_cn in province_map.items():
            try:
                total_sales = 0
                if prov_en == "beijing":
                    model = CAR_PROVINCE_MODELS.get("beijing")
                    if model: total_sales += model.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                elif prov_en == "shanghai":
                    model = CAR_PROVINCE_MODELS.get("shanghai")
                    if model: total_sales += model.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                elif prov_en == "tianjin":
                    model = CAR_PROVINCE_MODELS.get("tianjin")
                    if model: total_sales += model.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                elif prov_en == "chongqing":
                    model = CAR_PROVINCE_MODELS.get("chongqing")
                    if model: total_sales += model.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                elif prov_en == "shanxi2":
                    model = CAR_PROVINCE_MODELS.get("xian")
                    if model: total_sales += model.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                elif prov_en == "sichuan":
                    model = CAR_PROVINCE_MODELS.get("chengdu")
                    if model: total_sales += model.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                elif prov_en == "guangdong":
                    model1 = CAR_PROVINCE_MODELS.get("guangzhou")
                    model2 = CAR_PROVINCE_MODELS.get("shenzhen")
                    if model1: total_sales += model1.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                    if model2: total_sales += model2.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                elif prov_en == "zhejiang":
                    model = CAR_PROVINCE_MODELS.get("hangzhou")
                    if model: total_sales += model.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                elif prov_en == "jiangxi":
                    model = CAR_PROVINCE_MODELS.get("nanchang")
                    if model: total_sales += model.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                elif prov_en == "jiangsu":
                    model1 = CAR_PROVINCE_MODELS.get("nanjing")
                    model2 = CAR_PROVINCE_MODELS.get("suzhou")
                    if model1: total_sales += model1.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                    if model2: total_sales += model2.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                elif prov_en == "hubei":
                    model = CAR_PROVINCE_MODELS.get("wuhan")
                    if model: total_sales += model.objects.aggregate(total=Sum('salevolume'))['total'] or 0
                province_sales.append({
                    "name": prov_cn,
                    "value": total_sales
                })
            except Exception as e:
                province_sales.append({
                    "name": prov_cn,
                    "value": 0
                })
        return province_sales

    @staticmethod
    def weighted_predict(history, months=6):
        history_valid = [x for x in history if x >= 1]
        n = len(history_valid)
        if n < 3:
            return [round(history_valid[-1])] * months if history_valid else [0] * months
        min_val = min(history_valid)
        max_val = max(history_valid)
        season = [1.2, 0.9, 1.1, 1.4, 1.2, 1.16]
        weights = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40][-n:]
        weights = np.array(weights) / sum(weights)
        weighted_base = sum(v * w for v, w in zip(history_valid, weights))
        x = np.arange(n)
        y = np.array(history_valid)
        slope = np.polyfit(x, y, 1)[0]
        preds = []
        for i in range(months):
            sea = season[i % 6]
            trend = slope * (i + 1) * 0.95
            rand = np.random.uniform(0.96, 1.04)
            val = (weighted_base + trend) * sea * rand
            val = max(min_val * 0.75, min(max_val * 1.25, val))
            preds.append(round(val))
        return preds

    @staticmethod
    def brand_weighted_predict(history, months=6):
        history_valid = [x for x in history if x >= 0]
        n = len(history_valid)
        if n < 3:
            return [round(history_valid[-1])] * months if history_valid else [0] * months
        min_val = min(history_valid)
        max_val = max(history_valid)
        season = [1.08, 1.03, 1.05, 1.09, 1.06, 1.04]
        weights = [0.12, 0.18, 0.22, 0.24, 0.26, 0.38][-n:]
        weights = np.array(weights) / np.sum(weights)
        weighted_base = np.sum(np.array(history_valid) * weights)
        x = np.arange(n)
        y = np.array(history_valid, dtype=np.float64)
        slope = np.polyfit(x, y, 1)[0]
        slope = np.clip(slope, -max_val * 0.05, max_val * 0.10)
        preds = []
        for i in range(months):
            sea = season[i % 6]
            trend = slope * (i + 1) * 0.6
            rand = np.random.uniform(0.92, 1.08)
            val = (weighted_base + trend) * sea * rand
            val = max(min_val * 0.85, min(max_val * 1.3, val))
            preds.append(round(val))
        return preds

    @staticmethod
    def get_top10_sales_forecast(limit=10):
        top_cars = CarInformation.objects.all().order_by('-salevolume')[:limit]
        history_months = ['5月前', '4月前', '3月前', '2月前', '1月前', '本月']
        future_months = ['1个月后', '2个月后', '3个月后', '4个月后', '5个月后', '6个月后']
        result = {'history_months': history_months, 'future_months': future_months, 'cars': []}
        for car in top_cars:
            history_sales = CarDataAnalysis.get_car_sales_history(car.carname)
            forecast_sales = CarDataAnalysis.weighted_predict(history_sales)
            result['cars'].append({
                'car_name': f"{car.brand} {car.carname}",
                'history_sales': history_sales,
                'forecast_sales': forecast_sales
            })
        return result

    @staticmethod
    def get_top10_brands_forecast(limit=10):
        top_brands = CarInformation.objects.values('brand').annotate(total=Sum('salevolume')).order_by('-total')[:limit]
        history_months = ['5月前', '4月前', '3月前', '2月前', '1月前', '本月']
        future_months = ['1个月后', '2个月后', '3个月后', '4个月后', '5个月后', '6个月后']
        result = {'history_months': history_months, 'future_months': future_months, 'brands': []}
        for item in top_brands:
            brand = item['brand']
            history_sales = CarDataAnalysis.get_brand_sales_history(brand)
            forecast_sales = CarDataAnalysis.brand_weighted_predict(history_sales)
            result['brands'].append({
                'brand_name': brand,
                'history_sales': history_sales,
                'forecast_sales': forecast_sales
            })
        return result

    @staticmethod
    def get_total_sales(city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        return model.objects.aggregate(total=Sum('salevolume'))['total'] or 0

    @staticmethod
    def get_car_count(city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        return model.objects.count() or 0

    @staticmethod
    def get_new_energy_rate(city="all", month="0"):
        model = CarDataAnalysis.get_model_by_params(city, month)
        new_types = ['纯电动', '插电式混合动力', '增程式', '油电混合']
        total = model.objects.count()
        return round((model.objects.filter(energytype__in=new_types).count() / total) * 100, 1) if total else 0

    @staticmethod
    def get_avg_monthly_sales(city="all", month="0"):
        total = CarDataAnalysis.get_total_sales(city, month)
        return round(total / 12) if total else 0

                                                                
    @staticmethod
    def get_bubble_chart_data(city="all", month="0", limit=30):
        """
        气泡图数据：X轴为价格，Y轴为销量，气泡大小代表市场份额
        返回适合echarts气泡图的数据格式
        """
        model = CarDataAnalysis.get_model_by_params(city, month)
        cars = model.objects.all().order_by('-salevolume')[:limit]

        bubble_data = []
        total_sales = model.objects.aggregate(total=Sum('salevolume'))['total'] or 1

        for car in cars:
            try:
                            
                price_str = car.price.strip('[]').split(',')
                if len(price_str) >= 2:
                    min_price = float(price_str[1])
                            
                    if min_price <= 0 or min_price > 500:
                        continue
                else:
                    continue

                sales = car.salevolume
                                           
                market_share = sales / total_sales
                bubble_size = 10 + (market_share * 50) ** 0.5 * 15
                bubble_size = min(max(bubble_size, 12), 55)

                                
                energy_color_map = {
                    '纯电动': '#10b981',      
                    '插电式混合动力': '#3b82f6',      
                    '汽油': '#ef4444',      
                    '柴油': '#f59e0b',      
                    '油电混合': '#8b5cf6',      
                    '增程式': '#06b6d4',      
                }
                color = energy_color_map.get(car.energytype, '#64748b')

                bubble_data.append({
                    'name': f"{car.brand} {car.carname}",
                    'brand': car.brand,
                    'price': round(min_price, 1),
                    'sales': sales,
                    'energy_type': car.energytype,
                    'car_img': car.carimg,
                    'value': [round(min_price, 1), sales, bubble_size],
                    'itemStyle': {'color': color}
                })
            except:
                continue

        return {
            'bubble_data': bubble_data,
            'total_sales': total_sales
        }

                                                                            
    @staticmethod
    def get_sunburst_chart_data(city="all", month="0", top_brands=8, top_cars_per_brand=5):
        """
        旭日图数据：多层结构
        第一层：品牌（按销量排序）
        第二层：该品牌下的车型（按销量排序）
        第三层：可选，展示销量数值
        """
        model = CarDataAnalysis.get_model_by_params(city, month)

                  
        brand_sales = model.objects.values('brand').annotate(
            total_sales=Sum('salevolume')
        ).order_by('-total_sales')[:top_brands]

        sunburst_data = []

        for brand_item in brand_sales:
            brand_name = brand_item['brand']
            brand_total_sales = brand_item['total_sales']

                       
            cars = model.objects.filter(brand=brand_name).order_by('-salevolume')[:top_cars_per_brand]

            children = []
            for car in cars:
                children.append({
                    'name': car.carname,
                    'value': car.salevolume,
                    'itemStyle': {'borderRadius': 6},
                    'tooltip': {
                        'formatter': f"{car.carname}<br/>销量: {car.salevolume} 台<br/>价格: {car.price}"
                    }
                })

                      
            brand_obj = CarBrand.objects.filter(brand=brand_name).first()
            brand_img = brand_obj.brand_img if brand_obj else ""

            sunburst_data.append({
                'name': brand_name,
                'value': brand_total_sales,
                'brand_img': brand_img,
                'children': children,
                'itemStyle': {'borderRadius': 8}
            })

        return sunburst_data
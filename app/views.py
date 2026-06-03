import datetime
import random
from datetime import datetime, timedelta
import re
import string
import os
from reportlab.platypus import KeepTogether
import numpy as np
from PIL import Image
from wordcloud import WordCloud
from snownlp import SnowNLP
import jieba
from pypinyin import lazy_pinyin
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse
from .models import User, CarInformation, CarBrand, SpiderCarComment
import matplotlib
import matplotlib.pyplot as plt
import xlwt
from django.contrib import messages
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from app.models import CAR_MONTH_MODELS, CAR_CITY_MODELS, CAR_CITY_NAMES, CarInformationTwoMonth,\
    CarInformationThreeMonth, CarInformationFourMonth, CarInformationFiveMonth,\
    CarInformationBeijing, CarInformationChengdu, CarInformationChongqing, CarInformationGuangzhou,\
    CarInformationHangzhou, CarInformationNanchang, CarInformationNanjing, CarInformationShanghai,\
    CarInformationShenzhen, CarInformationSuzhou, CarInformationTianjin, CarInformationWuhan, CarInformationXian
from app.recommendation import get_car_recommendations, get_popular_cars
from app.utils import errorResponse, getChangeSelfInfoData
from app.utils.car_data_analysis import CarDataAnalysis
from .AI import main, getText, checklen
from . import ai_assistant
from .models import (
    CarInformationOneMonth,
    CarComment
)
import logging
import json
import subprocess
import threading

matplotlib.use('Agg')
logger = logging.getLogger(__name__)
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
FONT_CN = 'STSong-Light'
FONT_EN = 'Times-Roman'
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            User.objects.get(username=username, password=password)
            request.session['username'] = username
            return redirect('/app/home')
        except:
            return errorResponse.errorResponse(request, '用户名或密码错误')

def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirmPassword = request.POST.get('confirmPassword')
        if not all([username, password, confirmPassword]):
            return errorResponse.errorResponse(request, '不允许为空值')
        if password != confirmPassword:
            return errorResponse.errorResponse(request, '两次密码不一致')
        try:
            User.objects.get(username=username)
            return errorResponse.errorResponse(request, '该账号已存在')
        except User.DoesNotExist:
            User.objects.create(username=username, password=password)
            return redirect('/app/login')
    return errorResponse.errorResponse(request, '该账号已存在')

def logOut(request):
    request.session.flush()
    return redirect('/app/login')

def home(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    popular_cars = get_popular_cars(top_n=6)
    old_car_names = set(CarInformationOneMonth.objects.values_list('carname', flat=True))
    latest_cars = CarInformation.objects.all()
    new_cars = []
    for car in latest_cars:
        if car.carname not in old_car_names:
            new_cars.append(car)
    new_recommend_cars = new_cars[:6]
    BASE_DIR = settings.BASE_DIR
    STATS_DIR = os.path.join(BASE_DIR, 'data_total')
    STATS_FILE = os.path.join(STATS_DIR, 'stats.json')
    if request.GET.get('update_stats') == '1':
        car_models = [
            CarInformation,
            CarInformationOneMonth,
            CarInformationTwoMonth,
            CarInformationThreeMonth,
            CarInformationFourMonth,
            CarInformationFiveMonth,
            CarInformationBeijing,
            CarInformationChengdu,
            CarInformationChongqing,
            CarInformationGuangzhou,
            CarInformationHangzhou,
            CarInformationNanchang,
            CarInformationNanjing,
            CarInformationShanghai,
            CarInformationShenzhen,
            CarInformationSuzhou,
            CarInformationTianjin,
            CarInformationWuhan,
            CarInformationXian,
        ]
        all_car_names = set()
        for model in car_models:
            names = model.objects.values_list('carname', flat=True)
            all_car_names.update(names)
        total_unique_cars = len(all_car_names)
        total_brands = CarBrand.objects.count()
        spider_comments = SpiderCarComment.objects.count()
        user_comments = CarComment.objects.count()
        total_comments = spider_comments + user_comments
        total_data_rows = 0
        for model in car_models:
            total_data_rows += model.objects.count()
        total_data_rows += total_comments
        stats_data = {
            "total_unique_cars": total_unique_cars,
            "total_brands": total_brands,
            "total_comments": total_comments,
            "total_data_rows": total_data_rows
        }
        if not os.path.exists(STATS_DIR):
            os.makedirs(STATS_DIR)
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=4)
        messages.success(request, "✅ 平台统计数据已更新完成！")
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            stats = json.load(f)
    except:
        stats = {
            "total_unique_cars": 0,
            "total_brands": 0,
            "total_comments": 0,
            "total_data_rows": 0
        }
    return render(request, 'home.html', {
        'userInfo': userInfo,
        'popular_cars': popular_cars,
        'new_recommend_cars': new_recommend_cars,
        **stats,
    })

def changeSelfInfo(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    if request.method == 'POST':
        getChangeSelfInfoData.changeSelfInfo(username, request.POST, request.FILES)
        userInfo = User.objects.get(username=username)
        return redirect('/app/home')
    return render(request, 'changeSelfInfo.html', {
        'userInfo': userInfo,
    })

def changePassword(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    if request.method == 'POST':
        res = getChangeSelfInfoData.changePassword(userInfo, request.POST)
        if res:
            return errorResponse.errorResponse(request, res)
        else:
            return redirect('/app/home')
    return render(request, 'changePassword.html', {
        'userInfo': userInfo,
    })

def car_sales_analysis(request):
    username = request.session.get('username')
    userInfo = None
    if username:
        try:
            userInfo = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
    selected_city = request.GET.get('city', 'all')
    selected_month = request.GET.get('month', '0')
    if selected_city != 'all':
        selected_month = '0'
    month_options = CarDataAnalysis.get_month_options()
    city_options = CarDataAnalysis.get_city_options()
    show_forecast = (selected_city == 'all' and selected_month == '0')
    brand_sales = CarDataAnalysis.get_top_brands_by_sales(limit=10, city=selected_city, month=selected_month)
    top_car_list = CarDataAnalysis.get_top_cars_by_sales(limit=10, city=selected_city, month=selected_month)
    energy_sales = CarDataAnalysis.get_sales_by_energy_type(city=selected_city, month=selected_month)
    energy_comparison = CarDataAnalysis.get_new_energy_vs_traditional(city=selected_city, month=selected_month)
    total_sales = CarDataAnalysis.get_total_sales(city=selected_city, month=selected_month)
    total_cars = CarDataAnalysis.get_car_count(city=selected_city, month=selected_month)
    new_energy_rate = CarDataAnalysis.get_new_energy_rate(city=selected_city, month=selected_month)
    top_car_data = CarDataAnalysis.get_top_selling_cars(limit=1, city=selected_city, month=selected_month)
    if top_car_data['car_names']:
        top_car_name = top_car_data['car_names'][0]
        top_car_sales = top_car_data['sales'][0]
    else:
        top_car_name = "暂无"
        top_car_sales = 0
    sales_forecast = None
    brand_forecast = None
    if show_forecast:
        sales_forecast = CarDataAnalysis.get_top10_sales_forecast(limit=10)
        brand_forecast = CarDataAnalysis.get_top10_brands_forecast(limit=10)
    bubble_chart_data = CarDataAnalysis.get_bubble_chart_data(
        city=selected_city,
        month=selected_month,
        limit=30
    )
    return render(request, 'car_sales_analysis.html', {
        'userInfo': userInfo,
        'brand_sales': brand_sales,
        'top_car_list': top_car_list,
        'sales_forecast': sales_forecast,
        'brand_forecast': brand_forecast,
        'energy_sales': energy_sales,
        'energy_comparison': energy_comparison,
        'total_sales': total_sales,
        'total_cars': total_cars,
        'new_energy_rate': f"{new_energy_rate}%",
        'top_car_name': top_car_name,
        'top_car_sales': top_car_sales,
        'selected_city': selected_city,
        'selected_month': selected_month,
        'month_options': month_options,
        'city_options': city_options,
        'show_forecast': show_forecast,
        'bubble_chart_data': bubble_chart_data,
    })

def car_market_analysis(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    selected_city = request.GET.get('city', 'all')
    selected_month = request.GET.get('month', '0')
    if selected_city != 'all':
        selected_month = '0'
    show_map_and_trend = (selected_city == 'all' and selected_month == '0')
    market_share = CarDataAnalysis.get_manufacturer_market_share(city=selected_city, month=selected_month)
    price_distribution = CarDataAnalysis.get_price_range_distribution(city=selected_city, month=selected_month)
    model_distribution = CarDataAnalysis.get_car_model_distribution(city=selected_city, month=selected_month)
    market_trends = CarDataAnalysis.get_recent_market_trends(city=selected_city, month=selected_month)
    brand_imgs = market_share.get('brand_imgs', [])
    city_options = CarDataAnalysis.get_city_options()
    month_options = CarDataAnalysis.get_month_options()
    city_sales_map = []
    monthly_new_car_trend = {}
                
    price_boxplot = {}
    if show_map_and_trend:
        city_sales_map = CarDataAnalysis.get_city_sales_for_map()
        monthly_new_car_trend = CarDataAnalysis.get_monthly_new_car_trend()

                        
    price_boxplot = CarDataAnalysis.get_price_boxplot_data(city=selected_city, month=selected_month)

    return render(request, 'car_market_analysis.html', {
        'userInfo': userInfo,
        'market_share': market_share,
        'price_distribution': price_distribution,
        'model_distribution': model_distribution,
        'market_trends': market_trends,
        'brand_imgs': brand_imgs,
        'city_sales_map': json.dumps(city_sales_map),
        'monthly_new_car_trend': monthly_new_car_trend,
        'show_map_and_trend': show_map_and_trend,
        'selected_city': selected_city,
        'selected_month': selected_month,
        'city_options': city_options,
        'month_options': month_options,
        'price_boxplot': price_boxplot,      
        'price_boxplot_json': json.dumps(price_boxplot),                 
    })

def car_list(request):
    username = request.session.get('username')
    userInfo = None
    if username:
        try:
            userInfo = User.objects.get(username=username)
        except:
            pass

    city_filter = request.GET.get('city', 'all')
    month_filter = request.GET.get('month', '0')
    brand_filter = request.GET.get('brand', '')
    brand_initial = request.GET.get('brand_initial', '')              
    energy_filter = request.GET.get('energy', '')
    model_filter = request.GET.get('model', '')
    keyword_filter = request.GET.get('keyword', '')
    sort = request.GET.get('sort', 'sale')
    price_filter = request.GET.get('price', '')

                            
    CAR_TYPE_MAPPING = {
        '轿车': ['微型车', '小型车', '紧凑型车', '中型车', '中大型车'],
        'SUV': ['小型SUV', '紧凑型SUV', '中型SUV', '中大型SUV', '大型SUV'],
        'MPV': ['小型MPV', '紧凑型MPV', '中型MPV', '中大型MPV', '大型MPV'],
        '跑车': [],
        '微面': [],
        '轻客': [],
        '卡车': ['轻卡', '皮卡', '微卡']
    }
                    
    ALL_MAIN_CAR_TYPES = list(CAR_TYPE_MAPPING.keys())

    from datetime import datetime
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    CAR_MONTH_NAMES = {}
    for i in range(6):
        year = current_year
        month = current_month - 1 - i
        while month <= 0:
            year -= 1
            month += 12
        CAR_MONTH_NAMES[str(i)] = f"{year}年{month:02d}月"

    if city_filter != 'all':
        month_filter = '0'
    if city_filter == 'all':
        CarModel = CAR_MONTH_MODELS.get(month_filter, CarInformation)
    else:
        CarModel = CAR_CITY_MODELS.get(city_filter, CarInformation)

    city_name = CAR_CITY_NAMES.get(city_filter, "全国")
    month_name = CAR_MONTH_NAMES.get(month_filter, "")

    cars = CarModel.objects.all()

                      
    if brand_filter:
        cars = cars.filter(brand=brand_filter)

                                                             
    if energy_filter:
                                         
        if energy_filter == "新能源":
            cars = cars.filter(energytype__in=["纯电动", "增程式", "插电式混合动力"])
        else:
            cars = cars.filter(energytype=energy_filter)
                                                                     

    if keyword_filter:
        cars = cars.filter(
            Q(brand__icontains=keyword_filter) | Q(carname__icontains=keyword_filter)
        )

                               
    if model_filter:
                                       
        if model_filter in CAR_TYPE_MAPPING:
            sub_models = CAR_TYPE_MAPPING[model_filter]
            if sub_models:
                cars = cars.filter(carmodel__in=sub_models)
            else:
                                             
                cars = cars.filter(carmodel=model_filter)
                                     
        else:
            cars = cars.filter(carmodel=model_filter)

                     
                    
    if price_filter:
        filtered_ids = []
        price_pattern = re.compile(r'\d+\.?\d*')
                                         
                                      
        for car in cars:
            print(f"车型：{car.carname}, 价格：{car.price}")
            price_str = str(car.price)
            nums = price_pattern.findall(price_str)
            print(f"提取的数字：{nums}")
            if nums:
                nums = [float(n) for n in nums]
                min_p = min(nums)
                max_p = max(nums)
                avg_price = (min_p + max_p) / 2
                print(f"avg_price：{avg_price}")
                print(f"是否匹配50+：{avg_price >= 50}")

                      
            match = False
            if price_filter == "0-10" and avg_price <= 10:
                match = True
            elif price_filter == "10-15" and 10 <= avg_price <= 15:
                match = True
            elif price_filter == "15-20" and 15 <= avg_price <= 20:
                match = True
            elif price_filter == "20-25" and 20 <= avg_price <= 25:
                match = True
            elif price_filter == "25-30" and 25 <= avg_price <= 30:
                match = True
            elif price_filter == "30-40" and 30 <= avg_price <= 40:
                match = True
            elif price_filter == "50万以上" and avg_price >= 50:
                match = True

            if match:
                filtered_ids.append(car.id)

                                           
        if filtered_ids:
            cars = cars.filter(id__in=filtered_ids)
        else:
                                         
            print(f"价格筛选无匹配，price_filter={price_filter}, filtered_ids为空")
            cars = cars.none()

                       
    def get_avg_price(car):
        try:
            price_str = str(car.price)
            nums = re.findall(r'\d+\.?\d*', price_str)
            nums = [float(n) for n in nums]
            if len(nums) >= 2:
                return (min(nums) + max(nums)) / 2
            elif nums:
                return nums[0]
        except:
            pass
        return 0.0

    cars = list(cars)
    if sort == 'sale':
        cars.sort(key=lambda x: x.salevolume, reverse=True)
    elif sort == 'price':
        cars.sort(key=get_avg_price)

                   
    paginator = Paginator(cars, 12)
    page = request.GET.get('page', 1)
    try:
        cars_page = paginator.page(page)
    except PageNotAnInteger:
        cars_page = paginator.page(1)
    except EmptyPage:
        cars_page = paginator.page(paginator.num_pages)

                                                                                 
    from pypinyin import lazy_pinyin
    import string

               
    brand_list = list(CarModel.objects.values_list('brand', flat=True).distinct())

             
    def brand_sort_key(brand):
        first_char = brand[0] if brand else ''
        if first_char.isdigit() or (first_char.isascii() and first_char.isalpha()):
            return (0, brand.lower())
        else:
            pinyin = ''.join(lazy_pinyin(brand))
            return (1, pinyin)

    all_brands = sorted(brand_list, key=brand_sort_key)

                               
    from .models import CarBrand
    brand_logo_map = {}
    brand_objs = CarBrand.objects.filter(brand__in=all_brands)
    for b in brand_objs:
        brand_logo_map[b.brand] = b.brand_img

                        
    all_brands_with_logo = []
    for b in all_brands:
        all_brands_with_logo.append({
            'name': b,
            'logo': brand_logo_map.get(b, '')
        })

                          
    brand_groups = {}
    for c in string.ascii_uppercase:
        brand_groups[c] = []
    brand_groups['其他'] = []

    for brand in all_brands:
        first_char = brand[0] if brand else ''
        if first_char.isdigit():
            brand_groups['其他'].append({
                'name': brand,
                'logo': brand_logo_map.get(brand, '')
            })
        elif first_char.isascii() and first_char.isalpha():
            initial = first_char.upper()
            item = {'name': brand, 'logo': brand_logo_map.get(brand, '')}
            if initial in brand_groups:
                brand_groups[initial].append(item)
            else:
                brand_groups['其他'].append(item)
        else:
            pinyin = lazy_pinyin(brand)[0]
            if pinyin:
                initial = pinyin[0].upper()
                item = {'name': brand, 'logo': brand_logo_map.get(brand, '')}
                if initial in brand_groups:
                    brand_groups[initial].append(item)
                else:
                    brand_groups['其他'].append(item)
            else:
                brand_groups['其他'].append({
                    'name': brand,
                    'logo': brand_logo_map.get(brand, '')
                })

    brand_groups = {k: v for k, v in brand_groups.items() if v}
                                                                                

    all_energy_types = CarModel.objects.values_list('energytype', flat=True).distinct().order_by('energytype')
    all_car_models = CarModel.objects.values_list('carmodel', flat=True).distinct().order_by('carmodel')

    return render(request, 'car_list.html', {
        'userInfo': userInfo,
        'cars': cars_page,
        'page_obj': cars_page,
        'is_paginated': True,
        'paginator': paginator,

                     
        'all_brands': all_brands_with_logo,
        'brand_groups': brand_groups,
        'brand_initial': brand_initial,

        'all_energy_types': all_energy_types,
        'all_car_models': all_car_models,
        'all_main_car_types': ALL_MAIN_CAR_TYPES,
        'car_type_mapping': CAR_TYPE_MAPPING,
        'brand_filter': brand_filter,
        'energy_filter': energy_filter,
        'model_filter': model_filter,
        'keyword_filter': keyword_filter,
        'current_sort': sort,
        'city_filter': city_filter,
        'month_filter': month_filter,
        'city_name': city_name,
        'month_name': month_name,
        'CAR_CITY_NAMES': CAR_CITY_NAMES,
        'CAR_MONTH_NAMES': CAR_MONTH_NAMES,
        'price_filter': price_filter,
    })

def car_detail(request, car_id):
    username = request.session.get('username')
    userInfo = None
    if username:
        try:
            userInfo = User.objects.get(username=username)
        except:
            pass

          
    city_filter = request.GET.get('city', 'all')
    month_filter = request.GET.get('month', '0')
    if city_filter != 'all':
        month_filter = '0'
    if city_filter == 'all':
        CarModel = CAR_MONTH_MODELS.get(month_filter, CarInformation)
    else:
        CarModel = CAR_CITY_MODELS.get(city_filter, CarInformation)

    car = get_object_or_404(CarModel, id=car_id)
                                                             
    brand_icon = ""
    try:
                               
        car_brand = CarBrand.objects.get(brand=car.brand)
        brand_icon = car_brand.brand_img
    except CarBrand.DoesNotExist:
                       
        brand_icon = ""
                                                                   

    comments = CarComment.objects.filter(car_id=car_id).order_by('-id')
    user_comment = None
    if username:
        try:
            user = User.objects.get(username=username)
            user_comment = CarComment.objects.filter(user=user, car_id=car_id).first()
        except User.DoesNotExist:
            pass

            
    if request.method == 'POST':
        if not username:
            messages.error(request, '请先登录后再评论')
            return redirect('car_detail', car_id=car.id)
        score = request.POST.get('score')
        content = request.POST.get('content', '').strip()
        if not score or not content:
            messages.error(request, '评分和评论内容不能为空')
            return redirect('car_detail', car_id=car.id)
        try:
            user = User.objects.get(username=username)
            existing_comment = CarComment.objects.filter(user=user, car_id=car_id).first()
            if existing_comment:
                existing_comment.score = score
                existing_comment.content = content
                existing_comment.save()
                messages.success(request, '评论更新成功')
            else:
                main_car = CarInformation.objects.get(id=car_id)
                CarComment.objects.create(
                    user=user,
                    car=main_car,
                    score=score,
                    content=content
                )
                messages.success(request, '评论提交成功')
        except User.DoesNotExist:
            messages.error(request, '用户不存在，请重新登录')
        except Exception as e:
            messages.error(request, '评论提交失败，请稍后再试')
            print(f'评论提交失败 - 用户: {username}, 汽车: {car.id}, 错误: {str(e)}')
        return redirect('car_detail', car_id=car.id)

          
                      
    price_trend = []
    if request.GET.get('city') == 'all' and request.GET.get('month') == '0':

        def get_fixed_random_price(price_str, car_id, month_idx):
            nums = re.findall(r'\d+\.?\d*', str(price_str))
            nums = [float(n) for n in nums if n]

            if len(nums) >= 2:
                min_p = min(nums[0], nums[1])
                max_p = max(nums[0], nums[1])
            elif len(nums) == 1:
                min_p = max_p = nums[0]
            else:
                return None

                                      
            seed = hash(f"car_{car_id}_month_{month_idx}")
            random.seed(seed)

            fixed_price = round(random.uniform(min_p, max_p), 2)
                             
            random.seed()
            return fixed_price

        trend_models = [
            CarInformation,
            CarInformationOneMonth,
            CarInformationTwoMonth,
            CarInformationThreeMonth,
            CarInformationFourMonth,
            CarInformationFiveMonth,
        ]
        trend_labels = ['1月前', '2月前', '3月前', '4月前', '5月前', '6月前']

        for idx, model in enumerate(trend_models):
            try:
                car_obj = model.objects.filter(carname=car.carname).first()
                if car_obj:
                                            
                    fixed_price = get_fixed_random_price(car_obj.price, car_id, idx)
                else:
                    fixed_price = None
            except:
                fixed_price = None

            price_trend.append({
                'label': trend_labels[idx],
                'price': fixed_price
            })

          
    try:
        main_car_info = CarInformation.objects.get(id=car_id)
        recommended_cars = CarInformation.objects.filter(
            Q(brand=main_car_info.brand) | Q(energytype=main_car_info.energytype)
        ).exclude(id=car_id)[:4]
    except:
        recommended_cars = []

                                                                 
    radar_scores = {
        "brand_score": 0,              
        "sale_score": 0,               
        "warranty_score": 0,         
        "price_score": 0,             
        "total_score": 0             
    }

    try:
                 
        current_brand = car.brand
        current_sale = car.salevolume if car.salevolume else 0
        current_insure = car.insure or ""
        current_price = car.price or ""

                            
                                    
        from django.db.models import Sum                 

                     
        brand_cars = CarModel.objects.filter(brand=current_brand)
        current_brand_total = brand_cars.aggregate(total=Sum('salevolume'))['total'] or 0

                           
        all_brand_sales = CarModel.objects.values('brand')\
            .annotate(total_sale=Sum('salevolume'))\
            .values_list('total_sale', flat=True)

        all_brand_sales = [s for s in all_brand_sales if s]        
        if not all_brand_sales:
            max_brand_sale = 1
        else:
            max_brand_sale = max(all_brand_sales)

                              
        brand_score = (current_brand_total / max_brand_sale) * 100
        radar_scores["brand_score"] = round(min(brand_score, 100))         

                          
        car_max_sale = CarModel.objects.aggregate(max_sale=Max('salevolume'))['max_sale'] or 1
        sale_score = (current_sale / car_max_sale) * 100
        radar_scores["sale_score"] = round(min(sale_score, 100))

                          
                                    
        warranty_years = 0
        insure_text = str(current_insure).replace(" ", "").replace(" ", "")          

        year_match = re.search(r'(\d+)年', insure_text)
        mile_match = re.search(r'(\d+)万', insure_text)

              
        if year_match:
            warranty_years = int(year_match.group(1))
        elif mile_match:
            miles = int(mile_match.group(1))
                               
            warranty_years = miles * 3 / 10

                            
        if warranty_years <= 0:
                   
            radar_scores["warranty_score"] = 20
        elif warranty_years < 2:
                    
            radar_scores["warranty_score"] = 30
        elif warranty_years < 3:
                  
            radar_scores["warranty_score"] = 45
        elif warranty_years == 3:
                         
            radar_scores["warranty_score"] = 50
        elif warranty_years <= 4:
                  
            radar_scores["warranty_score"] = 65
        elif warranty_years <= 6:
                
            radar_scores["warranty_score"] = 80
        elif warranty_years <= 8:
                
            radar_scores["warranty_score"] = 90
        else:
                      
            radar_scores["warranty_score"] = 100

                           
                                                                    
        price_nums = re.findall(r'\d+\.?\d*', current_price)
        price_nums = [float(p) for p in price_nums]
        car_price = 0
        if len(price_nums) >= 2:
            car_price = (price_nums[0] + price_nums[1]) / 2
        elif price_nums:
            car_price = price_nums[0]

        all_prices = []
        for c in CarModel.objects.all():
            nums = re.findall(r'\d+\.?\d*', str(c.price))
            nums = [float(n) for n in nums]
            if nums:
                all_prices.append(sum(nums) / len(nums))

        if all_prices and car_price > 0:
            avg_price = sum(all_prices) / len(all_prices)

                                         
            ratio = car_price / avg_price           

            if ratio <= 0.5:
                                     
                score = 85
            elif ratio <= 0.8:
                                  
                score = 85 - (ratio - 0.5) / 0.3 * 5
            elif ratio <= 1.2:
                                      
                score = 80 - (ratio - 0.8) / 0.4 * 5
            elif ratio <= 2:
                                
                score = 75 - (ratio - 1.2) / 0.8 * 35
            else:
                                   
                score = max(20, 40 - (ratio - 2) * 10)

            radar_scores["price_score"] = round(score)
        else:
            radar_scores["price_score"] = 50
                                                               

                     
        radar_scores["total_score"] = round(
            radar_scores["brand_score"] * 0.2 +
            radar_scores["sale_score"] * 0.45 +
            radar_scores["warranty_score"] * 0.2 +
            radar_scores["price_score"] * 0.15
        )

    except Exception as e:
        print(f"雷达评分计算异常：{str(e)}")
        radar_scores = {
            "brand_score": 50,
            "sale_score": 50,
            "warranty_score": 50,
            "price_score": 50,
            "total_score": 50
        }
                                                          

    return render(request, 'car_detail.html', {
        'userInfo': userInfo,
        'car': car,
        'brand_icon': brand_icon,               
        'comments': comments,
        'user_comment': user_comment,
        'recommended_cars': recommended_cars,
        'price_trend': price_trend,
        'radar_scores': radar_scores,         
    })

def car_recommendations(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    gender = request.GET.get('gender', '')
    age_group = request.GET.get('age_group', '')
    job = request.GET.get('job', '')
    budget_group = request.GET.get('budget_group', '')
    brand_filter = request.GET.get('brand', '')
    energy_filter = request.GET.get('energy', '')
    model_filter = request.GET.get('model', '')
    price_filter = request.GET.get('price', '')
    CarModel = CarInformation
    user_rated_cars = []
    base_cars = CarModel.objects.all()
    if brand_filter:
        base_cars = base_cars.filter(brand=brand_filter)
    if energy_filter:
        if energy_filter == "传统燃油车":
            base_cars = base_cars.filter(energytype__in=["汽油", "柴油"])
        elif energy_filter == "新能源":
            base_cars = base_cars.filter(energytype__in=["纯电动", "插电混动", "增程式", "氢能源"])
    if model_filter:
        if model_filter == "轿车":
            base_cars = base_cars.filter(carmodel__in=["紧凑型车", "中型车", "中大型车", "小型车", "微型车", "豪华车"])
        elif model_filter == "SUV":
            base_cars = base_cars.filter(carmodel__in=["SUV", "紧凑型SUV", "中型SUV", "中大型SUV", "小型SUV"])
        elif model_filter == "MPV":
            base_cars = base_cars.filter(carmodel__in=["MPV", "紧凑型MPV", "中型MPV", "中大型MPV", "小型MPV"])
        elif model_filter == "跑车":
            base_cars = base_cars.filter(carmodel__in=["跑车"])
        elif model_filter == "微面":
            base_cars = base_cars.filter(carmodel__in=["微面"])
    if price_filter:
        import json
        filtered_ids = []
        for car in base_cars:
            try:
                                 
                price_list = json.loads(car.price)
                if isinstance(price_list, list):
                                      
                    price_list = sorted([float(p) for p in price_list])
                    min_p = price_list[0]
                    max_p = price_list[-1]
                    avg_price = (min_p + max_p) / 2
                else:
                    avg_price = float(price_list)
            except:
                try:
                    avg_price = float(car.price)
                except:
                    continue

                    
            if price_filter == "0-10" and avg_price <= 10:
                filtered_ids.append(car.id)
            elif price_filter == "10-15" and 10 < avg_price <= 15:
                filtered_ids.append(car.id)
            elif price_filter == "15-20" and 15 < avg_price <= 20:
                filtered_ids.append(car.id)
            elif price_filter == "20-25" and 20 < avg_price <= 25:
                filtered_ids.append(car.id)
            elif price_filter == "25-30" and 25 < avg_price <= 30:
                filtered_ids.append(car.id)
            elif price_filter == "30-40" and 30 < avg_price <= 40:
                filtered_ids.append(car.id)
            elif price_filter == "50万以上" and avg_price >= 50:
                filtered_ids.append(car.id)

        base_cars = base_cars.filter(id__in=filtered_ids) if filtered_ids else base_cars.none()
    allowed_ids = list(base_cars.values_list('id', flat=True))
    all_recommendations = []

                  
    recommended_results = get_car_recommendations(
        pre_filtered_cars=base_cars,
        gender=gender,
        age_group=age_group,
        job=job,
        budget_group=budget_group,
        price_filter=price_filter,
        top_n=100,
        return_reasons=True
    )

                      
    recommendation_data = []
    for item in recommended_results:
        car = item['car']
        if car.id in allowed_ids:
            recommendation_data.append({
                'car': car,
                'reasons': item.get('reasons', ['推荐车型'])
            })

    recommendation_data = recommendation_data[:12]

                         
    all_recommendations = [item['car'] for item in recommendation_data]
    recommendation_reasons = {item['car'].id: item['reasons'] for item in recommendation_data}
    all_brands = CarModel.objects.values_list('brand', flat=True).distinct().order_by('brand')
    all_energy_types = ["传统燃油车", "新能源"]
    all_car_models = ["轿车", "SUV", "MPV", "跑车", "微面"]
    return render(request, 'car_recommendations.html', {
        'userInfo': userInfo,
        'user_rated_cars': user_rated_cars,
        'recommended_cars': all_recommendations,
        'recommendation_reasons': recommendation_reasons,
        'has_ratings': len(user_rated_cars) > 0,

        'all_brands': all_brands,
        'all_energy_types': all_energy_types,
        'all_car_models': all_car_models,
        'brand_filter': brand_filter,
        'energy_filter': energy_filter,
        'model_filter': model_filter,
        'price_filter': price_filter,

        'gender': gender,
        'age_group': age_group,
        'job': job,
        'budget_group': budget_group,
    })

def car_comparison(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    city_filter = request.GET.get('city', 'all')
    month_filter = request.GET.get('month', '0')
    if city_filter != 'all':
        month_filter = '0'
    if city_filter == 'all':
        CarModel = CAR_MONTH_MODELS.get(month_filter, CarInformation)
    else:
        CarModel = CAR_CITY_MODELS.get(city_filter, CarInformation)
    car_ids = request.GET.getlist('car_id')
    selected_cars = []
    if car_ids:
        selected_cars = CarModel.objects.filter(id__in=car_ids)
    all_brands = CarModel.objects.values_list('brand', flat=True).distinct().order_by('brand')
    return render(request, 'car_comparison.html', {
        'userInfo': userInfo,
        'selected_cars': selected_cars,
        'all_brands': all_brands,
        'city_filter': city_filter,
        'month_filter': month_filter
    })

def get_cars_by_brand(request):
    brand = request.GET.get('brand', '')
    if brand:
        cars = CarInformation.objects.filter(brand=brand).values('id', 'carname')
        return JsonResponse(list(cars), safe=False)
    return JsonResponse([], safe=False)

def get_car_data(request):
    data_type = request.GET.get('type', '')
    if data_type == 'brand_sales':
        data = CarDataAnalysis.get_top_brands_by_sales()
    elif data_type == 'energy_distribution':
        data = CarDataAnalysis.get_energy_type_distribution()
    elif data_type == 'car_model_distribution':
        data = CarDataAnalysis.get_car_model_distribution()
    elif data_type == 'sales_by_energy':
        data = CarDataAnalysis.get_sales_by_energy_type()
    elif data_type == 'top_selling_cars':
        data = CarDataAnalysis.get_top_selling_cars()
    elif data_type == 'manufacturer_share':
        data = CarDataAnalysis.get_manufacturer_market_share()
    elif data_type == 'price_distribution':
        data = CarDataAnalysis.get_price_range_distribution()
    elif data_type == 'energy_comparison':
        data = CarDataAnalysis.get_new_energy_vs_traditional()
    elif data_type == 'market_trends':
        data = CarDataAnalysis.get_recent_market_trends()
    else:
        data = {'error': '未知的数据类型'}
    return JsonResponse(data)

def spider_management(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    return render(request, 'spider_management.html', {'userInfo': userInfo})

@csrf_exempt
def start_spider(request):
    if request.method == 'POST':
        try:
            crawl_count = 10
            try:
                body = json.loads(request.body.decode('utf-8'))
                crawl_count = int(body.get('crawl_count', 10))
                crawl_count = max(1, crawl_count)
            except:
                crawl_count = 10
            spider_thread = threading.Thread(target=run_spider_background, args=(crawl_count,))
            spider_thread.daemon = True
            spider_thread.start()
            return JsonResponse({'success': True, 'message': f'爬虫启动成功，将爬取前{crawl_count}名数据'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'启动失败: {str(e)}'})
    return JsonResponse({'success': False, 'message': '请求方法错误'})

@csrf_exempt
def import_spider_data(request):
    if request.method == 'POST':
        try:
            import_thread = threading.Thread(target=run_import_data)
            import_thread.daemon = True
            import_thread.start()
            return JsonResponse({'success': True, 'message': '数据更新已开始'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'更新失败: {str(e)}'})
    return JsonResponse({'success': False, 'message': '请求方法错误'})

spider_logs = []
spider_log_lock = threading.Lock()

def add_spider_log(message, log_type='info'):
    with spider_log_lock:
        timestamp = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        log_entry = {'timestamp': timestamp, 'message': message, 'type': log_type}
        spider_logs.append(log_entry)
        if len(spider_logs) > 500:
            spider_logs.pop(0)
        print(f"[{timestamp}] {message}")

@csrf_exempt
def get_spider_logs(request):
    if request.method == 'GET':
        try:
            last_index = int(request.GET.get('last_index', 0))
            with spider_log_lock:
                new_logs = spider_logs[last_index:] if last_index < len(spider_logs) else []
            return JsonResponse({
                'success': True,
                'logs': new_logs,
                'total_count': len(spider_logs)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'获取日志失败: {str(e)}'})
    return JsonResponse({'success': False, 'message': '请求方法错误'})

@csrf_exempt
def clear_spider_logs(request):
    if request.method == 'POST':
        with spider_log_lock:
            spider_logs.clear()
        return JsonResponse({'success': True, 'message': '日志已清空'})
    return JsonResponse({'success': False, 'message': '请求方法错误'})

def run_spider_background(crawl_count=10):
    try:
        add_spider_log(f"开始调用原始爬虫，目标爬取{crawl_count}条数据", 'info')
        import sys
        spider_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'spider')
        if spider_path not in sys.path:
            sys.path.append(spider_path)
        from spider.spiders import spider
        class LoggedSpider(spider):
            def __init__(self, crawl_count=10):
                super().__init__(crawl_count)
            def main(self, start_offset=0):
                self.current_count = 0
                current_offset = start_offset
                add_spider_log(f"开始爬取，目标数量: {self.crawl_count}条", 'info')
                while self.current_count < self.crawl_count:
                    remaining_count = self.crawl_count - self.current_count
                    request_count = min(100, remaining_count + 20)
                    params = {
                        'aid': 1839,
                        'app_name': 'auto_web_pc',
                        'count': request_count,
                        'month': '',
                        'new_energy_type': '',
                        'rank_data_type': 11,
                        'brand_id': '',
                        'price': '',
                        'manufacturer': '',
                        'outter_detail_type': '',
                        'nation': 0,
                        'offset': current_offset
                    }
                    add_spider_log(
                        f"第{(current_offset // 50) + 1}次API请求: offset={current_offset}, count={request_count}, 已爬取={self.current_count}/{self.crawl_count}条",
                        'info')
                    try:
                        import requests
                        response = requests.get(self.base_url, headers=self.header, params=params, timeout=30)
                        pageJson = response.json()
                        if 'data' not in pageJson or 'list' not in pageJson['data']:
                            add_spider_log(f"API返回数据格式异常: {pageJson}", 'error')
                            break
                        car_list = pageJson["data"]["list"]
                        if not car_list:
                            add_spider_log(f"没有更多数据可获取，停止爬取", 'warning')
                            break
                        add_spider_log(f"本次API返回{len(car_list)}条数据", 'info')
                        for index, car in enumerate(car_list):
                            if self.current_count >= self.crawl_count:
                                add_spider_log(f"已达到目标爬取数量{self.crawl_count}，停止爬取", 'success')
                                return
                            carData = []
                            car_name = car.get('series_name', '未知车型')
                            add_spider_log(f"正在爬取第{self.current_count + 1}条数据: {car_name}", 'info')
                            carData.append(car["brand_name"])
                            carData.append(car["series_name"])
                            carData.append(car["image"])
                            carData.append(car["count"])
                            price = []
                            price.append(car["max_price"])
                            price.append(car["min_price"])
                            carData.append(price)
                            carData.append(car["sub_brand_name"])
                            carNum = car["series_id"]
                            try:
                                from lxml import etree
                                infoHTML = requests.get(
                                    f"https://www.dongchedi.com/auto/params-carIds-x-{carNum}",
                                    headers=self.header, timeout=15
                                )
                                infoHTMLpath = etree.HTML(infoHTML.text)
                                try:
                                    carModel = infoHTMLpath.xpath("//div[@data-row-anchor='jb']/div[2]/div/text()")[0]
                                    carData.append(carModel)
                                except:
                                    carData.append("未知车型")
                                try:
                                    energyType = infoHTMLpath.xpath("//div[@data-row-anchor='fuel_form']/div[2]/div/text()")[0]
                                    carData.append(energyType)
                                except:
                                    carData.append("未知能源")
                                try:
                                    marketTime = infoHTMLpath.xpath("//div[@data-row-anchor='market_time']/div[2]/div/text()")[0]
                                    carData.append(marketTime)
                                except:
                                    carData.append("未知")
                                try:
                                    insure = infoHTMLpath.xpath("//div[@data-row-anchor='period']/div[2]/div/text()")[0]
                                    carData.append(insure)
                                except:
                                    carData.append("未知")
                            except:
                                carData.extend(["未知车型", "未知能源", "未知", "未知"])
                            add_spider_log(f"完整数据: {carData}", 'info')
                            self.save_to_csv(carData)
                            self.current_count += 1
                        current_offset += len(car_list)
                        if len(car_list) < request_count:
                            add_spider_log(f"返回数据不足，可能已达到数据源末尾", 'warning')
                            if self.current_count < self.crawl_count:
                                add_spider_log(f"目标{self.crawl_count}条，实际只获取到{self.current_count}条数据", 'warning')
                            break
                    except Exception as e:
                        add_spider_log(f"爬取过程中出错: {e}", 'error')
                        current_offset += 50
                        continue
                add_spider_log(f"本次爬取完成，共获取{self.current_count}条数据", 'success')
        spider_instance = LoggedSpider(crawl_count=crawl_count)
        spider_instance.main()
        if hasattr(spider_instance, 'current_count') and spider_instance.current_count > 0:
            add_spider_log(f"爬虫执行成功，共爬取{spider_instance.current_count}条数据", 'success')
            if hasattr(spider_instance, 'csv_path') and spider_instance.csv_path:
                csv_filename = os.path.basename(spider_instance.csv_path)
                add_spider_log(f"数据已保存到: {csv_filename}", 'success')
            else:
                add_spider_log("数据已保存到CSV文件", 'success')
        else:
            add_spider_log("爬虫执行失败或未获取到数据", 'error')
    except Exception as e:
        add_spider_log(f"爬虫运行错误: {e}", 'error')

def run_import_data():
    try:
        current_dir = os.getcwd()
        import_script_path = os.path.join(current_dir, 'spider', 'import_data.py')
        add_spider_log("开始更新数据库数据...", 'info')
        add_spider_log(f"导入脚本路径: {import_script_path}", 'info')
        if not os.path.exists(import_script_path):
            add_spider_log(f"导入脚本不存在: {import_script_path}", 'error')
            return
        venv_python = os.path.join(current_dir, 'venv', 'Scripts', 'python.exe')
        if os.path.exists(venv_python):
            python_cmd = venv_python
            add_spider_log(f"使用虚拟环境Python: {python_cmd}", 'info')
        else:
            python_cmd = 'python'
            add_spider_log("虚拟环境Python不存在，使用系统Python", 'warning')
        result = subprocess.run(
            [python_cmd, import_script_path],
            cwd=current_dir,
            timeout=300,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        add_spider_log(f"脚本执行返回码: {result.returncode}", 'info')
        if result.stdout:
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if line.strip():
                    if any(key in line for key in ['错误', 'Error', 'error']):
                        log_type = 'error'
                    elif any(key in line for key in ['成功', '完成', '新建', '更新']):
                        log_type = 'success'
                    else:
                        log_type = 'info'
                    add_spider_log(line, log_type)
        if result.stderr:
            error_lines = result.stderr.strip().split('\n')
            for line in error_lines:
                if line.strip():
                    add_spider_log(f"错误: {line}", 'error')
        if result.returncode == 0:
            add_spider_log("数据更新完成", 'success')
        else:
            add_spider_log(f"数据更新失败，返回码: {result.returncode}", 'error')
    except subprocess.TimeoutExpired:
        add_spider_log("数据更新超时（超过5分钟）", 'error')
    except Exception as e:
        add_spider_log(f"数据更新错误: {e}", 'error')

def generate_wordcloud_api(request):
    carname = request.GET.get('carname', '')
    if not carname:
        return JsonResponse({'code': 1, 'msg': '请选择车型'})
    try:
        comment_list = SpiderCarComment.objects.filter(carname=carname).values_list('content', flat=True)
        if not comment_list:
            return JsonResponse({'code': 1, 'msg': '该车型暂无评论数据'})

        stop_words = {
                     
            "的", "了", "是", "在", "和", "都", "很", "有", "不", "也", "就", "但",
            "啊", "吧", "吗", "呢", "呀", "哇", "哦", "哟", "唉", "啦", "罢了",
            "之", "乎", "者", "也", "其", "此", "彼", "于", "与", "及", "或",
                  
            "你", "我", "他", "她", "它", "我们", "你们", "他们", "她们", "它们",
            "自己", "本人", "别人", "人家", "大家", "有人",
                     
            "这", "那", "这里", "那里", "这边", "那边", "这个", "那个", "这样", "那样",
            "什么", "怎么", "如何", "为什么", "哪里", "哪些", "多少",
                    
            "没有", "可以", "还是", "非常", "特别", "十分", "极其", "有点", "好像",
            "其实", "然后", "但是", "可是", "不过", "而且", "并且", "另外",
            "总之", "因此", "所以", "因为", "由于", "虽然", "即使", "既然",
                   
            "一个", "一种", "一些", "一点", "一切", "所有", "全部", "各种",
                      
            "车", "车子", "车型", "辆车", "台车", "这款", "那款", "这车", "那车",
            "开", "坐", "买", "提", "看", "说", "用", "搞", "做", "让", "使", "叫",
            "感觉", "觉得", "认为", "以为", "看起来", "看上去"
        }
        neutral_words = {
                    
            "吉利", "比亚迪", "特斯拉", "大众", "丰田", "本田", "宝马", "奔驰", "奥迪", "萤火虫",
            "蔚来", "理想", "小鹏", "零跑", "哪吒", "问界", "极氪", "岚图", "高合",
            "长城", "哈弗", "魏牌", "欧拉", "奇瑞", "星途", "长安", "传祺", "红旗",
            "日产", "马自达", "斯巴鲁", "标致", "雪铁龙", "雷诺", "福特", "雪佛兰",
            "凯迪拉克", "林肯", "沃尔沃", "捷豹", "路虎", "保时捷", "宾利", "劳斯莱斯",
                   
            "星愿", "秦", "宋", "唐", "汉", "元", "海豚", "海豹", "Model3", "ModelY",
            "迈腾", "凯美瑞", "雅阁", "轩逸", "朗逸", "卡罗拉", "X3", "X5", "C级", "E级", "A4L", "A6L",
                  
            "高速", "市区", "城市", "郊区", "山路", "国道", "省道", "高架", "隧道",
            "起步", "超车", "变道", "转弯", "掉头", "停车", "倒车", "入库", "巡航",
                    
            "内饰", "外观", "动力", "空间", "配置", "刹车", "油门", "方向盘",
            "发动机", "电机", "电池", "底盘", "悬架", "变速箱", "轮胎", "轮毂",
            "车灯", "天窗", "座椅", "中控", "屏幕", "音响", "空调", "气囊",
                   
            "续航", "油耗", "电耗", "马力", "扭矩", "功率", "加速", "极速", "操控",
            "通过性", "舒适性", "稳定性", "风噪", "胎噪", "隔音",
                   
            "车机", "导航", "辅助驾驶", "自动泊车", "快充", "慢充", "四驱", "两驱",
            "雷达", "摄像头", "氛围灯", "无线充电", "座椅加热", "座椅通风"
        }
        positive_words = {
                  
            "好", "不错", "棒", "满意", "推荐", "超值", "给力", "舒服", "省心", "优秀",
            "喜欢", "值得", "完美", "好用", "稳定", "平顺", "安静", "漂亮", "大气",
                  
            "好开", "好坐", "轻松", "灵活", "好操控", "顺手", "稳", "丝滑", "好上手",
            "提速快", "加速猛", "响应快", "转向准", "刹车稳", "底盘稳", "隔音好",
                      
            "宽敞", "够用", "视野好", "颜值高", "精致", "高级", "用料足", "做工好",
            "上档次", "简约", "时尚", "耐看", "质感好", "座椅软", "包裹性好",
                   
            "智能", "方便", "实用", "齐全", "丰富", "清晰", "流畅", "续航实", "充电快",
            "功能全", "科技感强", "人性化", "安全", "靠谱",
                    
            "划算", "实惠", "良心", "性价比高", "服务好", "态度好", "专业", "及时",
            "贴心", "放心", "安心", "靠谱",
                  
            "超好", "极好", "太棒", "超赞", "大爱", "真香", "无敌", "一流", "顶尖", "给力"
        }
        negative_words = {
                  
            "差", "垃圾", "坑", "不值", "破", "费油", "抖动", "噪音大", "异响", "故障",
            "后悔", "失望", "慢", "卡顿", "漏油", "毛病", "吐槽", "差劲", "敷衍",
                  
            "难开", "笨重", "转向虚", "刹车软", "刹车硬", "顿挫", "窜车", "跑偏", "熄火",
            "起步肉", "加速慢", "操控差", "底盘散", "侧倾大", "滤震差", "颠",
                      
            "小", "拥挤", "压抑", "视野差", "丑", "廉价", "塑料感", "做工差", "缝隙大",
            "粗糙", "掉价", "座椅硬", "靠背塌",
                   
            "卡顿", "死机", "反应慢", "续航虚", "充电慢", "功能少", "减配", "简配",
            "不智能", "不好用", "逻辑乱", "雷达误报",
                  
            "漏水", "漏电", "烧机油", "亏电", "生锈", "起皮", "异味重", "胎噪大",
            "风噪大", "高频噪音", "小毛病多", "质量差", "易坏",
                    
            "贵", "溢价高", "不划算", "服务差", "态度差", "推诿", "慢", "拖延",
            "不专业", "坑人", "套路多",
                  
            "极差", "超差", "垃圾", "离谱", "恶心", "糟糕", "崩溃", "无语", "失望透顶"
        }

        positive_text = []
        negative_text = []
        neutral_text = []
        word_with_sentiment = []
        word_weight = {}
        pos_threshold = 0.6
        neg_threshold = 0.4

        for content in comment_list:
            if not content:
                continue
            content_str = str(content).strip()
            s = SnowNLP(content_str)
            score = s.sentiments

            if score >= pos_threshold:
                positive_text.append(content_str)
            elif score <= neg_threshold:
                negative_text.append(content_str)
            else:
                neutral_text.append(content_str)

            words = jieba.lcut(content_str)
            for word in words:
                word_stripped = word.strip()
                if word_stripped and word_stripped not in stop_words:
                    word_with_sentiment.append((word_stripped, score))
                    lower_word = word_stripped.lower()
                    if lower_word in positive_words:
                        word_weight[lower_word] = word_weight.get(lower_word, 0) + 3
                    elif lower_word in negative_words:
                        word_weight[lower_word] = word_weight.get(lower_word, 0) + 3
                    else:
                        word_weight[lower_word] = word_weight.get(lower_word, 0) + 1

              
        total = len(comment_list)
        positive_count = len(positive_text)
        negative_count = len(negative_text)
        neutral_count = len(neutral_text)
        positive_pct = round(positive_count / total * 100, 1) if total > 0 else 0
        negative_pct = round(negative_count / total * 100, 1) if total > 0 else 0
        neutral_pct = round(neutral_count / total * 100, 1) if total > 0 else 0

        sentiment_summary = {
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count,
            'total': total,
            'positive_pct': positive_pct,
            'negative_pct': negative_pct,
            'neutral_pct': neutral_pct,
        }
        words_text = " ".join([(word + " ") * weight for word, weight in word_weight.items()])
        base_dir = settings.BASE_DIR
        mask_path = os.path.join(base_dir, "static", "mask.jpg")
        save_dir = os.path.join(base_dir, "static", "wordCloud")
        os.makedirs(save_dir, exist_ok=True)
        mask = np.array(Image.open(mask_path)) if os.path.exists(mask_path) else None
        font_path = "C:/Windows/Fonts/simhei.ttf"

        def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
            lower_word = word.lower()
            if lower_word in neutral_words:
                return "#868686"
            if lower_word in positive_words:
                return "#E53E3E" if font_size > 50 else "#F56565"
            elif lower_word in negative_words:
                return "#2B6CB0" if font_size > 50 else "#4299E1"
            scores = [s for w, s in word_with_sentiment if w.lower() == lower_word]
            if not scores:
                return "#868686"
            avg_score = sum(scores) / len(scores)
            return "#E53E3E" if avg_score >= pos_threshold else "#2B6CB0" if avg_score <= neg_threshold else "#868686"

        wc = WordCloud(
            font_path=font_path, background_color="white", mask=mask,
            width=1200, height=800, max_words=300, max_font_size=120, min_font_size=12,
            color_func=color_func, collocations=False, random_state=42,
            prefer_horizontal=0.9, relative_scaling=0.6
        )
        wc.generate(words_text)
        safe_carname = carname.replace(" ", "_").replace("/", "_").replace("\\", "_")
        img_filename = f"wordcloud_sentiment_{safe_carname}.png"
        img_path = os.path.join(save_dir, img_filename)
        wc.to_file(img_path)
        wordcloud_img_url = f"/static/wordCloud/{img_filename}"

        return JsonResponse({
            'code': 0,
            'msg': '生成成功',
            'carname': carname,
            'wordcloud_url': wordcloud_img_url,
            'sentiment': sentiment_summary
        })

    except Exception as e:
        return JsonResponse({'code': 1, 'msg': f'生成失败：{str(e)}'})

def wordcloud(request):
    username = request.GET.get('username') or request.session.get('username')
    userInfo = None
    if username:
        try:
            userInfo = User.objects.get(username=username)
        except:
            pass
    carname = request.GET.get('carname', '')
    brand_filter = request.GET.get('brand', '')
    brand_initial = request.GET.get('brand_initial', '')         
    wordcloud_img_url = None
    error_msg = None
    sentiment_summary = None
    stop_words = {
        "的", "了", "是", "在", "和", "都", "很", "有", "不", "也", "就", "但",
        "啊", "吧", "吗", "呢", "呀", "哇", "哦", "哟", "唉", "啦", "罢了",
        "之", "乎", "者", "也", "其", "此", "彼", "于", "与", "及", "或",
        "你", "我", "他", "她", "它", "我们", "你们", "他们", "她们", "它们",
        "自己", "本人", "别人", "人家", "大家", "有人",
        "这", "那", "这里", "那里", "这边", "那边", "这个", "那个", "这样", "那样",
        "什么", "怎么", "如何", "为什么", "哪里", "哪些", "多少",
        "没有", "可以", "还是", "非常", "特别", "十分", "极其", "有点", "好像",
        "其实", "然后", "但是", "可是", "不过", "而且", "并且", "另外",
        "总之", "因此", "所以", "因为", "由于", "虽然", "即使", "既然",
        "一个", "一种", "一些", "一点", "一切", "所有", "全部", "各种",
        "车", "车子", "车型", "辆车", "台车", "这款", "那款", "这车", "那车",
        "开", "坐", "买", "提", "看", "说", "用", "搞", "做", "让", "使", "叫",
        "感觉", "觉得", "认为", "以为", "看起来", "看上去"
    }
    neutral_words = {
        "吉利", "比亚迪", "特斯拉", "大众", "丰田", "本田", "宝马", "奔驰", "奥迪", "萤火虫",
        "蔚来", "理想", "小鹏", "零跑", "哪吒", "问界", "极氪", "岚图", "高合",
        "长城", "哈弗", "魏牌", "欧拉", "奇瑞", "星途", "长安", "传祺", "红旗",
        "日产", "马自达", "斯巴鲁", "标致", "雪铁龙", "雷诺", "福特", "雪佛兰",
        "凯迪拉克", "林肯", "沃尔沃", "捷豹", "路虎", "保时捷", "宾利", "劳斯莱斯",
        "星愿", "秦", "宋", "唐", "汉", "元", "海豚", "海豹", "Model3", "ModelY",
        "迈腾", "凯美瑞", "雅阁", "轩逸", "朗逸", "卡罗拉", "X3", "X5", "C级", "E级", "A4L", "A6L",
        "高速", "市区", "城市", "郊区", "山路", "国道", "省道", "高架", "隧道",
        "起步", "超车", "变道", "转弯", "掉头", "停车", "倒车", "入库", "巡航",
        "内饰", "外观", "动力", "空间", "配置", "刹车", "油门", "方向盘",
        "发动机", "电机", "电池", "底盘", "悬架", "变速箱", "轮胎", "轮毂",
        "车灯", "天窗", "座椅", "中控", "屏幕", "音响", "空调", "气囊",
        "续航", "油耗", "电耗", "马力", "扭矩", "功率", "加速", "极速", "操控",
        "通过性", "舒适性", "稳定性", "风噪", "胎噪", "隔音",
        "车机", "导航", "辅助驾驶", "自动泊车", "快充", "慢充", "四驱", "两驱",
        "雷达", "摄像头", "氛围灯", "无线充电", "座椅加热", "座椅通风"
    }
    positive_words = {
        "好", "不错", "棒", "满意", "推荐", "超值", "给力", "舒服", "省心", "优秀",
        "喜欢", "值得", "完美", "好用", "稳定", "平顺", "安静", "漂亮", "大气",
        "好开", "好坐", "轻松", "灵活", "好操控", "顺手", "稳", "丝滑", "好上手",
        "提速快", "加速猛", "响应快", "转向准", "刹车稳", "底盘稳", "隔音好",
        "宽敞", "够用", "视野好", "颜值高", "精致", "高级", "用料足", "做工好",
        "上档次", "简约", "时尚", "耐看", "质感好", "座椅软", "包裹性好",
        "智能", "方便", "实用", "齐全", "丰富", "清晰", "流畅", "续航实", "充电快",
        "功能全", "科技感强", "人性化", "安全", "靠谱",
        "划算", "实惠", "良心", "性价比高", "服务好", "态度好", "专业", "及时",
        "贴心", "放心", "安心", "靠谱",
        "超好", "极好", "太棒", "超赞", "大爱", "真香", "无敌", "一流", "顶尖", "给力"
    }
    negative_words = {
        "差", "垃圾", "坑", "不值", "破", "费油", "抖动", "噪音大", "异响", "故障",
        "后悔", "失望", "慢", "卡顿", "漏油", "毛病", "吐槽", "差劲", "敷衍",
        "难开", "笨重", "转向虚", "刹车软", "刹车硬", "顿挫", "窜车", "跑偏", "熄火",
        "起步肉", "加速慢", "操控差", "底盘散", "侧倾大", "滤震差", "颠",
        "小", "拥挤", "压抑", "视野差", "丑", "廉价", "塑料感", "做工差", "缝隙大",
        "粗糙", "掉价", "座椅硬", "靠背塌",
        "卡顿", "死机", "反应慢", "续航虚", "充电慢", "功能少", "减配", "简配",
        "不智能", "不好用", "逻辑乱", "雷达误报",
        "漏水", "漏电", "烧机油", "亏电", "生锈", "起皮", "异味重", "胎噪大",
        "风噪大", "高频噪音", "小毛病多", "质量差", "易坏",
        "贵", "溢价高", "不划算", "服务差", "态度差", "推诿", "慢", "拖延",
        "不专业", "坑人", "套路多",
        "极差", "超差", "垃圾", "离谱", "恶心", "糟糕", "崩溃", "无语", "失望透顶"
    }
    if carname:
        try:
            comment_list = SpiderCarComment.objects.filter(carname=carname).values_list('content', flat=True)
            if not comment_list:
                error_msg = "该车型暂无评论数据"
            else:
                positive_text = []
                negative_text = []
                neutral_text = []
                word_with_sentiment = []
                word_weight = {}
                pos_threshold = 0.6
                neg_threshold = 0.4

                for content in comment_list:
                    if not content:
                        continue
                    content_str = str(content).strip()
                    s = SnowNLP(content_str)
                    score = s.sentiments

                    if score >= pos_threshold:
                        positive_text.append(content_str)
                    elif score <= neg_threshold:
                        negative_text.append(content_str)
                    else:
                        neutral_text.append(content_str)

                    words = jieba.lcut(content_str)
                    for word in words:
                        word_stripped = word.strip()
                        if word_stripped and word_stripped not in stop_words:
                            word_with_sentiment.append((word_stripped, score))
                            lower_word = word_stripped.lower()
                            if lower_word in positive_words:
                                word_weight[lower_word] = word_weight.get(lower_word, 0) + 3
                            elif lower_word in negative_words:
                                word_weight[lower_word] = word_weight.get(lower_word, 0) + 3
                            else:
                                word_weight[lower_word] = word_weight.get(lower_word, 0) + 1

                total = len(comment_list)
                positive_count = len(positive_text)
                negative_count = len(negative_text)
                neutral_count = len(neutral_text)

                positive_pct = round(positive_count / total * 100, 1) if total > 0 else 0
                negative_pct = round(negative_count / total * 100, 1) if total > 0 else 0
                neutral_pct = round(neutral_count / total * 100, 1) if total > 0 else 0

                sentiment_summary = {
                    'positive': positive_count,
                    'negative': negative_count,
                    'neutral': neutral_count,
                    'total': total,
                    'positive_pct': positive_pct,
                    'negative_pct': negative_pct,
                    'neutral_pct': neutral_pct,
                    'pos_threshold': pos_threshold,
                    'neg_threshold': neg_threshold,
                }

                words_text = ""
                for word, weight in word_weight.items():
                    words_text += (word + " ") * weight

                base_dir = settings.BASE_DIR
                mask_path = os.path.join(base_dir, "static", "mask.jpg")
                save_dir = os.path.join(base_dir, "static", "wordCloud")
                os.makedirs(save_dir, exist_ok=True)
                mask = np.array(Image.open(mask_path)) if os.path.exists(mask_path) else None
                font_path = "C:/Windows/Fonts/simhei.ttf"

                def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
                    lower_word = word.lower()
                    if lower_word in neutral_words:
                        return "#868686"
                    if lower_word in positive_words:
                        return "#E53E3E" if font_size > 50 else "#F56565"
                    elif lower_word in negative_words:
                        return "#2B6CB0" if font_size > 50 else "#4299E1"
                    scores = [s for (w, s) in word_with_sentiment if w.lower() == lower_word]
                    if not scores:
                        return "#868686"
                    avg_score = sum(scores) / len(scores)
                    if avg_score >= pos_threshold:
                        return "#E53E3E"
                    elif avg_score <= neg_threshold:
                        return "#2B6CB0"
                    else:
                        return "#868686"

                wc = WordCloud(
                    font_path=font_path, background_color="white", mask=mask,
                    width=1200, height=800, max_words=300, max_font_size=120, min_font_size=12,
                    color_func=color_func, collocations=False, random_state=42,
                    prefer_horizontal=0.9, relative_scaling=0.6
                )
                wc.generate(words_text)
                safe_carname = carname.replace(" ", "_").replace("/", "_").replace("\\", "_")
                img_filename = f"wordcloud_sentiment_{safe_carname}.png"
                img_path = os.path.join(save_dir, img_filename)
                wc.to_file(img_path)
                wordcloud_img_url = f"/static/wordCloud/{img_filename}"

        except Exception as e:
            error_msg = f"生成失败：{str(e)}"
    brand_list = list(CarInformation.objects.values_list('brand', flat=True).distinct())

    def brand_sort_key(brand):
        first_char = brand[0] if brand else ''
        if first_char.isdigit() or (first_char.isascii() and first_char.isalpha()):
            return (0, brand.lower())
        else:
            pinyin = ''.join(lazy_pinyin(brand))
            return (1, pinyin)

    all_brands_sorted = sorted(brand_list, key=brand_sort_key)
    brand_logo_map = {}
    brand_objs = CarBrand.objects.filter(brand__in=all_brands_sorted)
    for b in brand_objs:
        brand_logo_map[b.brand] = b.brand_img
    all_brands_with_logo = []
    for b in all_brands_sorted:
        all_brands_with_logo.append({
            'name': b,
            'logo': brand_logo_map.get(b, '')
        })

    brand_groups = {}
    for c in string.ascii_uppercase:
        brand_groups[c] = []
    brand_groups['其他'] = []

    for brand in all_brands_sorted:
        first_char = brand[0] if brand else ''
        if first_char.isdigit():
            brand_groups['其他'].append({'name': brand, 'logo': brand_logo_map.get(brand, '')})
        elif first_char.isascii() and first_char.isalpha():
            initial = first_char.upper()
            item = {'name': brand, 'logo': brand_logo_map.get(brand, '')}
            brand_groups[initial].append(item) if initial in brand_groups else brand_groups['其他'].append(item)
        else:
            pinyin = lazy_pinyin(brand)[0] if brand else ''
            if pinyin:
                initial = pinyin[0].upper()
                item = {'name': brand, 'logo': brand_logo_map.get(brand, '')}
                brand_groups[initial].append(item) if initial in brand_groups else brand_groups['其他'].append(item)
            else:
                brand_groups['其他'].append({'name': brand, 'logo': brand_logo_map.get(brand, '')})

    brand_groups = {k: v for k, v in brand_groups.items() if v}

    all_cars = CarInformation.objects.values('id', 'carname', 'brand').order_by('carname')
    if brand_filter:
        all_cars = all_cars.filter(brand=brand_filter)
    if brand_initial:
        if brand_initial == '其他':
            filtered_brands = [b['name'] for b in brand_groups.get('其他', [])]
            all_cars = all_cars.filter(brand__in=filtered_brands)
        else:
            filtered_brands = [b['name'] for b in brand_groups.get(brand_initial, [])]
            all_cars = all_cars.filter(brand__in=filtered_brands)

    return render(request, 'wordCloud.html', {
        'userInfo': userInfo,
        'carname': carname,
        'wordcloud_img_url': wordcloud_img_url,
        'error_msg': error_msg,
        'sentiment_summary': sentiment_summary,
        'all_brands': all_brands_with_logo,
        'brand_groups': brand_groups,
        'brand_filter': brand_filter,
        'brand_initial': brand_initial,

        'all_cars': all_cars,
    })

def largescreen(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    all_cars = CarInformation.objects.all()
    from django.db.models import Sum
    total_car_count = all_cars.count()
    total_sales = all_cars.aggregate(total=Sum('salevolume'))['total'] or 0
    total_brands = all_cars.values('brand').distinct().count()
    new_energy_cars = all_cars.filter(
        energytype__in=['纯电动', '插电式混合动力', '增程式', '油电混合']
    ).count()
    top_brand_data = all_cars.values('brand').annotate(total=Sum('salevolume')).order_by('-total').first()
    top_brand_display = top_brand_data['brand'] if top_brand_data else "暂无数据"
    top_model_data = all_cars.values('carmodel').annotate(total=Sum('salevolume')).order_by('-total').first()
    top_model_display = top_model_data['carmodel'] if top_model_data else "暂无数据"
    brand_sales_data = all_cars.values('brand').annotate(total=Sum('salevolume')).order_by('-total')[:8]
    brands = [f"NO.{i + 1} {item['brand']}" for i, item in enumerate(brand_sales_data)]
    brand_sales = [item['total'] for item in brand_sales_data]
    energy_sales_data = all_cars.values('energytype').annotate(total=Sum('salevolume')).order_by('-total')
    energy_types = [item['energytype'] for item in energy_sales_data]
    energy_sales = [item['total'] for item in energy_sales_data]
    energy_pie_data = [{'name': item['energytype'], 'value': item['total']} for item in energy_sales_data]
    energy_pie_json = json.dumps(energy_pie_data, ensure_ascii=False)
    model_data = all_cars.values('carmodel').annotate(total=Sum('salevolume')).order_by('-total')
    car_models = [item['carmodel'] for item in model_data]
    model_sales = [item['total'] for item in model_data]
    price_ranges = [
        ('5万以下', 0, 5), ('5-10万', 5, 10), ('10-15万', 10, 15),
        ('15-20万', 15, 20), ('20-30万', 20, 30), ('30-50万', 30, 50), ('50万以上', 50, 9999)
    ]
    price_pattern = re.compile(r'[-+]?\d*\.\d+|\d+')
    price_data = []
    for name, min_p, max_p in price_ranges:
        total_sale = 0
        for car in all_cars:
            try:
                price_str = str(car.price).strip()
                nums = price_pattern.findall(price_str)
                if len(nums) >= 2:
                    avg_price = (float(nums[0]) + float(nums[1])) / 2
                elif len(nums) == 1:
                    avg_price = float(nums[0])
                else:
                    continue
                if min_p <= avg_price < max_p:
                    total_sale += car.salevolume
            except:
                continue
        price_data.append({'name': name, 'value': total_sale})
    price_range_json = json.dumps(price_data, ensure_ascii=False)
    top10_cars = all_cars.order_by('-salevolume')[:10]
    x_axis_data = []
    sales_data = []
    avg_price_data = []
    for car in top10_cars:
        x_axis_data.append(car.carname)
        sales_data.append(car.salevolume)
        try:
            price_str = str(car.price).strip()
            nums = price_pattern.findall(price_str)
            if len(nums) >= 2:
                avg_p = (float(nums[0]) + float(nums[1])) / 2
            elif len(nums) == 1:
                avg_p = float(nums[0])
            else:
                avg_p = 0
        except:
            avg_p = 0
        avg_price_data.append(round(avg_p, 2))
    dual_axis_json = json.dumps({
        'x_axis': x_axis_data,
        'sales': sales_data,
        'avg_price': avg_price_data
    }, ensure_ascii=False)
    top_car_list = all_cars.order_by('-salevolume')[:20]
    return render(request, 'largescreen.html', {
        'top_car_list': top_car_list,
        'userInfo': userInfo,
        'total_car_count': total_car_count,
        'total_sales': total_sales,
        'total_brands': total_brands,
        'new_energy_cars': new_energy_cars,
        'top_brand_display': top_brand_display,
        'top_model_display': top_model_display,
        'brands': brands,
        'brand_sales': brand_sales,
        'energy_types': energy_types,
        'energy_sales': energy_sales,
        'car_models': car_models,
        'model_sales': model_sales,
        'energy_sales_data': energy_pie_json,
        'price_range_data': price_range_json,
        'dual_axis_data': dual_axis_json,
    })

def clustering(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    return render(request, 'clustering.html', {'userInfo': userInfo})

def api_clustering_data(request):
    import numpy as np
    import re
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    all_cars = CarInformation.objects.all()
    price_pattern = re.compile(r'[-+]?\d*\.\d+|\d+')
    car_data = []
    valid_cars = []
    for car in all_cars:
        try:
            price_str = str(car.price).strip()
            nums = price_pattern.findall(price_str)
            if len(nums) >= 2:
                avg_price = (float(nums[0]) + float(nums[1])) / 2
            elif len(nums) == 1:
                avg_price = float(nums[0])
            else:
                continue
            if avg_price <= 0:
                continue
            sale_num = int(car.salevolume) if str(car.salevolume).isdigit() else 0
            car_data.append([avg_price, sale_num])
            valid_cars.append({
                'name': car.carname,
                'brand': car.brand,
                'price': round(avg_price, 2),
                'sale': sale_num
            })
        except:
            continue
    if len(car_data) > 0:
        data_arr = np.array(car_data)
        prices = data_arr[:, 0]
        mean_p = np.mean(prices)
        std_p = np.std(prices)
        lower = mean_p - 3 * std_p
        upper = mean_p + 3 * std_p
        valid_mask = (prices >= lower) & (prices <= upper)
        clean_data = []
        clean_cars = []
        for idx in range(len(valid_cars)):
            if valid_mask[idx]:
                clean_data.append(car_data[idx])
                clean_cars.append(valid_cars[idx])
        car_data = clean_data
        valid_cars = clean_cars
    cluster_names = ["低端经济型", "中端家用型", "中高端舒适型", "高端豪华型"]
    scatter_series = []
    cluster_count = [0, 0, 0, 0]
    cluster_sale_sum = [0, 0, 0, 0]
    if len(car_data) >= 4:
        data_np = np.array(car_data)
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(data_np)
        kmeans = KMeans(n_clusters=4, random_state=42, n_init='auto')
        labels = kmeans.fit_predict(data_scaled)
        centers = kmeans.cluster_centers_[:, 0]
        sorted_idx = np.argsort(centers)
        label_map = {old: new for new, old in enumerate(sorted_idx)}
        for i in range(4):
            series_data = []
            for idx, car in enumerate(valid_cars):
                new_label = label_map[labels[idx]]
                if new_label == i:
                    series_data.append([
                        car['price'],
                        car['sale'],
                        f"{car['name']} | {car['brand']}"
                    ])
                    cluster_count[new_label] += 1
                    cluster_sale_sum[new_label] += car['sale']
            scatter_series.append({
                'name': cluster_names[i],
                'data': series_data,
                'type': 'scatter',
                'symbolSize': 12
            })
    else:
        series_data = []
        for car in valid_cars:
            series_data.append([
                car['price'],
                car['sale'],
                f"{car['name']} | {car['brand']}"
            ])
            cluster_count[0] += 1
            cluster_sale_sum[0] += car['sale']
        scatter_series.append({
            'name': "全部车型",
            'data': series_data,
            'type': 'scatter',
            'symbolSize': 12
        })
    return JsonResponse({
        'scatter_series': scatter_series,
        'cluster_names': cluster_names,
        'cluster_count': cluster_count,
        'cluster_sale_sum': cluster_sale_sum
    }, safe=False)

def car_warning(request):
    username = request.session.get('username')
    userInfo = User.objects.get(username=username)
    all_cars = CarInformation.objects.all()
    price_pattern = re.compile(r'[-+]?\d*\.\d+|\d+')
    car_list = []
    for car in all_cars:
        try:
            price_str = str(car.price).strip()
            nums = price_pattern.findall(price_str)
            if not nums:
                continue
            if len(nums) >= 2:
                avg_price = (float(nums[0]) + float(nums[1])) / 2
            else:
                avg_price = float(nums[0])
            sale = car.salevolume if car.salevolume >= 0 else 0
            if avg_price < 10:
                level = "入门级(10万以下)"
            elif 10 <= avg_price < 15:
                level = "经济型(10-15万)"
            elif 15 <= avg_price < 20:
                level = "家用型(15-20万)"
            elif 20 <= avg_price < 30:
                level = "中端型(20-30万)"
            elif 30 <= avg_price < 50:
                level = "中高端(30-50万)"
            else:
                level = "豪华型(50万以上)"
            car_list.append({
                "car": car,
                "avg_price": round(avg_price, 1),
                "level": level,
                "sale": sale
            })
        except:
            continue
    level_stats = {}
    for item in car_list:
        level = item["level"]
        if level not in level_stats:
            level_stats[level] = {"prices": [], "sales": []}
        level_stats[level]["prices"].append(item["avg_price"])
        level_stats[level]["sales"].append(item["sale"])
    for level in level_stats:
        prices = level_stats[level]["prices"]
        sales = level_stats[level]["sales"]
        level_stats[level]["avg_price"] = round(np.mean(prices), 1) if prices else 0
        level_stats[level]["median_sale"] = round(np.median(sales), 0) if sales else 0
        level_stats[level]["std_sale"] = round(np.std(sales), 0) if len(sales) >= 2 else 0
        level_stats[level]["count"] = len(sales)
    warning_list = []
    # 从请求参数读取用户自定义阈值（带默认值）
    try:
        PRICE_WARNING_LOW = float(request.GET.get('price_low', 0.7))
    except:
        PRICE_WARNING_LOW = 0.7
    try:
        PRICE_WARNING_HIGH = float(request.GET.get('price_high', 1.3))
    except:
        PRICE_WARNING_HIGH = 1.3
    try:
        SALE_WARNING_RATIO = float(request.GET.get('sale_ratio', 0.5))
    except:
        SALE_WARNING_RATIO = 0.5
    try:
        SALE_CRITICAL_RATIO = float(request.GET.get('sale_critical', 0.2))
    except:
        SALE_CRITICAL_RATIO = 0.2
    # 限制合理范围
    PRICE_WARNING_LOW = max(0.1, min(0.95, PRICE_WARNING_LOW))
    PRICE_WARNING_HIGH = max(1.05, min(3.0, PRICE_WARNING_HIGH))
    SALE_WARNING_RATIO = max(0.05, min(0.95, SALE_WARNING_RATIO))
    SALE_CRITICAL_RATIO = max(0.01, min(SALE_WARNING_RATIO, SALE_CRITICAL_RATIO))
    for item in car_list:
        car = item["car"]
        price = item["avg_price"]
        level = item["level"]
        sale = item["sale"]
        warnings = []
        stats = level_stats.get(level, {
            "avg_price": 0,
            "median_sale": 0,
            "std_sale": 0,
            "count": 0
        })
        level_avg_price = stats["avg_price"]
        median_sale = stats["median_sale"]
        car_count = stats["count"]
        if car_count < 3:
            continue
        if level_avg_price > 0:
            if price < level_avg_price * PRICE_WARNING_LOW:
                warnings.append(f"价格异常偏低({price:.1f}万)")
            elif price > level_avg_price * PRICE_WARNING_HIGH:
                warnings.append(f"价格虚高({price:.1f}万)")
        if median_sale > 0:
            if sale < median_sale * SALE_CRITICAL_RATIO:
                warnings.append(f"销量严重偏低({sale})")
            elif sale < median_sale * SALE_WARNING_RATIO:
                warnings.append(f"销量偏低({sale})")
        if warnings:
            warning_list.append({
                "id": car.id,
                "brand": car.brand,
                "carname": car.carname,
                "level": level,
                "salevolume": sale,
                "price": f"{price:.1f}万",
                "reason": " | ".join(warnings),
                "warning_level": len(warnings) + (1 if "严重" in "|".join(warnings) else 0)
            })
    warning_list.sort(key=lambda x: x["warning_level"], reverse=True)

    if "export" in request.GET:
        response = HttpResponse(content_type='application/vnd.ms-excel')
        file_name = f"汽车预警列表_{datetime.now().strftime('%Y%m%d%H%M')}.xls"
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        wb = xlwt.Workbook(encoding='utf-8')
        sheet = wb.add_sheet('预警列表', cell_overwrite_ok=True)
        header_style = xlwt.XFStyle()
        header_font = xlwt.Font()
        header_font.name = '微软雅黑'
        header_font.size = 11
        header_font.bold = True
        header_style.font = header_font
        header_pattern = xlwt.Pattern()
        header_pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        header_pattern.pattern_fore_colour = 13
        header_style.pattern = header_pattern
        header_alignment = xlwt.Alignment()
        header_alignment.horz = xlwt.Alignment.HORZ_CENTER
        header_alignment.vert = xlwt.Alignment.VERT_CENTER
        header_style.alignment = header_alignment
        data_style = xlwt.XFStyle()
        data_font = xlwt.Font()
        data_font.name = '微软雅黑'
        data_font.size = 10
        data_style.font = data_font
        data_style.alignment = header_alignment
        number_style = xlwt.XFStyle()
        number_style.font = data_font
        num_align = xlwt.Alignment()
        num_align.horz = xlwt.Alignment.HORZ_RIGHT
        num_align.vert = xlwt.Alignment.VERT_CENTER
        number_style.alignment = num_align
        warn_style = xlwt.XFStyle()
        warn_font = xlwt.Font()
        warn_font.name = '微软雅黑'
        warn_font.size = 10
        warn_font.colour_index = 2
        warn_style.font = warn_font
        warn_style.alignment = header_alignment
        headers = ['ID', '品牌', '车型', '级别', '销量', '价格', '预警原因']
        for i, h in enumerate(headers):
            sheet.write(0, i, h, header_style)
        widths = [8, 15, 28, 20, 12, 12, 50]
        for i, w in enumerate(widths):
            sheet.col(i).width = w * 256
        sheet.row(0).height_mismatch = True
        sheet.row(0).height = 32 * 20
        for row, item in enumerate(warning_list, 1):
            sheet.row(row).height_mismatch = True
            sheet.row(row).height = 24 * 20
            sheet.write(row, 0, item['id'], number_style)
            sheet.write(row, 1, item['brand'], data_style)
            sheet.write(row, 2, item['carname'], data_style)
            sheet.write(row, 3, item['level'], data_style)
            sheet.write(row, 4, item['salevolume'], number_style)
            sheet.write(row, 5, item['price'], data_style)
            sheet.write(row, 6, item['reason'], warn_style)
        wb.save(response)
        return response

    return render(request, 'car_warning.html', {
        'userInfo': userInfo,
        'warning_list': warning_list,
        'total': len(warning_list),
        'PRICE_WARNING_LOW': int((1 - PRICE_WARNING_LOW) * 100),
        'PRICE_WARNING_HIGH': int((PRICE_WARNING_HIGH - 1) * 100),
        'SALE_WARNING_RATIO': int(SALE_WARNING_RATIO * 100),
        'SALE_CRITICAL_RATIO': int(SALE_CRITICAL_RATIO * 100),
        'price_low_val': PRICE_WARNING_LOW,
        'price_high_val': PRICE_WARNING_HIGH,
        'sale_ratio_val': SALE_WARNING_RATIO,
        'sale_critical_val': SALE_CRITICAL_RATIO,
    })

@csrf_exempt
def api_car_warning_config(request):
    """AJAX API：接收自定义阈值参数，返回预警列表JSON"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            price_low = float(data.get('price_low', 0.7))
            price_high = float(data.get('price_high', 1.3))
            sale_ratio = float(data.get('sale_ratio', 0.5))
            sale_critical = float(data.get('sale_critical', 0.2))
        except:
            return JsonResponse({'code': 1, 'msg': '参数错误'})
    elif request.method == 'GET':
        try:
            price_low = float(request.GET.get('price_low', 0.7))
            price_high = float(request.GET.get('price_high', 1.3))
            sale_ratio = float(request.GET.get('sale_ratio', 0.5))
            sale_critical = float(request.GET.get('sale_critical', 0.2))
        except:
            return JsonResponse({'code': 1, 'msg': '参数错误'})
    else:
        return JsonResponse({'code': 1, 'msg': '不支持的请求方法'})

    # 限制合理范围
    price_low = max(0.1, min(0.95, price_low))
    price_high = max(1.05, min(3.0, price_high))
    sale_ratio = max(0.05, min(0.95, sale_ratio))
    sale_critical = max(0.01, min(sale_ratio, sale_critical))

    all_cars = CarInformation.objects.all()
    price_pattern = re.compile(r'[-+]?\d*\.\d+|\d+')
    car_list = []
    for car in all_cars:
        try:
            price_str = str(car.price).strip()
            nums = price_pattern.findall(price_str)
            if not nums:
                continue
            if len(nums) >= 2:
                avg_price = (float(nums[0]) + float(nums[1])) / 2
            else:
                avg_price = float(nums[0])
            sale = car.salevolume if car.salevolume >= 0 else 0
            if avg_price < 10:
                level = "入门级(10万以下)"
            elif 10 <= avg_price < 15:
                level = "经济型(10-15万)"
            elif 15 <= avg_price < 20:
                level = "家用型(15-20万)"
            elif 20 <= avg_price < 30:
                level = "中端型(20-30万)"
            elif 30 <= avg_price < 50:
                level = "中高端(30-50万)"
            else:
                level = "豪华型(50万以上)"
            car_list.append({
                "car_id": car.id,
                "brand": car.brand,
                "carname": car.carname,
                "avg_price": round(avg_price, 1),
                "level": level,
                "sale": sale
            })
        except:
            continue

    level_stats = {}
    for item in car_list:
        level = item["level"]
        if level not in level_stats:
            level_stats[level] = {"prices": [], "sales": []}
        level_stats[level]["prices"].append(item["avg_price"])
        level_stats[level]["sales"].append(item["sale"])
    for level in level_stats:
        prices = level_stats[level]["prices"]
        sales = level_stats[level]["sales"]
        level_stats[level]["avg_price"] = round(np.mean(prices), 1) if prices else 0
        level_stats[level]["median_sale"] = round(np.median(sales), 0) if sales else 0

    warning_list = []
    for item in car_list:
        car_id = item["car_id"]
        price = item["avg_price"]
        level = item["level"]
        sale = item["sale"]
        warnings = []
        stats = level_stats.get(level, {"avg_price": 0, "median_sale": 0, "count": 0})
        level_avg_price = stats["avg_price"]
        median_sale = stats["median_sale"]
        car_count = stats["count"]
        if car_count < 3:
            continue
        if level_avg_price > 0:
            if price < level_avg_price * price_low:
                warnings.append(f"价格异常偏低({price:.1f}万)")
            elif price > level_avg_price * price_high:
                warnings.append(f"价格虚高({price:.1f}万)")
        if median_sale > 0:
            if sale < median_sale * sale_critical:
                warnings.append(f"销量严重偏低({sale})")
            elif sale < median_sale * sale_ratio:
                warnings.append(f"销量偏低({sale})")
        if warnings:
            warning_list.append({
                "id": car_id,
                "brand": item["brand"],
                "carname": item["carname"],
                "level": level,
                "salevolume": sale,
                "price": f"{price:.1f}万",
                "reason": " | ".join(warnings),
            })
    warning_list.sort(key=lambda x: len(x["reason"]), reverse=True)

    return JsonResponse({
        'code': 0,
        'msg': '成功',
        'data': {
            'total': len(warning_list),
            'list': warning_list,
            'params': {
                'price_low': price_low,
                'price_high': price_high,
                'sale_ratio': sale_ratio,
                'sale_critical': sale_critical,
            }
        }
    })

def api_get_brands(request):
    brands = list(CarInformation.objects.values_list("brand", flat=True).distinct().order_by("brand"))
    return JsonResponse({"brands": brands}, safe=False)

def api_get_cars_by_brand(request):
    brand = request.GET.get("brand", "").strip()
    if not brand:
        return JsonResponse({"code": 1, "msg": "品牌不能为空", "cars": []}, safe=False)
    cars = list(CarInformation.objects.filter(brand__exact=brand).values("id", "carname", "brand"))
    return JsonResponse({"code": 0, "msg": "成功", "cars": cars}, safe=False)

def api_generate_wordcloud(request):
    carname = request.GET.get("carname", "")
    if not carname:
        return JsonResponse({"code": 1, "msg": "请选择车型"}, safe=False)
    try:
        stop_words = {
            "的", "了", "是", "你", "我", "在", "和", "都", "很", "有", "不", "也", "就", "但"
        }
        neutral_words = {"吉利", "比亚迪", "特斯拉", "大众", "丰田", "本田", "宝马", "奔驰", "奥迪"}
        positive_words = {"好", "不错", "棒", "满意", "推荐", "超值", "给力", "舒服"}
        negative_words = {"差", "垃圾", "坑", "不值", "破", "费油", "抖动", "噪音大"}
        comment_list = SpiderCarComment.objects.filter(carname=carname).values_list('content', flat=True)
        if not comment_list:
            return JsonResponse({"code": 1, "msg": "该车型暂无评论数据"}, safe=False)
        positive_text = []
        negative_text = []
        neutral_text = []
        word_with_sentiment = []
        word_weight = {}
        pos_threshold = 0.55
        neg_threshold = 0.45
        for content in comment_list:
            if not content:
                continue
            content_str = str(content)
            s = SnowNLP(content_str)
            score = s.sentiments
            if score > pos_threshold:
                positive_text.append(content_str)
            elif score < neg_threshold:
                negative_text.append(content_str)
            else:
                neutral_text.append(content_str)
            words = jieba.lcut(content_str)
            for word in words:
                word_stripped = word.strip()
                if word_stripped and word_stripped not in stop_words:
                    word_with_sentiment.append((word_stripped, score))
                    lower_word = word_stripped.lower()
                    if lower_word in positive_words:
                        word_weight[lower_word] = word_weight.get(lower_word, 0) + 2
                    else:
                        word_weight[lower_word] = word_weight.get(lower_word, 0) + 1
        words_text = ""
        for word, weight in word_weight.items():
            words_text += (word + " ") * weight
        base_dir = settings.BASE_DIR
        mask_path = os.path.join(base_dir, "static", "mask.jpg")
        save_dir = os.path.join(base_dir, "static", "wordCloud")
        os.makedirs(save_dir, exist_ok=True)
        mask = np.array(Image.open(mask_path)) if os.path.exists(mask_path) else None
        font_path = "C:/Windows/Fonts/simhei.ttf"
        def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
            lower_word = word.lower()
            if lower_word in neutral_words:
                return "#718096" if font_size > 60 else "#A0AEC0"
            if lower_word in positive_words:
                return "#E53E3E" if font_size > 50 else "#F56565"
            elif lower_word in negative_words:
                return "#2B6CB0" if font_size > 50 else "#4299E1"
            scores = [s for (w, s) in word_with_sentiment if w.lower() == lower_word]
            if not scores:
                return "#A0AEC0"
            avg_score = sum(scores) / len(scores)
            if avg_score > pos_threshold:
                return "#E53E3E" if font_size > 50 else "#F56565"
            elif avg_score < neg_threshold:
                return "#2B6CB0" if font_size > 50 else "#4299E1"
            else:
                return "#718096" if font_size > 60 else "#A0AEC0"
        wc = WordCloud(
            font_path=font_path,
            background_color="white",
            mask=mask,
            width=1200, height=800,
            max_words=300,
            max_font_size=120,
            min_font_size=12,
            color_func=color_func,
            collocations=False,
            random_state=42,
            prefer_horizontal=0.9,
            relative_scaling=0.6
        )
        wc.generate(words_text)
        safe_carname = carname.replace(" ", "_").replace("/", "_").replace("\\", "_")
        img_filename = f"wordcloud_sentiment_{safe_carname}.png"
        img_path = os.path.join(save_dir, img_filename)
        wc.to_file(img_path)
        wordcloud_url = f"/static/wordCloud/{img_filename}"
        return JsonResponse({
            "code": 0,
            "msg": "生成成功",
            "wordcloud_url": wordcloud_url,
            "carname": carname,
            "sentiment_summary": {
                "positive": len(positive_text),
                "negative": len(negative_text),
                "neutral": len(neutral_text),
                "total": len(comment_list)
            }
        })
    except Exception as e:
        return JsonResponse({"code": 1, "msg": f"生成失败：{str(e)}"}, safe=False)

def export_car_market_report(request):
    selected_city = request.GET.get('city', 'all')
    selected_month = request.GET.get('month', '0')

    if selected_city != 'all':
        selected_month = '0'

    market_share = CarDataAnalysis.get_manufacturer_market_share(city=selected_city, month=selected_month)
    price_distribution = CarDataAnalysis.get_price_range_distribution(city=selected_city, month=selected_month)
    model_distribution = CarDataAnalysis.get_car_model_distribution(city=selected_city, month=selected_month)
                
    price_boxplot = CarDataAnalysis.get_price_boxplot_data(city=selected_city, month=selected_month)

    city_sales_data = CarDataAnalysis.get_city_sales_list()

    city_name_map = {
        'all': '全国',
        'beijing': '北京',
        'shanghai': '上海',
        'guangzhou': '广州',
        'shenzhen': '深圳',
        'chengdu': '成都',
        'hangzhou': '杭州',
        'wuhan': '武汉',
        'nanchang': '南昌',
        'nanjing': '南京',
        'chongqing': '重庆',
        'suzhou': '苏州',
        'tianjin': '天津',
        'xian': '西安',
    }
    city_text = city_name_map.get(selected_city, selected_city)

    month_date_map = {
        '0': datetime.now().replace(day=1) - timedelta(days=1),
        '1': (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1),
        '2': ((datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(
            day=1) - timedelta(days=1),
        '3': (((datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(
            day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1),
        '4': ((((datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(
            day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1),
        '5': (((((datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(
            day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)),
    }
    month_datetime = month_date_map.get(selected_month, datetime.now())
    month_text = month_datetime.strftime("%Y年%m月")
    filter_text = f"当前筛选：{city_text} | {month_text}"

    show_map_and_trend = (selected_city == 'all' and selected_month == '0')

    response = HttpResponse(content_type='application/pdf')
    filename = f"汽车市场分析报告_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )
    story = []
    title_style = ParagraphStyle(
        'title', fontSize=18, fontName=FONT_CN, alignment=1, spaceAfter=20, bold=True
    )
    head_style = ParagraphStyle(
        'head', fontSize=14, fontName=FONT_CN, alignment=0, spaceBefore=15, spaceAfter=10,
        textColor=colors.HexColor('#2563eb')
    )
    subhead_style = ParagraphStyle(
        'subhead', fontSize=12, fontName=FONT_CN, alignment=0, spaceBefore=10, spaceAfter=8,
        textColor=colors.HexColor('#1e40af')
    )
    text_style = ParagraphStyle(
        'text', fontSize=10, fontName=FONT_CN, spaceAfter=1, alignment=1
    )
    car_name_style = ParagraphStyle(
        'car_name_wrap',
        fontSize=10,
        fontName=FONT_CN,
        alignment=1,
        leading=12
    )
    note_style = ParagraphStyle(
        'note', fontSize=9, fontName=FONT_CN, alignment=0, spaceAfter=6,
        textColor=colors.HexColor('#6b7280'), leading=14
    )

    story.append(Paragraph("汽车市场分析报告", title_style))
    story.append(Paragraph(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", text_style))
    story.append(Paragraph(filter_text, text_style))
    story.append(Spacer(1, 10))

                                                         
    story.append(Paragraph("一、制造商市场份额 TOP10", head_style))
    manufacturers = market_share.get('manufacturers', [])[:10]
    shares = market_share.get('market_shares', [])[:10]
    share_table = [["制造商", "市场占比(%)"]]
    for m, s in zip(manufacturers, shares):
        share_table.append([m, f"{s}%"])
    tbl = Table(share_table, colWidths=[8.5 * cm, 8.5 * cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(KeepTogether(tbl))         

                                                      
    story.append(Spacer(1, 20))
    story.append(Paragraph("二、车型分布", head_style))
    car_models = model_distribution.get('car_models', [])
    model_counts = model_distribution.get('counts', [])
    model_table = [["车型", "数量"]]
    for m, c in zip(car_models, model_counts):
        model_table.append([m, str(c)])
    mt = Table(model_table, colWidths=[8.5 * cm, 8.5 * cm])
    mt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(KeepTogether(mt))         

                      
    story.append(PageBreak())

                                                        
    story.append(Paragraph("三、价格区间分布", head_style))
    prices = price_distribution.get('price_ranges', [])
    counts = price_distribution.get('counts', [])
    price_table = [["价格区间", "车型数量"]]
    for p, c in zip(prices, counts):
        price_table.append([p, str(c)])
    pt = Table(price_table, colWidths=[8.5 * cm, 8.5 * cm])
    pt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(KeepTogether(pt))         

                                                             
    story.append(Spacer(1, 20))
    story.append(Paragraph("四、各能源类型价格分布统计（箱线图数据）", head_style))

            
    story.append(Paragraph(
        f"数据过滤说明：已自动过滤最低价格 ≤ 1万元（0元/异常标价）和 ≥ 500万元（天价限量车）的车型。"
        f"有效数据：{price_boxplot.get('active_count', 0)} 条，"
        f"已过滤异常数据：{price_boxplot.get('filtered_count', 0)} 条"
        f"（共 {price_boxplot.get('total_count', 0)} 条）",
        note_style
    ))
    story.append(Spacer(1, 8))

               
    boxplot_stats = price_boxplot.get('stats', {})

    if boxplot_stats:
                  
        sorted_categories = sorted(boxplot_stats.items(), key=lambda x: x[1].get('count', 0), reverse=True)

                             
        for energy_type, stat in sorted_categories:
            stats_table = [
                ["指标", "数值"],
                ["能源类型", energy_type],
                ["样本数", str(stat.get('count', 0))],
                ["最小值", f"{stat.get('min', 0):.1f} 万元"],
                ["下四分位数(Q1)", f"{stat.get('q1', 0):.1f} 万元"],
                ["中位数", f"{stat.get('median', 0):.1f} 万元"],
                ["上四分位数(Q3)", f"{stat.get('q3', 0):.1f} 万元"],
                ["最大值", f"{stat.get('max', 0):.1f} 万元"],
                ["平均值", f"{stat.get('mean', 0):.1f} 万元"],
            ]

                         
            box_tbl = Table(stats_table, colWidths=[8.5 * cm, 8.5 * cm])

                          
            box_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
                ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]))

            story.append(KeepTogether(box_tbl))            
            story.append(Spacer(1, 12))

                
        story.append(KeepTogether([
            Paragraph(
                "图表解读：",
                ParagraphStyle('legend_title', fontSize=10, fontName=FONT_CN, alignment=0, spaceBefore=6, spaceAfter=4)
            ),
            Paragraph(
                "• Q1（下四分位数）表示25%的车型价格低于此值；",
                note_style
            ),
            Paragraph(
                "• 中位数表示50%的车型价格低于此值，反映价格集中趋势；",
                note_style
            ),
            Paragraph(
                "• Q3（上四分位数）表示75%的车型价格低于此值；",
                note_style
            ),
            Paragraph(
                "• 箱体范围（Q1~Q3）越窄，说明该能源类型车型价格越集中；",
                note_style
            ),
            Paragraph(
                "• 均值与中位数差距大，说明存在极端值影响。",
                note_style
            ),
        ]))
    else:
        story.append(Paragraph("暂无箱线图统计数据", text_style))

                                                             
    if show_map_and_trend:
        story.append(PageBreak())
        story.append(Paragraph("五、近6个月新车型上市趋势", head_style))
        trend_data = CarDataAnalysis.get_monthly_new_car_trend()
        months = trend_data.get('months', [])
        cnts = trend_data.get('counts', [])
        trend_table = [["月份", "新上市车型数"]]
        for m, c in zip(months, cnts):
            trend_table.append([m, str(c)])
        tt = Table(trend_table, colWidths=[8.5 * cm, 8.5 * cm])
        tt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
            ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(KeepTogether(tt))         

                                                              
        story.append(Spacer(1, 20))
        story.append(Paragraph("六、重点城市销量统计", head_style))
        city_table = [["城市名称", "累计销量"]]
        for item in city_sales_data:
            city_table.append([item['name'], f"{item['sales']:,}"])
        city_tbl = Table(city_table, colWidths=[8.5 * cm, 8.5 * cm])
        city_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
            ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(KeepTogether(city_tbl))         

    doc.build(story)
    return response

def export_car_sales_report(request):
    selected_city = request.GET.get('city', 'all')
    selected_month = request.GET.get('month', '0')
    if selected_city != 'all':
        selected_month = '0'
    total_sales = CarDataAnalysis.get_total_sales(city=selected_city, month=selected_month)
    total_cars = CarDataAnalysis.get_car_count(city=selected_city, month=selected_month)
    top_car_data = CarDataAnalysis.get_top_selling_cars(limit=1, city=selected_city, month=selected_month)

    if top_car_data['car_names']:
        top_car_name = top_car_data['car_names'][0]
        top_car_sales = top_car_data['sales'][0]
    else:
        top_car_name = "暂无"
        top_car_sales = 0

    energy_comparison = CarDataAnalysis.get_new_energy_vs_traditional(city=selected_city, month=selected_month)
    energy_sales = CarDataAnalysis.get_sales_by_energy_type(city=selected_city, month=selected_month)
    brand_sales = CarDataAnalysis.get_top_brands_by_sales(limit=10, city=selected_city, month=selected_month)
    top_car_list = CarDataAnalysis.get_top_cars_by_sales(limit=10, city=selected_city, month=selected_month)
    try:
        new_energy_sales = int(energy_comparison['sales']['values'][0])
        old_energy_sales = int(energy_comparison['sales']['values'][1])
        new_energy_count = int(energy_comparison['counts']['values'][0])
        old_energy_count = int(energy_comparison['counts']['values'][1])
    except:
        new_energy_sales = 0
        old_energy_sales = 0
        new_energy_count = 0
        old_energy_count = 0

    all_sales = int(total_sales)
    new_energy_rate = f"{round(new_energy_sales / all_sales * 100, 1)}%" if all_sales > 0 else "0%"
    not_new_energy_rate = f"{round(100 - (new_energy_sales / all_sales * 100), 1)}%" if all_sales > 0 else "0%"
    brand_data_list = []
    if brand_sales:
        brand_data_list = [
            [item.get('brand', ''), f"{item.get('sales', 0):,}", f"{item.get('rate', 0)}%"]
            for item in brand_sales
        ]
    energy_types = energy_sales.get('energy_types', [])
    energy_sales_values = energy_sales.get('sales', [])
    energy_data_list = list(zip(energy_types, energy_sales_values))
    car_name_style = ParagraphStyle(
        'car_name_wrap',
        fontSize=10,
        fontName=FONT_CN,
        alignment=1,
        leading=12
    )
    car_data_list = [
        [Paragraph(item.get('car_name', ''), car_name_style), f"{item.get('sale_volume', 0):,}"]
        for item in top_car_list
    ]
    show_forecast = (selected_city == 'all' and selected_month == '0')
    brand_forecast = None
    sales_forecast = None
    if show_forecast:
        brand_forecast = CarDataAnalysis.get_top10_brands_forecast(limit=10)
        sales_forecast = CarDataAnalysis.get_top10_sales_forecast(limit=10)
    city_name_map = {
        'all': '全国',
        'beijing': '北京',
        'shanghai': '上海',
        'guangzhou': '广州',
        'shenzhen': '深圳',
        'chengdu': '成都',
        'hangzhou': '杭州',
        'wuhan': '武汉',
        'nanchang': '南昌',
        'nanjing': '南京',
    }
    city_text = city_name_map.get(selected_city, selected_city)
    month_date_map = {
        '0': datetime.now().replace(day=1) - timedelta(days=1),
        '1': (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1),
        '2': ((datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1),
        '3': (((datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1),
        '4': ((((datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1),
        '5': (((((datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1),
    }
    month_datetime = month_date_map.get(selected_month, datetime.now())
    month_text = month_datetime.strftime("%Y年%m月")

    filter_text = f"当前筛选：{city_text} | {month_text}"
    response = HttpResponse(content_type='application/pdf')
    filename = f"汽车销量分析报告_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )
    story = []
    title_style = ParagraphStyle(
        'title',
        fontSize=18,
        fontName=FONT_CN,
        alignment=1,
        spaceAfter=20,
        bold=True,
    )
    head_style = ParagraphStyle(
        'head',
        fontSize=14,
        fontName=FONT_CN,
        alignment=0,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.HexColor('#2563eb')
    )
    text_style = ParagraphStyle(
        'text',
        fontSize=10,
        fontName=FONT_CN,
        spaceAfter=1,
        alignment=1
    )

    story.append(Paragraph("汽车销量数据分析报告", title_style))
    story.append(Paragraph(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", text_style))
    story.append(Paragraph(filter_text, text_style))

    story.append(Spacer(1, 1))
    story.append(Paragraph("一、数据概览", head_style))

    data_overview = [
        ["指标", "数值", "指标", "数值"],
        ["累计总销量", f"{total_sales:,}", "在售车型总数", f"{total_cars:,}"],
        ["销量冠军车型", f"{top_car_name}", "冠军销量", f"{top_car_sales:,} 台"],
        ["新能源销量占比", new_energy_rate, "传统能源销量占比", not_new_energy_rate]
    ]
    table_overview = Table(data_overview, colWidths=[4.25 * cm, 4.25 * cm, 4.25 * cm, 4.25 * cm])
    table_overview.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(table_overview)
    story.append(Spacer(1, 10))
    story.append(Paragraph("二、品牌销量排行 TOP10", head_style))
    brand_table_data = [["品牌", "累计销量", "市场占比"]] + brand_data_list
    table_brand = Table(brand_table_data, colWidths=[8 * cm, 5 * cm, 4 * cm])
    table_brand.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(table_brand)
    story.append(Spacer(1, 10))
    story.append(Paragraph("三、车型销量排行 TOP10", head_style))
    car_table_data = [["车型", "累计销量"]] + car_data_list
    table_car = Table(car_table_data, colWidths=[12 * cm, 5 * cm])
    table_car.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('WORDWRAP', (0, 0), (-1, -1), True),
        ('ROWHEIGHT', (0, 0), (-1, -1), 22),
    ]))
    story.append(table_car)

    story.append(PageBreak())
    story.append(Paragraph("四、能源类型销量分析", head_style))
    energy_table_data = [["能源类型", "销量"]]
    for e_type, e_sale in energy_data_list:
        energy_table_data.append([e_type, f"{e_sale:,}"])
    table_energy = Table(energy_table_data, colWidths=[10 * cm, 7 * cm])
    table_energy.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(table_energy)
    story.append(Spacer(1, 20))
    story.append(Paragraph("五、新能源 vs 传统能源对比", head_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("1. 销量对比", head_style))
    sale_data = [
        ["能源类型", "销量"],
        ["新能源", f"{new_energy_sales:,}"],
        ["传统能源", f"{old_energy_sales:,}"]
    ]
    table_sale = Table(sale_data, colWidths=[8.5 * cm, 8.5 * cm])
    table_sale.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(table_sale)

    story.append(Spacer(1, 10))
    story.append(Paragraph("2. 车型数量对比", head_style))
    count_data = [
        ["能源类型", "车型数量"],
        ["新能源", f"{new_energy_count:,}"],
        ["传统能源", f"{old_energy_count:,}"]
    ]
    table_count = Table(count_data, colWidths=[8.5 * cm, 8.5 * cm])
    table_count.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
        ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(table_count)
    story.append(Spacer(1, 10))
    sale_drawing = Drawing(220, 140)
    sale_pie = Pie()
    sale_pie.x = 60
    sale_pie.y = 20
    sale_pie.width = 84
    sale_pie.height = 84
    sale_pie.data = [new_energy_sales, old_energy_sales]
    sale_pie.simpleLabels = 1
    sale_pie.slices.labelRadius = 0.0
    sale_pie.slices.strokeWidth = 1
    if len(sale_pie.slices) >= 1:
        sale_pie.slices[0].fillColor = colors.HexColor('#4e79a7')
    if len(sale_pie.slices) >= 2:
        sale_pie.slices[1].fillColor = colors.HexColor('#f28e2c')
    sale_drawing.add(sale_pie)
    sale_label = Paragraph("销量占比分布", text_style)

    count_drawing = Drawing(220, 140)
    count_pie = Pie()
    count_pie.x = 60
    count_pie.y = 20
    count_pie.width = 84
    count_pie.height = 84
    count_pie.data = [new_energy_count, old_energy_count]
    count_pie.simpleLabels = 1
    count_pie.slices.labelRadius = 0.0
    count_pie.slices.strokeWidth = 1
    if len(count_pie.slices) >= 1:
        count_pie.slices[0].fillColor = colors.HexColor('#4e79a7')
    if len(count_pie.slices) >= 2:
        count_pie.slices[1].fillColor = colors.HexColor('#f28e2c')
    count_drawing.add(count_pie)
    count_label = Paragraph("车型数量占比分布", text_style)

    legend = Paragraph("（蓝色 = 新能源，橙色 = 传统能源）", text_style)
    pie_row = Table(
        [[sale_drawing, count_drawing], [sale_label, count_label]],
        colWidths=[8.5 * cm, 8.5 * cm],
        hAlign='CENTER'
    )
    story.append(pie_row)
    story.append(Spacer(1, 5))
    story.append(legend)
    if show_forecast:
        story.append(PageBreak())
        story.append(Paragraph("六、销量预测数据（历史6期 + 未来6期）", head_style))

        story.append(Spacer(1, 10))
        story.append(Paragraph("1. TOP10 品牌销量预测", head_style))
        try:
            brand_history = brand_forecast.get('history_months', [])
            brand_future = brand_forecast.get('future_months', [])
            brand_headers = ['品牌'] + brand_history + ['预测1', '预测2', '预测3', '预测4', '预测5', '预测6']
            brand_table_data = [brand_headers]
            for brand_item in brand_forecast.get('brands', []):
                name = brand_item.get('brand_name', '未知')
                history = brand_item.get('history_sales', [0] * 6)
                future = brand_item.get('forecast_sales', [0] * 6)
                row = [name] + [f'{v:,}' for v in history] + [f'{v:,}' for v in future]
                brand_table_data.append(row)
            col_w = [17 / 13 * cm for _ in range(13)]
            brand_table = Table(brand_table_data, colWidths=col_w, repeatRows=1)
            brand_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
                ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            story.append(brand_table)
        except:
            story.append(Paragraph("品牌预测数据暂无", text_style))

        story.append(Spacer(1, 15))
        story.append(Paragraph("2. TOP10 车型销量预测", head_style))
        try:
            car_history = sales_forecast.get('history_months', [])
            car_future = sales_forecast.get('future_months', [])
            car_headers = ['车型'] + car_history + ['预测1', '预测2', '预测3', '预测4', '预测5', '预测6']
            car_table_data = [car_headers]
            for car_item in sales_forecast.get('cars', []):
                name = car_item.get('car_name', '未知')
                history = car_item.get('history_sales', [0] * 6)
                future = car_item.get('forecast_sales', [0] * 6)
                row = [Paragraph(name, car_name_style)] + [f'{v:,}' for v in history] + [f'{v:,}' for v in future]
                car_table_data.append(row)
            col_w2 = [2.2 * cm] + [1.2 * cm for _ in range(12)]
            car_table = Table(car_table_data, colWidths=col_w2, repeatRows=1)
            car_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
                ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('WORDWRAP', (0, 0), (0, -1), True),
                ('ROWHEIGHT', (0, 0), (-1, -1), 18),
            ]))
            story.append(car_table)
        except:
            story.append(Paragraph("车型预测数据暂无", text_style))
    else:
        story.append(PageBreak())
        story.append(Paragraph("提示：仅【全国 + 上个月】可导出销量预测数据", text_style))

    doc.build(story)
    return response

@csrf_exempt
def ai_chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'msg': '仅支持POST请求'})

    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()

        if not question:
            return JsonResponse({'code': 1, 'msg': '问题不能为空'})

                        
        db_result = ai_assistant.query_database_for_question(question)

        if db_result and db_result.get('can_answer'):
                               
            context = ai_assistant.format_context_for_ai(question, db_result)
            if context:
                text_list = []
                question_list = checklen(getText("user", context, text_list))
            else:
                question_list = checklen(getText("user", question, []))
        else:
                           
            text_list = []
            question_list = checklen(getText("user", question, text_list))

        appid = "bb2fc088"
        api_secret = "NzM2MTdiNmJjNDhjNTUyYTc0MTQwNTQw"
        api_key = "1fecfee0b9482cac4d476f955d22089d"
        domain = "spark-x"
        Spark_url = "wss://spark-api.xf-yun.com/v1/x1"
        answer = main(appid, api_key, api_secret, Spark_url, domain, question_list)

        if not answer.strip():
            return JsonResponse({'code': 500, 'msg': '模型返回结果为空，请重试'})

        return JsonResponse({
            'code': 0,
            'msg': 'success',
            'data': answer
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'code': 500, 'msg': f'服务异常：{str(e)}'})
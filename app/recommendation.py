import json
import os
import random

import django
from django.db.models import Avg

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '基于Django系统.settings')
django.setup()
from app.models import CarInformation


def get_car_real_price(price_field):
    try:
        price_list = json.loads(price_field)
        if isinstance(price_list, list) and len(price_list) >= 2:
            price_list = sorted([float(p) for p in price_list])
            min_p = price_list[0]
            max_p = price_list[-1]
            return (min_p + max_p) / 2
        elif len(price_list) == 1:
            return float(price_list[0])
    except:
        pass
    try:
        return float(price_field)
    except:
        return 9999


def get_price_range_from_filter(price_filter):
    if not price_filter:
        return None

    price_ranges = {
        "0-10": (0, 10),
        "10-15": (10, 15),
        "15-20": (15, 20),
        "20-25": (20, 25),
        "25-30": (25, 30),
        "30-50": (30, 50),
        "50万以上": (50, 9999)
    }
    return price_ranges.get(price_filter)


def get_budget_range(budget_group):
    budget_ranges = {
        "10以下": (0, 10),
        "10-20": (10, 20),
        "20-30": (20, 30),
        "30-50": (30, 50),
        "50万以上": (50, 9999)
    }
    return budget_ranges.get(budget_group, (0, 9999))


def is_car_in_price_range(car, min_price, max_price):
    car_price = get_car_real_price(car.price)
    return min_price <= car_price <= max_price


def get_car_type_scores(car, user_profile):
    score = 0
    type_info = []


    age_preferences = {
        "18-25": ['小型车', 'SUV', '紧凑型车', '微型车', '紧凑型SUV', '小型SUV'],
        "26-35": ['SUV', '中型车', '紧凑型车', '中型SUV'],
        "36-50": ['中型车', '中大型车', 'MPV', '中大型SUV', 'SUV'],
        "50+": ['SUV', 'MPV', '中大型车', '中型车', '中大型SUV',]
    }


    gender_preferences = {
        "男": {
            '高': ['SUV', '中大型车', '中大型SUV', '皮卡', '跑车', '大型SUV', '大型车'],
            '中': ['中型车', 'MPV', '中型SUV'],
            '低': ['紧凑型车', '小型车']
        },
        "女": {
            '高': ['小型车', 'SUV', '紧凑型车', '小型SUV', '紧凑型SUV'],
            '中': ['中型车', 'MPV'],
            '低': ['中大型车', '皮卡', '跑车']
        }
    }


    job_preferences = {
        "国家机关/党群组织/事业单位人员": ['中型车', '中大型车', 'SUV', 'MPV', '中大型SUV'],
        "专业技术人员": ['中型车', '紧凑型车', 'SUV', 'MPV', '中型SUV'],
        "办事人员和有关人员": ['紧凑型车', '中型车', 'SUV', '紧凑型SUV'],
        "商业/服务业人员": ['SUV', 'MPV', '紧凑型车', '中型车', '中型SUV'],
        "农林牧渔水利业生产人员": ['SUV', '紧凑型SUV', '皮卡', '中大型SUV', '中型SUV'],
        "生产制造/运输设备操作人员": ['SUV', '紧凑型车', '中型车', '皮卡', '中型SUV'],
        "军人": ['SUV', '中型车', '中大型车', '中型SUV', '中大型SUV'],
        "学生": ['小型车', '紧凑型车', 'SUV', '小型SUV', '紧凑型SUV'],
        "退休人员": ['中型车', 'SUV', 'MPV', '中大型车', '中大型SUV']
    }

    carmodel = car.carmodel


    if user_profile.get('age_group') in age_preferences:
        age_cars = age_preferences[user_profile['age_group']]
        if carmodel in age_cars:
            score += 20
            type_info.append('年龄匹配')


    if user_profile.get('gender') in gender_preferences:
        gender_prefs = gender_preferences[user_profile['gender']]
        if carmodel in gender_prefs.get('高', []):
            score += 25
            type_info.append('性别高度匹配')
        elif carmodel in gender_prefs.get('中', []):
            score += 15
            type_info.append('性别中度匹配')
        elif carmodel in gender_prefs.get('低', []):
            score += 5


    if user_profile.get('job') in job_preferences:
        job_cars = job_preferences[user_profile['job']]
        if carmodel in job_cars:
            score += 20
            type_info.append('职业匹配')


    budget_group = user_profile.get('budget_group')
    if budget_group:
        min_b, max_b = get_budget_range(budget_group)
        car_price = get_car_real_price(car.price)

        if min_b <= car_price <= max_b:
            score += 35
            type_info.append('预算完美匹配')

    return score, type_info


def recommend_by_user_profile(pre_filtered_cars, gender, age_group, job, budget_group,
                              price_filter=None, top_n=10):


    is_queryset = hasattr(pre_filtered_cars, 'annotate')


    if price_filter:
        min_price, max_price = get_price_range_from_filter(price_filter)
        if min_price is not None:
            if is_queryset:

                price_filtered_cars = [
                    car for car in pre_filtered_cars
                    if is_car_in_price_range(car, min_price, max_price)
                ]
            else:

                price_filtered_cars = [
                    car for car in pre_filtered_cars
                    if is_car_in_price_range(car, min_price, max_price)
                ]
            if not price_filtered_cars:

                return get_popular_cars_with_price_filter(
                    pre_filtered_cars, price_filter, top_n=top_n
                )
            pre_filtered_cars = price_filtered_cars
    elif budget_group:

        min_price, max_price = get_budget_range(budget_group)
        if is_queryset:
            price_filtered_cars = [
                car for car in pre_filtered_cars
                if is_car_in_price_range(car, min_price, max_price)
            ]
        else:
            price_filtered_cars = [
                car for car in pre_filtered_cars
                if is_car_in_price_range(car, min_price, max_price)
            ]
        if not price_filtered_cars:
            return get_popular_cars_with_price_filter(
                pre_filtered_cars, price_filter, top_n=top_n
            )
        pre_filtered_cars = price_filtered_cars


    user_profile = {
        'gender': gender,
        'age_group': age_group,
        'job': job,
        'budget_group': budget_group
    }


    scored_cars = []
    for car in pre_filtered_cars:
        score, type_info = get_car_type_scores(car, user_profile)


        try:
            avg_score = car.avg_score if hasattr(car, 'avg_score') and car.avg_score else 0
        except:
            avg_score = 0


        final_score = score + (avg_score * 5) + (min(car.salevolume or 0, 10000) / 500)

        scored_cars.append({
            'car': car,
            'profile_score': score,
            'avg_score': avg_score,
            'salevolume': car.salevolume or 0,
            'final_score': final_score
        })


    scored_cars.sort(key=lambda x: x['final_score'], reverse=True)


    result_cars = [item['car'] for item in scored_cars]


    if price_filter:
        min_price, max_price = get_price_range_from_filter(price_filter)
        result_cars = [
            car for car in result_cars
            if is_car_in_price_range(car, min_price, max_price)
        ]


    if len(result_cars) < top_n:

        popular = get_popular_cars(pre_filtered_cars, top_n=top_n * 2)
        exist_ids = {c.id for c in result_cars}
        for car in popular:
            if car.id not in exist_ids:

                if price_filter:
                    min_price, max_price = get_price_range_from_filter(price_filter)
                    if is_car_in_price_range(car, min_price, max_price):
                        result_cars.append(car)
                else:
                    result_cars.append(car)
            if len(result_cars) >= top_n:
                break


    if len(result_cars) > 3:
        top_cars = result_cars[:5]
        rest_cars = result_cars[5:]
        random.shuffle(rest_cars)
        result_cars = top_cars + rest_cars

    return result_cars[:top_n]


def get_popular_cars_with_price_filter(pre_filtered_cars, price_filter=None, top_n=10):
    if price_filter:
        min_price, max_price = get_price_range_from_filter(price_filter)
        if min_price is not None:

            scored_cars = []
            for car in pre_filtered_cars:
                try:
                    avg_score = car.avg_score if hasattr(car, 'avg_score') and car.avg_score else 0
                except:
                    avg_score = 0
                scored_cars.append({
                    'car': car,
                    'score': avg_score + (min(car.salevolume or 0, 10000) / 500)
                })
            scored_cars.sort(key=lambda x: x['score'], reverse=True)

            result = [item['car'] for item in scored_cars
                     if is_car_in_price_range(item['car'], min_price, max_price)]
            if result:
                return result[:top_n]


    return get_popular_cars(pre_filtered_cars, top_n=top_n)


def get_popular_cars(pre_filtered_cars=None, top_n=10):
    if pre_filtered_cars is None:
        pre_filtered_cars = CarInformation.objects.all()


    is_queryset = hasattr(pre_filtered_cars, 'annotate')

    if is_queryset:
        top_rated = pre_filtered_cars.annotate(
            avg_score=Avg('carcomment__score')
        ).order_by('-avg_score', '-salevolume')[:top_n]

        car_list = list(top_rated)
        if len(car_list) < top_n:
            all_sales = pre_filtered_cars.order_by('-salevolume')[:top_n]
            exist = {c.id for c in car_list}
            for car in all_sales:
                if car.id not in exist and len(car_list) < top_n:
                    car_list.append(car)
    else:

        scored_cars = []
        for car in pre_filtered_cars:
            try:
                avg_score = car.avg_score if hasattr(car, 'avg_score') and car.avg_score else 0
            except:
                avg_score = 0
            scored_cars.append({
                'car': car,
                'score': avg_score + (min(car.salevolume or 0, 10000) / 500)
            })
        scored_cars.sort(key=lambda x: x['score'], reverse=True)
        car_list = [item['car'] for item in scored_cars]

    return car_list


def get_car_recommendations(
    pre_filtered_cars=None,
    user_id=None,
    gender=None, age_group=None, job=None, budget_group=None,
    price_filter=None,
    top_n=10,
    return_reasons=False
):

    if pre_filtered_cars is None:
        pre_filtered_cars = CarInformation.objects.all()


    user_profile_complete = all([gender, age_group, job, budget_group])

    if user_profile_complete:

        result = recommend_by_user_profile_with_reasons(
            pre_filtered_cars,
            gender, age_group, job, budget_group,
            price_filter=price_filter,
            top_n=top_n
        ) if return_reasons else recommend_by_user_profile(
            pre_filtered_cars,
            gender, age_group, job, budget_group,
            price_filter=price_filter,
            top_n=top_n
        )
        return result
    else:

        result = get_popular_cars_with_price_filter(
            pre_filtered_cars, price_filter, top_n=top_n
        )

        if return_reasons:
            return [{'car': car, 'reasons': ['热门推荐车型']} for car in result]
        return result


def recommend_by_user_profile_with_reasons(pre_filtered_cars, gender, age_group, job, budget_group,
                                          price_filter=None, top_n=10):


    if price_filter:
        min_price, max_price = get_price_range_from_filter(price_filter)
        if min_price is not None:
            price_filtered_cars = [
                car for car in pre_filtered_cars
                if is_car_in_price_range(car, min_price, max_price)
            ]
            if not price_filtered_cars:
                return get_popular_cars_with_price_filter_and_reasons(
                    pre_filtered_cars, price_filter, top_n=top_n
                )
            pre_filtered_cars = price_filtered_cars
    elif budget_group:

        min_price, max_price = get_budget_range(budget_group)
        price_filtered_cars = [
            car for car in pre_filtered_cars
            if is_car_in_price_range(car, min_price, max_price)
        ]
        if not price_filtered_cars:
            return get_popular_cars_with_price_filter_and_reasons(
                pre_filtered_cars, price_filter, top_n=top_n
            )
        pre_filtered_cars = price_filtered_cars


    user_profile = {
        'gender': gender,
        'age_group': age_group,
        'job': job,
        'budget_group': budget_group
    }


    scored_cars = []
    for car in pre_filtered_cars:
        score, type_info = get_car_type_scores(car, user_profile)


        try:
            avg_score = car.avg_score if hasattr(car, 'avg_score') and car.avg_score else 0
        except:
            avg_score = 0


        final_score = score + (avg_score * 5) + (min(car.salevolume or 0, 10000) / 500)


        reasons = generate_recommendation_reasons(car, user_profile, type_info)

        scored_cars.append({
            'car': car,
            'profile_score': score,
            'avg_score': avg_score,
            'salevolume': car.salevolume or 0,
            'final_score': final_score,
            'reasons': reasons
        })


    scored_cars.sort(key=lambda x: x['final_score'], reverse=True)


    result_cars = [item['car'] for item in scored_cars]
    result_reasons = {item['car'].id: item['reasons'] for item in scored_cars}


    if price_filter:
        min_price, max_price = get_price_range_from_filter(price_filter)
        result_cars = [
            car for car in result_cars
            if is_car_in_price_range(car, min_price, max_price)
        ]


    if len(result_cars) < top_n:
        popular = get_popular_cars(pre_filtered_cars, top_n=top_n * 2)
        exist_ids = set(result_cars)
        for car in popular:
            if car.id not in exist_ids:
                if price_filter:
                    min_price, max_price = get_price_range_from_filter(price_filter)
                    if is_car_in_price_range(car, min_price, max_price):
                        result_cars.append(car)
                        result_reasons[car.id] = ['热门推荐车型']

            if len(result_cars) >= top_n:
                break


    if len(result_cars) > 3:
        top_cars = result_cars[:5]
        top_reasons = {c.id: result_reasons[c.id] for c in top_cars}
        rest_cars = result_cars[5:]
        rest_reasons = {c.id: result_reasons[c.id] for c in rest_cars}
        random.shuffle(rest_cars)
        result_cars = top_cars + rest_cars
        result_reasons.update(rest_reasons)


    final_result = []
    for car in result_cars[:top_n]:
        final_result.append({
            'car': car,
            'reasons': result_reasons.get(car.id, ['推荐车型'])
        })

    return final_result


def generate_recommendation_reasons(car, user_profile, type_info):
    reasons = []


    reason_mapping = {
        '年龄匹配': '适合您的年龄段',
        '性别高度匹配': '非常符合您的性别偏好',
        '性别中度匹配': '符合您的性别偏好',
        '职业匹配': '适合您的职业类型',
        '预算完美匹配': '完美符合您的预算'
    }

    for info in type_info:
        if info in reason_mapping:
            reasons.append(reason_mapping[info])


    if not reasons and any([user_profile.get('gender'), user_profile.get('age_group'),
                            user_profile.get('job'), user_profile.get('budget_group')]):
        reasons.append('综合推荐')


    budget_group = user_profile.get('budget_group')
    if budget_group and '预算完美匹配' not in type_info:
        min_price, max_price = get_budget_range(budget_group)
        car_price = get_car_real_price(car.price)
        if min_price <= car_price <= max_price:
            if '综合推荐' in reasons:
                reasons.remove('综合推荐')
            reasons.insert(0, f'价格在{min_price}-{max_price}万区间')

    return reasons if reasons else ['精选推荐']


def get_popular_cars_with_price_filter_and_reasons(pre_filtered_cars, price_filter=None, top_n=10):
    result = get_popular_cars_with_price_filter(pre_filtered_cars, price_filter, top_n)
    return [{'car': car, 'reasons': ['热门推荐车型']} for car in result]

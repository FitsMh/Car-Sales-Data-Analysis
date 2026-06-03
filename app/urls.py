from django.urls import path
from app import views
from app.views import export_car_market_report, generate_wordcloud_api

urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logOut/', views.logOut, name='logOut'),
    path('home/', views.home, name='home'),
    path('changeSelfInfo/', views.changeSelfInfo, name='changeSelfInfo'),
    path('changePassword/', views.changePassword, name='changePassword'),
    path('export/car/market/report/', export_car_market_report, name='export_car_market_report'),
    path('export/car_sales_report/', views.export_car_sales_report, name='export_car_sales_report'),

    path('car_sales_analysis/', views.car_sales_analysis, name='car_sales_analysis'),
    path('car_market_analysis/', views.car_market_analysis, name='car_market_analysis'),
    path('car_list/', views.car_list, name='car_list'),
    path('car_detail/<int:car_id>/', views.car_detail, name='car_detail'),
    path('car_recommendations/', views.car_recommendations, name='car_recommendations'),
    path('car_comparison/', views.car_comparison, name='car_comparison'),
    path('wordcloud/', views.wordcloud, name='wordcloud'),
    path('clustering/', views.clustering, name='clustering'),
    path('car_warning/', views.car_warning, name='car_warning'),
    path('api/wordcloud/brands/', views.api_get_brands, name='api_brands'),
    path('api/wordcloud/cars/', views.api_get_cars_by_brand, name='api_cars_by_brand'),
    path('api/wordcloud/generate/', generate_wordcloud_api, name='generate_wordcloud_api'),
    path('api/wordcloud/generate/', views.api_generate_wordcloud, name='api_generate_wordcloud'),
    path('api/clustering/data/', views.api_clustering_data, name='api_clustering_data'),
    path('api/car_data/', views.get_car_data, name='get_car_data'),
    path('api/cars-by-brand/', views.get_cars_by_brand, name='get_cars_by_brand'),
    path('api/ai_chat/', views.ai_chat_api, name='ai_chat_api'),
    path('api/car_warning/config/', views.api_car_warning_config, name='api_car_warning_config'),
    path('spider_management/', views.spider_management, name='spider_management'),
    path('api/spider/start/', views.start_spider, name='start_spider'),
    path('api/spider/import/', views.import_spider_data, name='import_spider_data'),
    path('api/spider/logs/', views.get_spider_logs, name='get_spider_logs'),
    path('api/spider/logs/clear/', views.clear_spider_logs, name='clear_spider_logs'),
]

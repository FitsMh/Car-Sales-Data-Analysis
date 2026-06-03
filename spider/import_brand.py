import os
import csv
import glob
import sys
import pandas as pd
from django.db import connection


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', '基于Django系统.settings')


try:
    import django

    django.setup()
    print("Django环境初始化成功")
except ImportError as e:
    print(f"Django导入失败: {e}")
    print("请确保已激活虚拟环境并安装了Django")
    print("运行命令: venv\\Scripts\\python.exe spider\\import_brand.py")
    sys.exit(1)

from app.models import CarBrand
from django.db import IntegrityError


def import_brand_to_db(csv_file_path):
    """
    将品牌CSV文件数据导入数据库
    存在则更新，不存在则新建
    """
    print(f"开始导入/更新品牌数据: {csv_file_path}")


    CarBrand.objects.all().delete()
    print("✅ 品牌表数据已清空，开始重新导入...")


    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE app_carbrand AUTO_INCREMENT = 1;")
    print("✅ 表已清空，ID 已重置为从 1 开始")


    df = pd.read_csv(csv_file_path)


    df.dropna(inplace=True)
    df.drop_duplicates(subset=['brand'], inplace=True)

    print(f"总共有 {df.shape[0]} 条有效品牌数据")


    created_count = 0
    error_count = 0

    for index, row in df.iterrows():
        try:
            brand = str(row['brand']).strip()
            brand_img = str(row['brand_img']).strip()
            brand_id = str(row['brand_id']).strip()


            obj, created = CarBrand.objects.update_or_create(
                brand=brand,
                defaults={
                    "brand_img": brand_img,
                    "brand_id": brand_id,
                }
            )

            if created:
                created_count += 1
                print(f"新建品牌: {brand}")

        except IntegrityError:
            error_count += 1
        except Exception as e:
            error_count += 1
            print(f"出错: {e} | {row}")

    print(f"\n✅ 品牌数据导入完成！")
    print(f"成功导入: {created_count} 条")
    print(f"错误数据: {error_count} 条")


def find_latest_brand_csv():
    """
    固定使用 latest_brand.csv
    完全按你要求来
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    latest_brand = os.path.join(current_dir, 'latest_brand.csv')

    if os.path.exists(latest_brand):
        print(f"找到品牌最新文件: {latest_brand}")
        return latest_brand

    return None


if __name__ == '__main__':
    csv_file = find_latest_brand_csv()

    if csv_file:
        import_brand_to_db(csv_file)
    else:
        print("❌ 未找到 latest_brand.csv 文件！")
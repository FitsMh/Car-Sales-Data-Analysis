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
    print("运行命令: venv\\Scripts\\python.exe spider\\import_data.py")
    sys.exit(1)

from app.models import CarInformationNanjing
from django.db import IntegrityError


def import_csv_to_db(csv_file_path):
    """
    将CSV文件中的数据导入到数据库（更新机制）
    使用品牌+车型名作为唯一标识，存在则更新，不存在则创建
    """
    print(f"开始导入/更新数据: {csv_file_path}")

    CarInformationNanjing.objects.all().delete()
    print("✅ 表数据已清空，开始重新导入...")
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE app_CarInformationNanjing AUTO_INCREMENT = 1;")
    print("✅ 表已清空，ID 已重置为从 1 开始")


    df = pd.read_csv(csv_file_path)



    df.dropna(inplace=True)

    df.drop_duplicates(subset=['brand', 'carname'], inplace=True)

    print(f"总共有 {df.shape[0]} 条有效数据")


    created_count = 0
    updated_count = 0
    error_count = 0

    for index, row in df.iterrows():
        try:

            brand = str(row['brand']).strip()
            carname = str(row['carname']).strip()


            existing_car = CarInformationNanjing.objects.filter(
                brand=brand,
                carname=carname
            ).first()

            if existing_car:

                existing_car.carimg = row['carimg']
                existing_car.salevolume = row['salevolume']
                existing_car.price = row['price']
                existing_car.manufacturer = row['manufacturer']
                existing_car.carmodel = row['carmodel']
                existing_car.energytype = row['energytype']
                existing_car.marketime = row['marketime']
                existing_car.insure = row['insure']
                existing_car.save()
                updated_count += 1
                print(f"更新: {brand}-{carname}")
            else:

                CarInformationNanjing.objects.create(
                    brand=brand,
                    carname=carname,
                    carimg=row['carimg'],
                    salevolume=row['salevolume'],
                    price=row['price'],
                    manufacturer=row['manufacturer'],
                    carmodel=row['carmodel'],
                    energytype=row['energytype'],
                    marketime=row['marketime'],
                    insure=row['insure']
                )
                created_count += 1
                print(f"新建: {brand}-{carname}")

            if (created_count + updated_count + error_count) % 50 == 0:
                print(
                    f"已处理 {created_count + updated_count + error_count} 条数据（新建: {created_count}, 更新: {updated_count}, 错误: {error_count}）")

        except IntegrityError as e:
            error_count += 1
            print(f"数据重复错误: {e}, 品牌: {row.get('brand', 'N/A')}, 车名: {row.get('carname', 'N/A')}")
        except Exception as e:
            error_count += 1
            print(f"处理数据出错: {e}, 行: {row}")

    print(f"数据处理完成，共处理 {created_count + updated_count + error_count} 条数据")
    print(f"新建数据: {created_count} 条")
    print(f"更新数据: {updated_count} 条")
    print(f"错误数据: {error_count} 条")

    return created_count, updated_count, error_count


def find_latest_csv():
    """
    查找最新的CSV文件
    优先使用latest_data.csv，如果不存在则查找最新的car_data_*.csv文件
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))


    latest_link = os.path.join(current_dir, 'latest_data.csv')
    if os.path.exists(latest_link):
        print(f"找到最新数据链接: {latest_link}")
        return latest_link


    csv_files = glob.glob(os.path.join(current_dir, 'car_data_*.csv'))
    if csv_files:

        latest_file = max(csv_files, key=os.path.getmtime)
        print(f"找到最新数据文件: {os.path.basename(latest_file)}")
        return latest_file


    old_csv = os.path.join(current_dir, 'temp.csv')
    if os.path.exists(old_csv):
        print(f"未找到新格式文件，使用旧文件: temp.csv")
        return old_csv

    return None


if __name__ == '__main__':

    csv_file_path = find_latest_csv()

    if csv_file_path:
        print(f"准备导入数据: {csv_file_path}")
        import_csv_to_db(csv_file_path)
    else:
        print("错误：未找到任何可用的CSV文件")
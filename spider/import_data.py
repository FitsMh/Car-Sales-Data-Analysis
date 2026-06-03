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

from app.models import CarInformation
from django.db import IntegrityError


def clean_csv_duplicates(csv_file_path):
    print(f"开始清洗CSV文件: {csv_file_path}")

    df = pd.read_csv(csv_file_path)
    original_count = df.shape[0]
    print(f"原始数据行数: {original_count}")

    df.dropna(how='all', inplace=True)
    after_dropna = df.shape[0]
    if after_dropna < original_count:
        print(f"删除空行: {original_count - after_dropna} 行")

    df.drop_duplicates(subset=['brand', 'carname'], keep='first', inplace=True)
    after_dedup = df.shape[0]
    duplicates_removed = after_dropna - after_dedup

    print(f"基于品牌+车型去重: 删除 {duplicates_removed} 条重复数据")
    print(f"清洗后数据行数: {after_dedup}")

    df.reset_index(drop=True, inplace=True)

    df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
    print(f"CSV文件清洗完成，已保存至: {csv_file_path}")

    return after_dedup, duplicates_removed


def import_csv_to_db(csv_file_path):
    print(f"开始导入数据到数据库: {csv_file_path}")

    deleted_count = CarInformation.objects.all().delete()[0]
    print(f"已删除 {deleted_count} 条旧数据")

    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE app_carinformation AUTO_INCREMENT = 1;")
    print("表已清空，ID已重置为从1开始")

    df = pd.read_csv(csv_file_path)

    df.dropna(inplace=True)
    df.drop_duplicates(subset=['brand', 'carname'], inplace=True)

    print(f"总共有 {df.shape[0]} 条有效数据")

    created_count = 0
    error_count = 0
    skipped_count = 0

    for index, row in df.iterrows():
        try:
            brand = str(row['brand']).strip()
            carname = str(row['carname']).strip()

            if not brand or not carname or brand == 'nan' or carname == 'nan':
                skipped_count += 1
                print(f"跳过空数据行 {index + 2}（CSV行号）")
                continue

            CarInformation.objects.create(
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

            if created_count % 100 == 0:
                print(f"已导入 {created_count} 条数据...")

        except IntegrityError as e:
            error_count += 1
            print(f"数据重复错误: {brand} - {carname}")
        except Exception as e:
            error_count += 1
            print(f"处理数据出错 (行 {index + 2}): {e}")
            print(f"数据: {row.to_dict()}")

    print(f"\n导入完成统计:")
    print(f"成功导入: {created_count} 条")
    print(f"跳过空数据: {skipped_count} 条")
    print(f"错误: {error_count} 条")
    print(f"总处理: {created_count + skipped_count + error_count} 条")

    last_car = CarInformation.objects.order_by('-id').first()
    total_cars = CarInformation.objects.count()
    if last_car and last_car.id == total_cars:
        print(f"ID连续性验证通过: ID从1到{last_car.id}，共{total_cars}条记录")
    else:
        print(f"ID可能不连续: 最后ID={last_car.id if last_car else 0}, 总数={total_cars}")

    return created_count, error_count


def find_latest_csv():
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
    print("=" * 60)
    print("汽车数据导入系统")
    print("=" * 60)

    csv_file_path = find_latest_csv()

    if csv_file_path:
        print(f"准备处理数据文件: {csv_file_path}")
        cleaned_count, removed_count = clean_csv_duplicates(csv_file_path)

        created_count, error_count = import_csv_to_db(csv_file_path)

        print("\n" + "=" * 60)
        print("所有操作完成！")
        print(f"CSV清洗: 删除 {removed_count} 条重复数据")
        print(f"数据库导入: 成功 {created_count} 条")
        if error_count > 0:
            print(f"导入错误: {error_count} 条")
        print("=" * 60)
    else:
        print("错误：未找到任何可用的CSV文件")
        print("请确保 spider 目录下存在 latest_data.csv 或 car_data_*.csv 文件")
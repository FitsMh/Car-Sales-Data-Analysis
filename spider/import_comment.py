import os
import csv
import glob
import sys
import pandas as pd
import numpy as np


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', '基于Django系统.settings')


try:
    import django
    django.setup()
    print("Django环境初始化成功")
except ImportError as e:
    print(f"Django导入失败: {e}")
    sys.exit(1)

from app.models import SpiderCarComment
from django.db import IntegrityError


def import_comment_csv_to_db(csv_file_path):
    """
    修复MySQL编码冲突 + 不丢数据 + 宽松去重
    """
    print(f"开始导入评论数据: {csv_file_path}")


    df = pd.read_csv(csv_file_path, dtype=str).fillna("")
    print(f"CSV文件总数据量: {df.shape[0]} 条")

    created_count = 0
    duplicate_count = 0
    error_count = 0


    def clean_text(text):
        if not text or pd.isna(text):
            return ""

        s = str(text).strip()

        s = s.encode('utf-8', 'ignore').decode('utf-8')
        return s

    for index, row in df.iterrows():
        try:

            series_id = clean_text(row.get('series_id', ''))
            carname = clean_text(row.get('carname', ''))
            username = clean_text(row.get('username', ''))
            user_profile_link = clean_text(row.get('user_profile_link', ''))
            content = clean_text(row.get('content', ''))
            timestamp = clean_text(row.get('timestamp', ''))
            comments = clean_text(row.get('comments', ''))
            likes = clean_text(row.get('likes', ''))




            SpiderCarComment.objects.create(
                series_id=series_id,
                carname=carname,
                username=username,
                user_profile_link=user_profile_link,
                content=content,
                timestamp=timestamp,
                comments=comments,
                likes=likes
            )
            created_count += 1


            total = created_count + duplicate_count + error_count
            if total % 200 == 0:
                print(f"进度：已处理 {total} 条 | 成功 {created_count}")

        except IntegrityError:
            duplicate_count += 1
        except Exception as e:
            error_count += 1



    print("\n===== 导入完成 =====")
    print(f"文件总条数：{len(df)}")
    print(f"成功入库：{created_count}")
    print(f"重复数据：{duplicate_count}")
    print(f"错误数据：{error_count}")

    return created_count, duplicate_count, error_count


def find_comment_csv():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    comment_file = os.path.join(current_dir, 'latest_comment_data.csv')
    if os.path.exists(comment_file):
        print(f"找到文件: {comment_file}")
        return comment_file
    return None


if __name__ == '__main__':
    csv_file_path = find_comment_csv()
    if csv_file_path:
        import_comment_csv_to_db(csv_file_path)
    else:
        print("错误：未找到 latest_comment_data.csv")
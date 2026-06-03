
"""
批量导入所有城市的爬虫数据（调用import_data.py）
适配目录结构：spider_{city}/import_data.py
"""
import os
import sys
import subprocess
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CITIES = [
    "beijing", "chengdu", "chongqing", "guangzhou", "hangzhou",
    "nanchang", "nanjing", "shanghai", "shenzhen", "suzhou",
    "tianjin", "wuhan", "xian"
]


def run_city_import(city: str) -> None:
    """
    执行单个城市目录下的import_data.py脚本
    :param city: 城市拼音（与目录名一致）
    """
    dir_name = f"spider_{city}"
    script_path = os.path.join(BASE_DIR, dir_name, "import_data.py")

    if not os.path.exists(script_path):
        logger.error(f"❌ 导入脚本不存在：{script_path}")
        return

    try:
        logger.info(f"▶️  开始导入 {dir_name} 数据 ...")
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.path.dirname(script_path),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            logger.info(f"✅ {dir_name} 数据导入成功！")
            if result.stdout:
                logger.debug(f"输出日志：\n{result.stdout}")
        else:
            logger.error(f"❌ {dir_name} 数据导入失败！")
            if result.stderr:
                logger.error(f"错误日志：\n{result.stderr}")

    except Exception as e:
        logger.error(f"⚠️  导入 {dir_name} 数据时出现异常：{str(e)}", exc_info=True)


def batch_run_city_imports():
    """批量导入所有城市数据"""
    logger.info("=" * 60)
    logger.info("🚀 开始批量导入城市数据")
    logger.info("=" * 60)

    for city in CITIES:
        run_city_import(city)

    logger.info("=" * 60)
    logger.info("🏁 所有城市数据导入任务执行完毕！")
    logger.info("=" * 60)


if __name__ == "__main__":
    batch_run_city_imports()
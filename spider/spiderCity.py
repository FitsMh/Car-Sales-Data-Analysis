
"""
批量执行所有城市的爬虫脚本（spider_beijing ~ spider_xian）
适配目录结构：spider_{city}/spiders.py
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


def run_city_spider(city: str) -> None:
    """
    执行单个城市目录下的spiders.py脚本
    :param city: 城市拼音（与目录名一致）
    """

    dir_name = f"spider_{city}"
    script_path = os.path.join(BASE_DIR, dir_name, "spiders.py")


    if not os.path.exists(script_path):
        logger.error(f"❌ 脚本不存在：{script_path}")
        return

    try:

        logger.info(f"▶️  开始执行 {dir_name}/spiders.py ...")
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.path.dirname(script_path),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            logger.info(f"✅ {dir_name} 执行成功！")
            if result.stdout:
                logger.debug(f"输出日志：\n{result.stdout}")
        else:
            logger.error(f"❌ {dir_name} 执行失败！")
            if result.stderr:
                logger.error(f"错误日志：\n{result.stderr}")

    except Exception as e:
        logger.error(f"⚠️  执行 {dir_name} 时出现异常：{str(e)}", exc_info=True)


def batch_run_city_spiders():
    """批量执行所有城市的爬虫脚本"""
    logger.info("=" * 60)
    logger.info("🚀 开始批量执行城市爬虫任务")
    logger.info("=" * 60)

    for city in CITIES:
        run_city_spider(city)

    logger.info("=" * 60)
    logger.info("🏁 所有城市爬虫任务执行完毕！")
    logger.info("=" * 60)


if __name__ == "__main__":
    batch_run_city_spiders()
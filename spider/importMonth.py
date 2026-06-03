
"""
批量导入1-5个月前的爬虫数据（调用import_data.py）
适配目录结构：spider_{n}_month_ago/import_data.py
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
MONTHS = [1, 2, 3, 4, 5]


def run_import_script(month: int) -> None:
    """
    执行单个月份目录下的import_data.py脚本
    :param month: 月份（1-5）
    """
    dir_name = f"spider_{month}_month_ago"
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


def batch_run_imports():
    """批量导入所有月份数据"""
    logger.info("=" * 60)
    logger.info("🚀 开始批量导入月度数据")
    logger.info("=" * 60)

    for month in MONTHS:
        run_import_script(month)

    logger.info("=" * 60)
    logger.info("🏁 所有月度数据导入任务执行完毕！")
    logger.info("=" * 60)


if __name__ == "__main__":
    batch_run_imports()
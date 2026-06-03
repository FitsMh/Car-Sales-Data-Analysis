import csv
import os
import shutil


class CSVManager:
    def __init__(self, latest_csv_name='latest_data.csv'):
        """
        初始化CSV管理器
        :param latest_csv_name: 目标文件名（默认为latest_data.csv）
        """
        self.current_dir = os.path.dirname(__file__)
        self.latest_csv_path = os.path.join(self.current_dir, latest_csv_name)

    def clear_latest_csv(self):
        """清空latest文件中的数据（只保留表头）"""
        try:
            if os.path.exists(self.latest_csv_path):
                # 读取原有表头
                with open(self.latest_csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    try:
                        header = next(reader)  # 获取表头
                    except StopIteration:
                        # 如果文件为空，使用默认表头
                        header = ["brand", "carname", "carimg", "salevolume", "price",
                                  "manufacturer", "carmodel", "energytype", "marketime", "insure"]

                # 用表头重新写入文件（清空数据）
                with open(self.latest_csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)

                print(f"✓ 已清空 {self.latest_csv_path} 中的数据（保留表头）")
            else:
                print(f"⚠ 文件 {self.latest_csv_path} 不存在，将创建新文件")
                # 创建新文件并写入表头
                header = ["brand", "carname", "carimg", "salevolume", "price",
                          "manufacturer", "carmodel", "energytype", "marketime", "insure"]
                with open(self.latest_csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                print(f"✓ 已创建 {self.latest_csv_path} 并写入表头")
        except Exception as e:
            print(f"✗ 清空文件失败: {e}")
            return False
        return True

    def import_csv_to_latest(self, source_csv_name):
        """
        将指定的CSV文件内容导入到latest文件
        :param source_csv_name: 源CSV文件名（可以是相对路径或绝对路径）
        """
        # 确定源文件路径
        if os.path.isabs(source_csv_name):
            source_path = source_csv_name
        else:
            source_path = os.path.join(self.current_dir, source_csv_name)

        # 检查源文件是否存在
        if not os.path.exists(source_path):
            print(f"✗ 源文件不存在: {source_path}")
            return False

        # 先清空latest文件
        if not self.clear_latest_csv():
            return False

        try:
            # 读取源文件数据
            with open(source_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)

            if not rows:
                print(f"⚠ 源文件 {source_csv_name} 为空")
                return False

            # 写入数据到latest文件
            with open(self.latest_csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # 如果源文件第一行是表头且与目标表头一致，跳过表头
                header = ["brand", "carname", "carimg", "salevolume", "price",
                          "manufacturer", "carmodel", "energytype", "marketime", "insure"]

                start_row = 0
                if rows and len(rows[0]) == len(header):
                    # 检查第一行是否是表头
                    if rows[0][0] == "brand" or rows[0][0] in header:
                        start_row = 1
                        print(f"✓ 检测到表头，自动跳过")

                # 写入数据行
                for row in rows[start_row:]:
                    # 确保数据有足够的列数
                    if len(row) < len(header):
                        row.extend([''] * (len(header) - len(row)))
                    writer.writerow(row[:len(header)])

                data_count = len(rows) - start_row
                print(f"✓ 成功将 {data_count} 条数据从 {source_csv_name} 导入到 {self.latest_csv_path}")
                return True

        except Exception as e:
            print(f"✗ 导入数据失败: {e}")
            return False

    def show_latest_content(self, max_rows=20):
        """显示latest文件的前几行内容"""
        try:
            if not os.path.exists(self.latest_csv_path):
                print(f"文件 {self.latest_csv_path} 不存在")
                return

            with open(self.latest_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)

            if not rows:
                print("文件为空")
                return

            print(f"\n{self.latest_csv_path} 内容预览（共{len(rows)}行，显示前{min(max_rows, len(rows))}行）:")
            print("-" * 100)
            for i, row in enumerate(rows[:max_rows]):
                print(f"第{i}行: {row}")
            if len(rows) > max_rows:
                print(f"... 还有 {len(rows) - max_rows} 行未显示")
            print("-" * 100)

        except Exception as e:
            print(f"读取文件失败: {e}")


# 交互式命令行工具
def interactive():
    """交互式命令行界面"""
    manager = CSVManager()

    print("\n" + "=" * 50)
    print("CSV文件管理工具")
    print("=" * 50)
    print("1. 清空 latest_data.csv 文件")
    print("2. 导入CSV文件到 latest_data.csv")
    print("3. 查看 latest_data.csv 内容")
    print("4. 导入并替换（清空+导入）")
    print("5. 退出")
    print("=" * 50)

    while True:
        choice = input("\n请选择操作 (1-5): ").strip()

        if choice == '1':
            manager.clear_latest_csv()

        elif choice == '2':
            filename = input("请输入要导入的CSV文件名: ").strip()
            if filename:
                manager.import_csv_to_latest(filename)
            else:
                print("文件名不能为空")

        elif choice == '3':
            manager.show_latest_content()

        elif choice == '4':
            filename = input("请输入要导入的CSV文件名: ").strip()
            if filename:
                # 先清空再导入
                if manager.clear_latest_csv():
                    manager.import_csv_to_latest(filename)
            else:
                print("文件名不能为空")

        elif choice == '5':
            print("再见！")
            break
        else:
            print("无效选择，请重新输入")


if __name__ == '__main__':
    # 方式1：交互式使用
    interactive()

    # 方式2：直接调用函数使用（取消注释下面的代码）
    # manager = CSVManager()
    #
    # # 清空latest文件
    # manager.clear_latest_csv()
    #
    # # 导入指定的CSV文件
    # manager.import_csv_to_latest('car_data_20260319_143022.csv')
    #
    # # 查看导入结果
    # manager.show_latest_content()
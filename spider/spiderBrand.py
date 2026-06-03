import csv
import os
import datetime




class BrandSpider(object):
    def __init__(self):
        self.spiderName = 'CarBrandLogo'
        self.local_file = "response.txt"


        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f"car_brand_{self.timestamp}.csv"
        self.csv_path = os.path.join(os.path.dirname(__file__), self.csv_filename)
        self.latest_csv_link = os.path.join(os.path.dirname(__file__), 'latest_brand.csv')

    def init(self):

        with open(self.csv_path, 'w', newline='', encoding='utf-8') as wf:
            writer = csv.writer(wf)
            writer.writerow(["brand", "brand_img", "brand_id"])


        try:
            if os.path.exists(self.latest_csv_link):
                os.remove(self.latest_csv_link)

            with open(self.latest_csv_link, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(["brand", "brand_img", "brand_id"])
        except Exception as e:
            print(f"更新 latest_brand.csv 失败: {e}")

        print(f"创建品牌CSV文件: {self.csv_filename}")
        print(f"已清空 latest_brand.csv 并准备写入最新数据")

    def main(self):
        print("开始从本地 response.txt 提取品牌数据...")


        try:
            with open(self.local_file, 'r', encoding='utf-8') as f:
                text = f.read()
        except:
            print("❌ 请把 response.txt 放在爬虫同一个文件夹！")
            return

        brand_list = []


        lines = text.splitlines()
        current_brand = None
        current_img = None
        current_id = None

        for line in lines:
            line = line.strip()


            if '"brand_name"' in line:
                parts = line.split(':', 1)
                if len(parts) >= 2:
                    val = parts[1].strip().strip('",')
                    current_brand = val


            if '"image_url"' in line:
                parts = line.split(':', 1)
                if len(parts) >= 2:
                    val = parts[1].strip().strip('",')
                    current_img = val


            if '"brand_id"' in line:
                parts = line.split(':', 1)
                if len(parts) >= 2:
                    val = parts[1].strip().strip('",')
                    current_id = val


            if current_brand and current_img and current_id:
                brand_list.append((current_brand, current_img, current_id))
                current_brand = None
                current_img = None
                current_id = None

        if not brand_list:
            print("❌ 没有抓到任何品牌数据")
            return


        count = 0
        for b, i, d in brand_list:

            i = i.replace("\\/", "/")
            print(f"{b} | {i}")
            self.save_to_csv([b, i, d])
            count += 1

        print(f"\n✅ 提取完成！共 {count} 个汽车品牌")
        print(f"📄 时间戳文件: {self.csv_filename}")
        print(f"📄 最新文件: {self.latest_csv_link}")

    def save_to_csv(self, resultData):

        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(resultData)

        with open(self.latest_csv_link, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(resultData)

    def run(self):
        self.init()
        self.main()


if __name__ == '__main__':
    spider = BrandSpider()
    spider.run()
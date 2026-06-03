import csv
import os
import datetime

import django
import pandas as pd
import requests
from lxml import etree


os.environ.setdefault('DJANGO_SETTINGS_MODULE', '基于Django系统.settings')

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from app.models import CarInformation


class spider(object):
    def __init__(self, crawl_count=1000):
        self.spiderName = 'VehicleView'

        self.base_url = "https://www.dongchedi.com/motor/pc/car/rank_data"
        self.crawl_count = crawl_count
        self.current_count = 0

        self.header = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
        }

        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f"car_data_{self.timestamp}.csv"
        self.csv_path = os.path.join(os.path.dirname(__file__), self.csv_filename)

        self.latest_csv_link = os.path.join(os.path.dirname(__file__), 'latest_data.csv')

    def init(self):

        car_data = {
            "brand": "品牌",
            "carname": "汽车名称",
            "carimg": "汽车图片链接",
            "salevolume": "销售量",
            "price": "价格",
            "manufacturer": "制造商",
            "carmodel": "车型",
            "energytype": "能源类型",
            "marketime": "上市时间",
            "insure": "保修信息"
        }


        with open(self.csv_path, 'w', newline='', encoding='utf-8') as wf:
            writer = csv.writer(wf)
            writer.writerow(
                ["brand", "carname", "carimg", "salevolume", "price", "manufacturer", "carmodel",
                 "energytype", "marketime", "insure"])

        print(f"创建新的CSV文件: {self.csv_filename}")


        try:

            if os.path.exists(self.latest_csv_link):
                os.remove(self.latest_csv_link)


            import shutil
            shutil.copy2(self.csv_path, self.latest_csv_link)
            print(f"更新最新数据链接: latest_data.csv -> {self.csv_filename}")
        except Exception as e:
            print(f"更新最新数据链接失败: {e}")



    def main(self, start_offset=0):
        """
        主爬取方法，支持分页获取大量数据
        :param start_offset: 起始偏移量
        """

        self.current_count = 0
        current_offset = start_offset

        print(f"开始爬取，目标数量: {self.crawl_count}条")


        while self.current_count < self.crawl_count:

            remaining_count = self.crawl_count - self.current_count
            request_count = min(100, remaining_count + 20)


            params = {
                'aid': 1839,
                'app_name': 'auto_web_pc',
                'count': request_count,
                'month': '202512',
                'new_energy_type': '',
                'rank_data_type': 11,
                'brand_id': '',
                'price': '',
                'manufacturer': '',
                'outter_detail_type': '',
                'nation': 0,
                'offset': current_offset
            }

            print(f"第{(current_offset//50)+1}次API请求: offset={current_offset}, count={request_count}, 已爬取={self.current_count}/{self.crawl_count}条")

            try:
                response = requests.get(self.base_url, headers=self.header, params=params, timeout=30)
                pageJson = response.json()

                if 'data' not in pageJson or 'list' not in pageJson['data']:
                    print(f"API返回数据格式异常: {pageJson}")
                    break

                car_list = pageJson["data"]["list"]

                if not car_list:
                    print(f"没有更多数据可获取，停止爬取")
                    break

                print(f"本次API返回{len(car_list)}条数据")

                for index, car in enumerate(car_list):

                    if self.current_count >= self.crawl_count:
                        print(f"已达到目标爬取数量{self.crawl_count}，停止爬取")
                        return

                    carData = []
                    car_name = car.get('series_name', '未知车型')
                    print(f"正在爬取第{self.current_count + 1}条数据: {car_name}")


                    carData.append(car["brand_name"])
                    carData.append(car["series_name"])
                    carData.append(car["image"])
                    carData.append(car["count"])


                    price = []
                    price.append(car["max_price"])
                    price.append(car["min_price"])
                    carData.append(price)


                    carData.append(car["sub_brand_name"])


                    carNum = car["series_id"]

                    try:
                        infoHTML = requests.get(f"https://www.dongchedi.com/auto/params-carIds-x-{carNum}",
                                              headers=self.header, timeout=15)
                        infoHTMLpath = etree.HTML(infoHTML.text)


                        try:
                            carModel = infoHTMLpath.xpath("//div[@data-row-anchor='jb']/div[2]/div/text()")[0]
                            carData.append(carModel)
                        except (IndexError, AttributeError):
                            carData.append("未知车型")


                        try:
                            energyType = infoHTMLpath.xpath("//div[@data-row-anchor='fuel_form']/div[2]/div/text()")[0]
                            carData.append(energyType)
                        except (IndexError, AttributeError):
                            carData.append("未知能源")


                        try:
                            marketTime = infoHTMLpath.xpath("//div[@data-row-anchor='market_time']/div[2]/div/text()")[0]
                            carData.append(marketTime)
                        except (IndexError, AttributeError):
                            carData.append("未知")


                        try:
                            insure = infoHTMLpath.xpath("//div[@data-row-anchor='period']/div[2]/div/text()")[0]
                            carData.append(insure)
                        except (IndexError, AttributeError):
                            carData.append("未知")

                    except Exception as e:
                        print(f"获取详细信息失败: {e}")

                        carData.extend(["未知车型", "未知能源", "未知", "未知"])

                    print(f"完整数据: {carData}")
                    self.save_to_csv(carData)
                    self.current_count += 1


                    import time
                    time.sleep(0.1)


                current_offset += len(car_list)


                if len(car_list) < request_count:
                    print(f"返回数据不足，可能已达到数据源末尾")
                    if self.current_count < self.crawl_count:
                        print(f"目标{self.crawl_count}条，实际只获取到{self.current_count}条数据")
                    break

            except Exception as e:
                print(f"爬取过程中出错: {e}")

                current_offset += 50
                continue

        print(f"本次爬取完成，共获取{self.current_count}条数据")

    def run_spider(self):
        """
        运行爬虫的便捷方法，供外部调用
        返回创建的CSV文件路径
        """
        try:
            self.init()
            self.main()
            print(f"爬虫运行完成，数据已保存到: {self.csv_filename}")
            return True, self.csv_path
        except Exception as e:
            print(f"爬虫运行失败: {e}")
            return False, None

    def save_to_csv(self, resultData):

        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(resultData)


        with open(self.latest_csv_link, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(resultData)


    def clear_csv(self, csv_path=None):

        if csv_path is None:
            csv_path = self.csv_path

        print(f"清洗CSV数据: {csv_path}")
        df = pd.read_csv(csv_path)


        df.dropna(inplace=True)

        df.drop_duplicates(inplace=True)
        print(f"清洗后总共有 {df.shape[0]} 条数据")
        return df.values

    def save_to_sql(self, csv_path=None):

        if csv_path is None:
            csv_path = self.csv_path

        print(f"将CSV数据导入数据库: {csv_path}")
        data = self.clear_csv(csv_path)

        created_count = 0
        for car in data:
            try:

                existing_car = CarInformation.objects.filter(
                    brand=car[0],
                    carname=car[1]
                ).first()

                if existing_car:

                    existing_car.carimg = car[2]
                    existing_car.salevolume = car[3]
                    existing_car.price = car[4]
                    existing_car.manufacturer = car[5]
                    existing_car.carmodel = car[6]
                    existing_car.energytype = car[7]
                    existing_car.marketime = car[8]
                    existing_car.insure = car[9]
                    existing_car.save()
                    print(f"更新: {car[0]}-{car[1]}")
                else:

                    CarInformation.objects.create(
                        brand=car[0],
                        carname=car[1],
                        carimg=car[2],
                        salevolume=car[3],
                        price=car[4],
                        manufacturer=car[5],
                        carmodel=car[6],
                        energytype=car[7],
                        marketime=car[8],
                        insure=car[9]
                    )
                    created_count += 1
                    print(f"新建: {car[0]}-{car[1]}")
            except Exception as e:
                print(f"导入数据出错: {e}, 数据: {car}")

        print(f"数据导入完成，新建 {created_count} 条记录")


if __name__ == '__main__':
    spiderObj = spider()
    spiderObj.init()
    spiderObj.main()


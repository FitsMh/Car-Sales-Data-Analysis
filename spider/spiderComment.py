import csv
import os
import datetime
import time
import requests
from lxml import etree
from bs4 import BeautifulSoup



class CarCommunitySpider:
    def __init__(self, crawl_count=10, comment_count=100):
        self.spiderName = 'CarCommunityView'
        self.base_url = "https://www.dongchedi.com/motor/pc/car/rank_data"
        self.crawl_count = crawl_count
        self.comment_count = comment_count
        self.current_count = 0

        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }

        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.comment_car_csv_filename = f"comment_car_data_{self.timestamp}.csv"
        self.comment_csv_filename = f"car_comment_{self.timestamp}.csv"
        self.latest_comment_csv = "latest_comment_data.csv"

        current_dir = os.getcwd()
        self.comment_car_csv_path = os.path.join(current_dir, self.comment_car_csv_filename)
        self.comment_csv_path = os.path.join(current_dir, self.comment_csv_filename)
        self.latest_comment_path = os.path.join(current_dir, self.latest_comment_csv)

    def init_csv(self):
        with open(self.comment_car_csv_path, 'w', newline='', encoding='utf-8') as wf:
            writer = csv.writer(wf)
            writer.writerow([
                "brand", "carname", "carimg", "salevolume", "price",
                "manufacturer", "carmodel", "energytype", "marketime", "insure", "series_id"
            ])

        with open(self.comment_csv_path, 'w', newline='', encoding='utf-8') as wf:
            writer = csv.writer(wf)
            writer.writerow([
                "series_id", "carname", "username", "user_profile_link",
                "content", "timestamp", "comments", "likes"
            ])

        with open(self.latest_comment_path, 'w', newline='', encoding='utf-8') as wf:
            writer = csv.writer(wf)
            writer.writerow([
                "series_id", "carname", "username", "user_profile_link",
                "content", "timestamp", "comments", "likes"
            ])

        print(f"汽车数据文件：{self.comment_car_csv_filename}")
        print(f"评论数据文件：{self.comment_csv_filename}")
        print(f"最新评论文件：{self.latest_comment_csv}（已清空）")

    def crawl_car_list(self):
        car_list = []
        current_offset = 0

        while self.current_count < self.crawl_count:
            remaining = self.crawl_count - self.current_count
            request_count = min(100, remaining + 20)

            params = {
                'aid': 1839,
                'app_name': 'auto_web_pc',
                'count': request_count,
                'month': '',
                'new_energy_type': '',
                'rank_data_type': 11,
                'brand_id': '',
                'price': '',
                'manufacturer': '',
                'outter_detail_type': '',
                'nation': 0,
                'offset': current_offset
            }

            try:
                response = requests.get(self.base_url, headers=self.header, params=params, timeout=30)
                pageJson = response.json()

                if 'data' not in pageJson or 'list' not in pageJson['data']:
                    break

                cars = pageJson["data"]["list"]
                if not cars:
                    break

                for car in cars:
                    if self.current_count >= self.crawl_count:
                        break

                    series_id = str(car.get("series_id", ""))
                    car_info = {
                        "brand": car.get("brand_name", "未知品牌"),
                        "carname": car.get("series_name", "未知车型"),
                        "carimg": car.get("image", ""),
                        "salevolume": car.get("count", 0),
                        "price": f"{car.get('min_price', 0)}-{car.get('max_price', 0)}万",
                        "manufacturer": car.get("sub_brand_name", "未知厂商"),
                        "series_id": series_id
                    }

                    detail = self.get_car_detail(series_id)
                    car_info.update(detail)

                    self.save_car(car_info)
                    car_list.append(car_info)

                    self.current_count += 1
                    print(f"汽车 {self.current_count}/{self.crawl_count}：{car_info['carname']}")
                    time.sleep(0.3)

                current_offset += len(cars)
                if len(cars) < request_count:
                    break

            except Exception as e:
                print(f"汽车列表出错：{e}")
                current_offset += 50
                continue

        return car_list

    def get_car_detail(self, series_id):
        try:
            url = f"https://www.dongchedi.com/auto/params-carIds-x-{series_id}"
            res = requests.get(url, headers=self.header, timeout=15)
            html = etree.HTML(res.text)

            def xpath_get(xp):
                try:
                    return html.xpath(xp)[0].strip()
                except:
                    return "未知"

            return {
                "carmodel": xpath_get("//div[@data-row-anchor='jb']/div[2]/div/text()"),
                "energytype": xpath_get("//div[@data-row-anchor='fuel_form']/div[2]/div/text()"),
                "marketime": xpath_get("//div[@data-row-anchor='market_time']/div/text()"),
                "insure": xpath_get("//div[@data-row-anchor='period']/div[2]/div/text()")
            }
        except:
            return {"carmodel": "未知", "energytype": "未知", "marketime": "未知", "insure": "未知"}


    def crawl_comments(self, car_info):
        sid = car_info["series_id"]
        name = car_info["carname"]
        collected = 0
        page = 1
        max_pages = 10

        print(f"正在爬评论：{name}（目标：{self.comment_count} 条）")

        while collected < self.comment_count and page <= max_pages:
            try:
                url = f"https://www.dongchedi.com/community/{sid}?page={page}"
                res = requests.get(url, headers=self.header, timeout=12)
                soup = BeautifulSoup(res.text, 'html.parser')
                cards = soup.find_all('section', class_='community-card')

                if not cards:
                    break

                for card in cards:
                    if collected >= self.comment_count:
                        break

                    item = {
                        "sid": sid, "name": name, "user": "", "link": "",
                        "content": "", "time": "", "cmt": "", "like": ""
                    }

                    u = card.find('a', href=True, title=True)
                    if u:
                        item["user"] = u["title"]
                        item["link"] = "https://www.dongchedi.com" + u["href"]

                    c = card.find('p', class_='tw-relative')
                    if c:
                        item["content"] = c.text.strip()

                    t = card.find('span', class_='tw-text-video-shallow-gray')
                    if t:
                        item["time"] = t.text.strip()

                    co = card.find('a', string=lambda x: x and "评论" in x)
                    if co:
                        item["cmt"] = co.text.strip()

                    lk = card.find('button', string=lambda x: x and "点赞" in x)
                    if lk:
                        item["like"] = lk.text.strip()

                    if item["content"]:
                        self.save_comment(item)
                        self.save_latest_comment(item)
                        collected += 1

                page += 1
                time.sleep(0.8)

            except Exception as e:
                print(f"  第{page}页出错：{e}")
                page += 1
                continue

        print(f"  └─ 完成，实际获取 {collected} 条评论")


    def save_car(self, info):
        with open(self.comment_car_csv_path, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([
                info["brand"], info["carname"], info["carimg"], info["salevolume"],
                info["price"], info["manufacturer"], info["carmodel"], info["energytype"],
                info["marketime"], info["insure"], info["series_id"]
            ])

    def save_comment(self, item):
        with open(self.comment_csv_path, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([
                item["sid"], item["name"], item["user"], item["link"],
                item["content"], item["time"], item["cmt"], item["like"]
            ])

    def save_latest_comment(self, item):
        with open(self.latest_comment_path, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([
                item["sid"], item["name"], item["user"], item["link"],
                item["content"], item["time"], item["cmt"], item["like"]
            ])

    def run(self):
        print("=" * 60)
        print("懂车帝 汽车排行榜 + 车友圈评论 整合爬虫")
        print("=" * 60)

        self.init_csv()
        cars = self.crawl_car_list()

        print("\n开始爬取车友圈评论...")
        for car in cars:
            self.crawl_comments(car)

        print("\n全部完成！")
        print(f"汽车数据：{self.comment_car_csv_filename}")
        print(f"评论数据：{self.comment_csv_filename}")
        print(f"最新评论：{self.latest_comment_csv}（已覆盖最新数据）")


if __name__ == '__main__':


    spider = CarCommunitySpider(crawl_count=1000, comment_count=100)
    spider.run()
## 🚗 汽车销售大数据分析可视化系统

> 基于 Python + Django 的全栈数据分析平台，集成 AI 智能助手、爬虫采集、情感分析、聚类推荐等核心功能，覆盖汽车销售数据的采集、存储、分析与可视化全链路。

---

## 📌 项目简介

本系统是面向汽车销售行业的大数据分析平台，支持对多城市、多车型的销售数据进行多维度统计与可视化展示，并通过集成讯飞星火大模型（RAG 增强）实现 AI 智能问答，结合 SnowNLP 情感分析、KMeans 聚类推荐，为用户提供数据洞察与决策支持。

---

## ✨ 核心功能

| 模块 | 说明 |
|------|------|
| **多维统计可视化** | 基于 ECharts 5 实现销量趋势、品牌对比、城市热力图等 10+ 种图表，支持按城市/月份/车型动态筛选 |
| **AI 智能助手** | 集成讯飞星火大模型，结合 RAG 知识检索增强，支持汽车领域专业问答 |
| **情感分析词云** | 使用 SnowNLP 对用户评论进行情感打分，生成词云图展示用户口碑 |
| **个性化推荐** | 基于 KMeans 聚类算法，对用户偏好进行分群，输出个性化车型推荐 |
| **爬虫数据采集** | 自研 Python 爬虫，覆盖主流汽车平台，采集销量、评价等结构化数据 |
| **异常预警** | 对销售数据设置阈值规则，自动识别并推送异常波动告警 |
| **报表导出** | 支持将统计结果导出为 Excel/PDF 格式，便于离线归档 |
| **分表存储架构** | 按城市/月份对 MySQL 数据表进行水平分表，提升查询性能 |
| **账户管理** | 支持用户注册、登录、权限控制，保障系统访问安全 |

---

## 🛠 技术栈

**后端**
- Python 3.11 · Django 4.x
- MySQL 8.0（水平分表架构）
- 讯飞星火大模型 API · RAG 知识检索增强
- SnowNLP（中文情感分析）· Scikit-learn KMeans（聚类推荐）
- Scrapy / Requests（爬虫采集）

**前端**
- Django 模板引擎（HTML/CSS/JS）
- ECharts 5（交互式数据可视化）

**工具链**
- Git · pip · venv

---

## 🗂 项目结构

```
├── app/                  # 主业务逻辑（视图、模型、路由）
├── spider/               # 爬虫模块（采集脚本 + 原始数据）
├── templates/            # Django 模板（HTML 页面）
├── static/               # 静态资源（ECharts、CSS、JS）
├── middleware/           # 自定义中间件（登录鉴权）
├── media/                # 用户上传文件
├── data_total/           # 数据汇总（JSON 格式）
└── manage.py             # Django 入口
```

---

## 🚀 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/your-username/AutoInsight.git
cd AutoInsight

# 2. 创建虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 配置数据库（修改 settings.py 中的 DATABASES 配置）

# 4. 执行数据库迁移
python manage.py migrate

# 5. 启动开发服务器
python manage.py runserver
```

访问 `http://127.0.0.1:8000` 查看系统。

---


## 👤 作者

**郑贺仁**  
南昌大学 · 数据科学与大数据技术

---


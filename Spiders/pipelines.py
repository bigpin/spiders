# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import csv
from items import LianjiaItem, EastMoneyItem

class SpidersPipeline:
    cvs_file = None
    file_handler = None
    
    def open_spider(self, spider):
        self.file_handler = open(spider.name + '_data.csv', 'w', encoding='utf-8')
        self.cvs_file = csv.writer(self.file_handler)
        if spider.name == 'lianjia':
            self.cvs_file.writerow(LianjiaItem.titles())
        elif spider.name == 'eastmoney':
            self.cvs_file.writerow(EastMoneyItem.titles())
        print(spider.name, "爬虫开始")
    
    def process_item(self, item, spider):
        # print(item)
        self.cvs_file.writerow(item.values())
        return item

    def close_spider(self, spider):
        self.file_handler.close()
        print(spider.name, "爬虫结束")
        
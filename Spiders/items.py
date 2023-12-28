# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SpidersItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class LianjiaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    unitPrice = scrapy.Field()
    flood = scrapy.Field()
    region = scrapy.Field()
    address = scrapy.Field()
    followInfo = scrapy.Field()
    tag = scrapy.Field()
    
    @classmethod
    def titles(self):
        return ['房源', '总价', '单价', '小区', '地区', '详情', '热度', '标签']


class EastMoneyItem(scrapy.Item):
    stock_id = scrapy.Field()
    stock_name = scrapy.Field()
    new_price = scrapy.Field()
    percentage_change = scrapy.Field()
    price_change = scrapy.Field()
    trading_volume = scrapy.Field()
    trading_value = scrapy.Field()
    price_range = scrapy.Field()
    highest_price = scrapy.Field()
    lowest_price = scrapy.Field()
    opening_price = scrapy.Field()
    closing_price = scrapy.Field()
    turnover = scrapy.Field()
    turnover_rate = scrapy.Field()
    pe = scrapy.Field()
    pb = scrapy.Field()
    
    @classmethod
    def titles(self):
        return ['股票代码', '股票名称', '最新价', '涨跌幅', '涨跌额', '成交量(手)', '成交额', '振幅', '最高价', '最低价', '今开', '昨收', '量比', '换手率', '市盈率', '市净率']

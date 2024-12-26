import scrapy
import json
from items import EastMoneyItem
from scrapy_splash import SplashRequest

class EasetMoneySpider(scrapy.Spider):
    name = "eastmoney"
    allowed_domains = ["eastmoney.com"]
    start_urls = ["https://quote.eastmoney.com/center/gridlist.html"]
    base_url = "https://quote.eastmoney.com/"
    curPage = 1
    
    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 0.5})
            
    def parse(self, response):
        # print(response.text)
        info = response.xpath("//div[@class='listview full']/table[@class='table_wrapper-table']/tbody/tr")
        for i in info:
            item = EastMoneyItem()
            stock_info = i.xpath("./td")
            item["stock_id"] = stock_info[1].xpath("./a/text()").extract()[0]
            item["stock_name"] = stock_info[2].xpath("./a/text()").extract()[0]
            item["new_price"] = stock_info[4].xpath("./span/text()").extract()[0]
            item["percentage_change"] = stock_info[5].xpath("./span/text()").extract()[0]
            item["price_change"] = stock_info[6].xpath("./span/text()").extract()[0]
            item["trading_volume"] = stock_info[7].xpath("./text()").extract()[0]
            item["trading_value"] = stock_info[8].xpath("./text()").extract()[0]
            item["price_range"] = stock_info[9].xpath("./text()").extract()[0]
            item["highest_price"] = stock_info[10].xpath("./span/text()").extract()[0]
            item["lowest_price"] = stock_info[11].xpath("./span/text()").extract()[0]
            item["opening_price"] = stock_info[12].xpath("./span/text()").extract()[0]
            item["closing_price"] = stock_info[13].xpath("./text()").extract()[0]
            item["turnover"] = stock_info[14].xpath("./text()").extract()[0]
            item["turnover_rate"] = stock_info[15].xpath("./text()").extract()[0]
            item["pe"] = stock_info[16].xpath("./text()").extract()[0]
            item["pb"] = stock_info[17].xpath("./text()").extract()[0]
            print(item['stock_id'], item['stock_name'])
            yield item
            
        if len(info) == 20 and self.curPage < 300:
            self.curPage = self.curPage + 1
            # 找到按钮并模拟点击
            script = """
            function main(splash, args)
                splash:go(args.url)
                splash:wait(0.2)

                -- 通过选择器找到按钮并模拟点击
                splash:runjs("document.querySelector('#main-table_paginate > input').value = '%d';")
                local button = splash:select('#main-table_paginate > a.paginte_go')
                button:mouse_click()

                splash:wait(1) -- 等待点击后的操作完成，根据需要调整等待时间

                return {
                    html = splash:html(),
                    png = splash:png(),
                }
            end
            """ % self.curPage
            yield SplashRequest(response.url, self.parse, dont_filter=True, endpoint='execute', args={'lua_source': script, 'wait': 0.2})


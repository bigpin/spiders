import scrapy
import json
from items import LianjiaItem

class LianjiaSpider(scrapy.Spider):
    name = "lianjia"
    allowed_domains = ["lianjia.com"]
    start_urls = ["https://bj.lianjia.com/ershoufang/rs新龙城/"]
    base_url = "https://bj.lianjia.com/"
    
    def parse(self, response):
        info = response.xpath('//div[@class="info clear"]')
        for i in info:
            item = LianjiaItem()
            item["title"] = i.xpath("./div[@class='title']/a/text()").extract()[0]
            item["price"] = i.xpath("./div[@class='priceInfo']/div[@class='totalPrice totalPrice2']/span/text()").extract()[0]
            item["unitPrice"] = i.xpath("./div[@class='priceInfo']/div[@class='unitPrice']/span/text()").extract()[0]
            temp = i.xpath("./div[@class='flood']/div[@class='positionInfo']/a/text()").extract()
            item["flood"] = temp[0]
            item["region"] = temp[1] if len(temp) > 1 else ""
            item["address"] = i.xpath("./div[@class='address']/div[@class='houseInfo']/text()").extract()[0]
            item["followInfo"] = i.xpath("./div[@class='followInfo']/text()").extract()[0]
            item["tag"] = i.xpath("./div[@class='tag']/span/text()").extract()
            yield item
            
        if len(info) > 0:
            next_page = response.xpath('//div[@class="page-box house-lst-page-box"]')
            next_page_url = next_page.xpath('./@page-url').extract()[0]
            page_data = json.loads(next_page.xpath('./@page-data').extract()[0])
            total_page = page_data['totalPage']
            current_page = page_data['curPage']
            if current_page < total_page:
                page = current_page + 1
                next_page_url = (self.base_url + next_page_url).replace('{page}', str(page))
                print(next_page_url)
                yield scrapy.Request(next_page_url, callback=self.parse)

if __name__ == "__main__":
    from scrapy import cmdline
    cmdline.execute("scrapy crawl lianjia".split())

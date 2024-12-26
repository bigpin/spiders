import scrapy
import json
import logging
import time

class StockListSpider(scrapy.Spider):
    name = "stock_list"
    allowed_domains = ["web.juhe.cn"]
    
    def __init__(self, api_key=None, *args, **kwargs):
        super(StockListSpider, self).__init__(*args, **kwargs)
        self.api_key = api_key or '8371893ed4ab2b2f75b59c7fa26bf2fe'  # 请替换为您的API key
        self.output_file = 'stock_list.txt'
        # 清空输出文件
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write('')
            
    def start_requests(self):
        # 基本请求参数
        params = {
            'key': self.api_key,
            'stock': 'a',  # 只获取A股
            'page': 1,
            'type': 4  # 每页80条数据
        }
        
        # 沪市和深市的API地址
        urls = [
            'http://web.juhe.cn/finance/stock/shall',
            'http://web.juhe.cn/finance/stock/szall'
        ]
        
        for url in urls:
            yield scrapy.Request(
                url=f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}",
                callback=self.parse,
                meta={
                    'page': 1, 
                    'params': params,
                    'base_url': url
                },
                dont_filter=True  # 允许重复的URL
            )
            # 添加延时避免请求过快
            time.sleep(1)
    
    def parse(self, response):
        try:
            data = json.loads(response.text)
            
            if data['error_code'] == 0:
                result = data['result']
                total_count = int(result['totalCount'])
                current_page = int(result['page'])
                
                # 保存当前页的股票代码
                stock_symbols = [item['symbol'] for item in result['data']]
                self.save_stock_symbols(stock_symbols)
                
                # 计算总页数
                items_per_page = 80
                total_pages = (total_count + items_per_page - 1) // items_per_page
                
                # 如果还有下一页，继续请求
                if current_page < total_pages:
                    params = response.meta['params']
                    params['page'] = current_page + 1
                    base_url = response.meta['base_url']
                    
                    # 添加延时避免请求过快
                    time.sleep(1)
                    
                    yield scrapy.Request(
                        url=f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}",
                        callback=self.parse,
                        meta={
                            'page': current_page + 1, 
                            'params': params,
                            'base_url': base_url
                        },
                        dont_filter=True  # 允许重复的URL
                    )
            else:
                self.logger.error(f"API返回错误: {data['reason']} - URL: {response.url}")
                
        except Exception as e:
            self.logger.error(f"解析响应时出错: {str(e)} - URL: {response.url}")
    
    def save_stock_symbols(self, symbols):
        """将股票代码保存到文件中"""
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                for symbol in symbols:
                    f.write(f"{symbol}\n")
            self.logger.info(f"成功保存 {len(symbols)} 个股票代码")
        except Exception as e:
            self.logger.error(f"保存股票代码时出错: {str(e)}")

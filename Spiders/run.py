from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.get_stock_list import StockListSpider
from scrapy import cmdline

def run_stock_list_spider():
    """获取股票列表"""
    process = CrawlerProcess(get_project_settings())
    process.crawl(StockListSpider, api_key='8371893ed4ab2b2f75b59c7fa26bf2fe')  # 替换为您的API key
    process.start()

def run_stock_detail_spider(stock_codes='sh603288,sz000858'):
    """爬取指定股票的详细信息"""
    cmdline.execute(f'scrapy crawl stock_detail -a stock_codes={stock_codes}'.split())

def run_stock_kline_spider_with_indicators(stock_codes):
    """获取带技术指标的K线数据"""
    cmdline.execute(f'scrapy crawl stock_kline -a use_file=true -a stock_codes={stock_codes} -a calc_indicators=true'.split())

def run_stock_kline_spider_without_indicators(stock_codes='sh603288'):
    """获取不带技术指标的K线数据"""
    cmdline.execute(f'scrapy crawl stock_kline -a stock_codes={stock_codes} -a calc_indicators=false'.split())

# 股票代码列表
STOCK_CODES = (
    'sz002717'
    # 'sh688426,sh688217,sh605378,sh605277,sh605196,sh605155,sh605151,sh603990,'
    # 'sh603768,sh603725,sh603633,sh603363,sh603316,sh603307,sh603286,sh603193,'
    # 'sh603172,sh603163,sh603125,sh603121,sh603097,sh603081,sh603048,sh603045,'
    # 'sh603011,sh603003,sh601083,sh600860,sh600789,sh600778,sh600503,sh600356,'
    # 'sh600237,sh600202,sz301603,sz301591,sz301548,sz301538,sz301526,sz301512,'
    # 'sz301489,sz301459,sz301390,sz301362,sz301329,sz301328,sz301320,sz301279,'
    # 'sz301261,sz301252,sz301229,sz301215,sz301199,sz301196,sz301179,sz301135,'
    # 'sz301133,sz301127,sz301115,sz301112,sz301092,sz301072,sz301069,sz301005,'
    # 'sz301002,sz300982,sz300971,sz300964,sz300946,sz300943,sz300931,sz300922,'
    # 'sz300902,sz300879,sz300863,sz300838,sz300780,sz300767,sz300739,sz300549,'
    # 'sz300510,sz300508,sz300497,sz300477,sz300471,sz300400,sz300287,sz300232,'
    # 'sz300228,sz300199,sz300092,sz002997,sz002990,sz002965,sz002952,sz002929,'
    # 'sz002921,sz002917,sz002893,sz002750,sz002733,sz002697,sz002609,sz002560,'
    # 'sz002541,sz002536,sz002448,sz002406,sz002337,sz002334,sz002249,sz002166,'
    # 'sz002139,sz002123,sz002112,sz002052,sz002031,sz001380,sz001373,sz001326,'
    # 'sz001319,sz001287,sz001266,sz000897,sz000837,sz000700,sz000678,sz000597,'
    # 'sz000584,sz0836270,sh0688288,sh0688028,sh0603507,sh0603121,sh0603101,'
    # 'sh0603097,sh0600628,sh0600158,sz0301229,sz0301199,sz0301127,sz0300912,'
    # 'sz0300905,sz0300902,sz0300753,sz0300638,sz0300559,sz0300471,sz0300444,'
    # 'sz0300228,sz0300092,sz002997,sz002990,sz002965,sz002933,sz002860,sz001380'
)

if __name__ == "__main__":
    # 运行获取股票列表的爬虫
    # run_stock_list_spider()
    
    # 运行获取股票详情的爬虫
    # run_stock_detail_spider()
    
    # 运行获取带技术指标K线数据的爬虫
    run_stock_kline_spider_with_indicators(STOCK_CODES)
    
    # 运行获取不带技术指标K线数据的爬虫
    # run_stock_kline_spider_without_indicators()
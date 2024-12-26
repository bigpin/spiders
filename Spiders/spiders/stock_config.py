# 东方财富API配置
EASTMONEY_API = {
    'base_url': 'https://push2.eastmoney.com/api/qt/stock/get',
    'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f55,f57,f58,f60,f71,f92,f105,f116,f117,f162,f167,f168,f169,f170,f171,f177,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f193,f194,f195,f196,f197',
    'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
    'wbp2u': '|0|0|0|web'
}

# 字段映射关系
FIELD_MAPPING = {
    'f58': 'stock_name',          # 股票名称
    'f43': 'new_price',           # 最新价
    'f169': 'price_change',       # 涨跌额
    'f170': 'percentage_change',   # 涨跌幅
    'f46': 'opening_price',       # 今开
    'f44': 'highest_price',       # 最高
    'f45': 'lowest_price',        # 最低
    'f60': 'closing_price',       # 昨收
    'f47': 'trading_volume',      # 成交量
    'f48': 'trading_value',       # 成交额
    'f168': 'turnover_rate',      # 换手率
    'f162': 'pe',                 # 市盈率
    'f167': 'pb'                  # 市净率
}

# 数据处理规则（除数）
FIELD_DIVISORS = {
    'new_price': 100,
    'price_change': 100,
    'percentage_change': 100,
    'opening_price': 100,
    'highest_price': 100,
    'lowest_price': 100,
    'closing_price': 100,
    'trading_volume': 100,
    'trading_value': 10000,  # 转换为亿
    'turnover_rate': 100,
    'pe': 100,
    'pb': 100
}

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://quote.eastmoney.com/',
    'Accept': '*/*'
}

# 股票代码前缀映射
STOCK_PREFIX_MAP = {
    'sh': '1',
    'sz': '0'
}


# K线数据
# stock_config.py 添加K线相关配置

# K线数据API配置
KLINE_API = {
    'base_url': 'https://push2his.eastmoney.com/api/qt/stock/kline/get',
    'fields': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
    'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
    'klt': {
        '1min': '1',    # 1分钟
        '5min': '5',    # 5分钟
        '15min': '15',  # 15分钟
        '30min': '30',  # 30分钟
        '60min': '60',  # 60分钟
        'daily': '101', # 日线
        'weekly': '102',# 周线
        'monthly': '103'# 月线
    },
    'fqt': {
        'none': '0',    # 不复权
        'forward': '1', # 前复权
        'backward': '2' # 后复权
    }
}

# K线数据字段映射
KLINE_FIELD_MAPPING = {
    0: 'date',          # 日期
    1: 'open',          # 开盘价
    2: 'close',         # 收盘价
    3: 'high',          # 最高价
    4: 'low',           # 最低价
    5: 'volume',        # 成交量
    6: 'amount',        # 成交额
    7: 'amplitude',     # 振幅
    8: 'change_rate',   # 涨跌幅
    9: 'change_amount', # 涨跌额
    10: 'turnover'      # 换手率
}

# 技术指标
# 技术指标配置
INDICATORS_CONFIG = {
    'kdj': {
        'period': 9,    # 默认周期
        'signal': 3,    # 信号周期
    },
    'macd': {
        'fast': 12,     # 快线周期
        'slow': 26,     # 慢线周期
        'signal': 9,    # 信号周期
    },
    'rsi': {
        'periods': [6, 12, 24]  # RSI周期
    },
    'boll': {
        'period': 20,   # 布林带周期
        'std': 2        # 标准差倍数
    },
    'ma': {
        'periods': [5, 10, 20, 30, 60]  # 移动平均线周期
    },
    'ema': {
        'periods': [5, 10, 20, 30, 60]  # 指数移动平均线周期
    },
    'wma': {
        'periods': [5, 10, 20, 30, 60]  # 加权移动平均线周期
    },
    'vwap': {},  # 成交量加权平均价格，不需要参数
    'atr': {
        'period': 14    # ATR周期
    },
    'dmi': {
        'length': 14,   # DMI周期
        'signal': 14    # ADX平滑周期
    },
    'cci': {
        'length': 20    # CCI周期
    },
    'obv': {},  # 能量潮指标，不需要参数
    'roc': {
        'length': 12    # ROC周期
    }
}
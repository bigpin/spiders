import scrapy
import json
import pandas as pd
from items import EastMoneyItem
from .stock_config import (
    KLINE_API,
    KLINE_FIELD_MAPPING,
    STOCK_PREFIX_MAP,
    HEADERS,
    INDICATORS_CONFIG
)
from .technical_indicators import TechnicalIndicators
import sqlite3
from datetime import datetime, timedelta

class StockKlineSpider(scrapy.Spider):
    name = "stock_kline"
    allowed_domains = ["eastmoney.com", "push2his.eastmoney.com"]
    # custom_settings = {
    #         'FEEDS': {
    #             'kline_data.csv': {
    #                 'format': 'csv',
    #                 'encoding': 'utf-8-sig',
    #                 'store_empty': False,
    #                 'overwrite': True,
    #                 'fields': [
    #                     'stock_code', 'date', 'open', 'high', 'low', 'close', 
    #                     'volume', 'amount', 'amplitude', 'change_rate', 'change_amount', 
    #                     'turnover', 'KST_9_3', 'DST_9_3', 'JST_9_3', 'MACD_12_26_9', 
    #                     'MACDh_12_26_9', 'MACDs_12_26_9', 'RSI_6', 'RSI_12', 'RSI_24', 
    #                     'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0', 'BBB_20_2.0', 'BBP_20_2.0'
    #                 ],
    #                 'headers': {
    #                     'stock_code': '股票代码',
    #                     'date': '日期',
    #                     'open': '开盘价',
    #                     'high': '最高价',
    #                     'low': '最低价',
    #                     'close': '收盘价',
    #                     'volume': '成交量',
    #                     'amount': '成交额',
    #                     'amplitude': '振幅',
    #                     'change_rate': '涨跌幅',
    #                     'change_amount': '涨跌额',
    #                     'turnover': '换手率',
    #                     'KST_9_3': 'K值',
    #                     'DST_9_3': 'D值',
    #                     'JST_9_3': 'J值',
    #                     'MACD_12_26_9': 'MACD',
    #                     'MACDh_12_26_9': 'MACD柱',
    #                     'MACDs_12_26_9': 'MACD信号',
    #                     'RSI_6': 'RSI6',
    #                     'RSI_12': 'RSI12',
    #                     'RSI_24': 'RSI24',
    #                     'BBL_20_2.0': '布林下轨',
    #                     'BBM_20_2.0': '布林中轨',
    #                     'BBU_20_2.0': '布林上轨',
    #                     'BBB_20_2.0': '布林带宽',
    #                     'BBP_20_2.0': '布林带百分比'
    #                 }
    #             }
    #         }
    #     }
    
    def __init__(self, stock_codes=None, use_file=False, stock_file='stock_list.txt', 
                 kline_type='daily', fq_type='forward', start_date=None, end_date=None, 
                 calc_indicators=True, *args, **kwargs):
        super(StockKlineSpider, self).__init__(*args, **kwargs)
        
        # 从文件读取股票代码或使用传入的股票代码
        if use_file and use_file.lower() == 'true':
            try:
                with open(stock_file, 'r', encoding='utf-8') as f:
                    self.stock_codes = [line.strip() for line in f if line.strip()]
                if not self.stock_codes:
                    self.logger.warning(f"股票代码文件 {stock_file} 为空，使用默认股票代码")
                    self.stock_codes = ['sh603288', 'sz000858']
            except FileNotFoundError:
                self.logger.error(f"找不到股票代码文件 {stock_file}，使用默认股票代码")
                self.stock_codes = ['sh603288', 'sz000858']
        else:
            self.stock_codes = stock_codes.split(',') if stock_codes else ['sh603288', 'sz000858']
        
        self.kline_type = kline_type
        self.fq_type = fq_type
        
        # 设置默认时间范围为最近一年
        from datetime import datetime, timedelta
        current_date = datetime.now()
        one_year_ago = current_date - timedelta(days=365)
        
        if not start_date:
            self.start_date = one_year_ago.strftime("%Y%m%d")  # 一年前的日期
        else:
            self.start_date = start_date
            
        if not end_date:
            self.end_date = current_date.strftime("%Y%m%d")    # 当前日期
        else:
            self.end_date = end_date
            
        self.calc_indicators = calc_indicators
        self.kline_data = {}  # 用于临时存储K线数据
        
        # 添加信号输出文件的路径
        self.signal_file = f'kdj_signals_{datetime.now().strftime("%Y%m%d")}.txt'
        # 清空信号文件
        with open(self.signal_file, 'w', encoding='utf-8') as f:
            f.write(f"股票信号分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
        
        # 初始化数据库连接
        self.conn = sqlite3.connect('stock_signals.db')
        self.cursor = self.conn.cursor()
        self.create_table()
    
    def create_table(self):
        """创建数据库表"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT,
                stock_name TEXT,
                date TEXT,
                signal TEXT,
                success_rate REAL,
                initial_price REAL,
                highest_price REAL,
                highest_price_date TEXT,
                highest_price_change_rate REAL,
                highest_price_days INTEGER,  -- 最高价格距离创建时间的天数
                lowest_price REAL,
                lowest_price_date TEXT,
                lowest_price_change_rate REAL,
                lowest_price_days INTEGER,   -- 最低价格距离创建时间的天数
                created_at TEXT,
                UNIQUE(stock_code, date, signal)
            )
        ''')
        self.conn.commit()
    
    def start_requests(self):
        for stock_code in self.stock_codes:
            # 获取股票代码前缀对应的数字
            prefix = STOCK_PREFIX_MAP.get(stock_code[:2])
            if not prefix:
                self.logger.error(f"不支持的股票代码前缀: {stock_code}")
                continue
            
            # 构建API请求参数
            params = {
                'secid': f"{prefix}.{stock_code[2:]}",
                'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': KLINE_API['klt'][self.kline_type],
                'fqt': KLINE_API['fqt'][self.fq_type],
                'ut': KLINE_API['ut'],
                'beg': self.start_date or '',
                'end': self.end_date or '',
                'lmt': '1000'  # 限制返回1000条数据
            }
            
            url = f"{KLINE_API['base_url']}?" + "&".join([f"{k}={v}" for k, v in params.items()])
            
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={'stock_code': stock_code},
                headers=HEADERS
            )
    
    def write_to_signal_file(self, content):
        """将内容写入信号文"""
        with open(self.signal_file, 'a', encoding='utf-8') as f:
            f.write(content + "\n")
        # 同时保存到数据库
        self.save_to_database(content)
    
    def save_to_database(self, content):
        """将信号保存到数据库"""
        try:
            # 解析content并插入到数据库
            lines = content.split('\n')
            for line in lines:
                if "股票:" in line:
                    try:
                        parts = line.split(',')
                        # 解析股票信息
                        stock_part = parts[0].split('股票:')[1].strip()
                        # 提取股票名称和代码
                        if '(' in stock_part and ')' in stock_part:
                            stock_name = stock_part[:stock_part.find('(')].strip()
                            stock_code = stock_part[stock_part.find('(')+1:stock_part.find(')')].strip()
                        else:
                            continue  # 如果格式不正确跳过这条记录
                        
                        # 解析其他信息
                        date_str = next((p.split(': ')[1].strip() for p in parts if '日期:' in p), None)
                        # 统一日期格式为YYYY-MM-DD
                        if date_str:
                            try:
                                date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
                            except ValueError:
                                try:
                                    date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
                                except ValueError:
                                    self.logger.error(f"无法解析日期格式: {date_str}")
                                    continue
                        else:
                            continue
                            
                        signal = next((p.split(': ')[1].strip() for p in parts if '信号:' in p), None)
                        
                        # 特殊处理信号胜率
                        success_rate_part = next((p for p in parts if '信号胜率:' in p), None)
                        if success_rate_part:
                            success_rate_str = success_rate_part.split('信号胜率:')[1].strip()
                            success_rate = float(success_rate_str.split('%')[0].strip())
                        else:
                            success_rate = None
                            
                        initial_price = next((float(p.split(': ')[1].strip()) for p in parts if '收盘价:' in p), None)

                        # 只有当所有必要信息都存在时才插入数据库
                        if all([stock_code, stock_name, date, signal, success_rate, initial_price]):
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            # 检查是否已存在相同记录
                            self.cursor.execute('''
                                SELECT COUNT(*) FROM stock_data 
                                WHERE stock_code=? AND date=? AND signal=?
                            ''', (stock_code, date, signal))
                            
                            if self.cursor.fetchone()[0] == 0:
                                self.cursor.execute('''
                                    INSERT INTO stock_data (
                                        stock_code, stock_name, date, signal, 
                                        success_rate, initial_price, created_at
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''', (stock_code, stock_name, date, signal, 
                                     success_rate, initial_price, current_time))
                            
                    except (IndexError, ValueError) as e:
                        self.logger.error(f"解析信号行时出错: {line}")
                        self.logger.error(str(e))
                        continue  # 跳过这条记录，继续处理下一条
            
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"保存到数据库时出错: {str(e)}")
            self.conn.rollback()  # 发生错误时回滚事务
    
    def parse(self, response):
        try:
            data = json.loads(response.text)
            if data.get('data') and data['data'].get('klines'):
                stock_code = response.meta['stock_code']
                klines = data['data']['klines']
                
                # 检查数据量是否足够
                if len(klines) < 16:
                    self.logger.warning(f"票 {stock_code} 的数据量不足16天，跳过分析")
                    return
                
                # 将K线数据转换为DataFrame
                kline_data = []
                for kline in klines:
                    values = kline.split(',')
                    item = {}
                    for i, value in enumerate(values):
                        field = KLINE_FIELD_MAPPING.get(i)
                        if field:
                            if field != 'date':
                                try:
                                    item[field] = float(value)
                                except ValueError:
                                    item[field] = None
                            else:
                                item[field] = value
                    kline_data.append(item)
                
                # 创建DataFrame
                df = pd.DataFrame(kline_data)
                df.set_index('date', inplace=True)
                
                # 算技术指标
                if self.calc_indicators:
                    df = TechnicalIndicators.calculate_all(df, INDICATORS_CONFIG)
                    
                    # 分析信号
                    kdj_analysis = self.analyze_signals(df)
                    
                    # 只要有满足条件的信号写入文件
                    if kdj_analysis['recent_signals']:
                        # 统计最近5天内的不同信号类型数量
                        recent_signal_types = set(signal['signal'] for signal in kdj_analysis['recent_signals'])
                        
                        # 有当出现三种以上不同信号时才输出
                        if len(recent_signal_types) >= 3:
                            # 写入文件
                            self.write_to_signal_file(f"\n股票 {data['data']['name']}({stock_code}) 股票信号分析结果")
                            self.write_to_signal_file(f"总体成功率: {kdj_analysis['overall_success_rate']:.2f}%")
                            self.write_to_signal_file(f"总信号数: {kdj_analysis['total_signals']}")
                            self.write_to_signal_file(f"总成功数: {kdj_analysis['total_success']}")
                            
                            # 输出最近信号
                            self.write_to_signal_file("\n最近3天出现的高胜率信号：")
                            for signal in kdj_analysis['recent_signals']:
                                # 输出信号相关信息
                                if signal:
                                    signal_info = []
                                    
                                    # 基础信息
                                    signal_info.extend([
                                        f"日期: {signal['date']}",
                                        f"信号类型: {signal['signal_type']}",
                                        f"信号: {signal['signal']}",
                                        f"信号胜率: {signal['signal_success_rate']:.2f}%",
                                        f"(历史出现: {signal['signal_total']}次)",
                                        f"整体胜率: {signal['overall_success_rate']:.2f}%",
                                        f"收盘价: {signal['close']:.2f}"
                                    ])
                                    
                                    # 根据信号类型添加对应的指标信息
                                    if signal['signal_type'].startswith('kdj'):
                                        signal_info.extend([
                                            f"K值: {signal.get('k_value', 'N/A'):.2f}",
                                            f"D值: {signal.get('d_value', 'N/A'):.2f}",
                                            f"J值: {signal.get('j_value', 'N/A'):.2f}"
                                        ])
                                    elif signal['signal_type'].startswith('macd'):
                                        signal_info.extend([
                                            f"MACD: {signal.get('macd', 'N/A'):.4f}",
                                            f"MACD信号: {signal.get('macd_signal', 'N/A'):.4f}"
                                        ])
                                    elif signal['signal_type'].startswith('rsi'):
                                        signal_info.extend([
                                            f"RSI(6): {signal.get('RSI_6', 'N/A'):.2f}",
                                            f"RSI(12): {signal.get('RSI_12', 'N/A'):.2f}"
                                        ])
                                    elif signal['signal_type'].startswith('boll'):
                                        signal_info.extend([
                                            f"布林下轨: {signal.get('BBL_20_2.0', 'N/A'):.2f}",
                                            f"布林中轨: {signal.get('BBM_20_2.0', 'N/A'):.2f}",
                                            f"布林上轨: {signal.get('BBU_20_2.0', 'N/A'):.2f}"
                                        ])
                                    elif signal['signal_type'].startswith('ma'):
                                        signal_info.extend([
                                            f"MA5: {signal.get('SMA_5', 'N/A'):.2f}",
                                            f"MA20: {signal.get('SMA_20', 'N/A'):.2f}"
                                        ])
                                    elif signal['signal_type'].startswith('dmi'):
                                        signal_info.extend([
                                            f"DMP(14): {signal.get('DMP_14', 'N/A'):.2f}",
                                            f"DMN(14): {signal.get('DMN_14', 'N/A'):.2f}",
                                            f"ADX(14): {signal.get('ADX_14', 'N/A'):.2f}"
                                        ])
                                    elif signal['signal_type'].startswith('cci'):
                                        signal_info.extend([
                                            f"CCI(20): {signal.get('CCI_20', 'N/A'):.2f}"
                                        ])
                                    elif signal['signal_type'].startswith('roc'):
                                        signal_info.extend([
                                            f"ROC(12): {signal.get('ROC_12', 'N/A'):.2f}"
                                        ])
                                    
                                    # 将所有信息用逗号连接并输出
                                    signal_info_str = ", ".join(signal_info)
                                    self.logger.info(signal_info_str)
                                    # 同时写入信号文件
                                    self.write_to_signal_file(f"股票: {data['data']['name']}({stock_code}), {signal_info_str}")
                            self.write_to_signal_file("-" * 80)  # 分隔线
                            
                            # 同时保持控制台输出
                            self.logger.info(f"股票 {stock_code} KDJ信号分析结果已写入文件: {self.signal_file}")
                        else:
                            self.logger.info(f"股票 {stock_code} 最近5天的不同信号类型少于2，跳过输出")
                    else:
                        self.logger.info(f"股票 {stock_code} 最近5天没有满足条件的高胜信号")
                
                # 结果数据
                for index, row in df.iterrows():
                    item = dict(row)
                    item.update({
                        'stock_code': stock_code,
                        'date': index,
                        'type': self.kline_type,
                        'fq_type': self.fq_type
                    })
                    
                    # print(f"获取到K线数据: {stock_code} - {index}")
                    yield item
                    
            else:
                self.logger.error(f"未获取到股票 {response.meta['stock_code']} 的K线数据")
                
        except Exception as e:
            error_msg = f"解析股票 {response.meta['stock_code']} 的K线数据出错: {str(e)}"
            self.logger.error(error_msg)
            self.write_to_signal_file(f"\n错误: {error_msg}")
            import traceback
            self.write_to_signal_file(traceback.format_exc())
        
        # 获取股票名称
        stock_name = data['data']['name'] if 'data' in data and 'name' in data['data'] else '未知'
        
        # 更新数据库中的最高价格
        self.update_price_extremes(stock_code, stock_name, df)
    
    def update_price_extremes(self, stock_code, stock_name, df):
        """更新数据库中记录的股票在日志记录时间14天内的最高和最低价格"""
        try:
            # 检查数据库中是否存在该股票的记录，只获取必要字段
            self.cursor.execute('''
                SELECT id, initial_price, created_at
                FROM stock_data 
                WHERE stock_code=? AND date>=?
            ''', (stock_code, (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")))
            
            records = self.cursor.fetchall()
            if records:
                if not df.empty:
                    # 遍历所有记录，统计14天内的最高和最低价格
                    for record in records:
                        record_id, initial_price, created_at = record
                        
                        # 如果initial_price为None，跳过这条记录
                        if initial_price is None:
                            self.logger.warning(f"记录ID {record_id} 的initial_price为None，跳过更新")
                            continue
                            
                        try:
                            # 将created_at转换为日期格式（去掉时分秒）
                            created_date = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                            
                            # 获取created_at日期在DataFrame中的位置
                            created_idx = df.index.get_loc(created_date)
                            # 获取created_at日期后一天到14天内的数据
                            future_data = df.iloc[created_idx + 1:created_idx + 15]  # +15是因为切片是左闭右开
                            
                            if not future_data.empty:
                                # 确保close列中没有None值
                                future_data = future_data[future_data['close'].notna()]
                                
                                if not future_data.empty:
                                    # 计算最高价格
                                    highest_price = future_data['close'].max()
                                    highest_price_date = future_data['close'].idxmax()
                                    highest_change_rate = ((highest_price - initial_price) / initial_price * 100)
                                    highest_days = (datetime.strptime(highest_price_date, "%Y-%m-%d") - 
                                                  datetime.strptime(created_date, "%Y-%m-%d")).days
                                    
                                    # 计算最低价格
                                    lowest_price = future_data['close'].min()
                                    lowest_price_date = future_data['close'].idxmin()
                                    lowest_change_rate = ((lowest_price - initial_price) / initial_price * 100)
                                    lowest_days = (datetime.strptime(lowest_price_date, "%Y-%m-%d") - 
                                                 datetime.strptime(created_date, "%Y-%m-%d")).days
                                    
                                    # 总是更新14天内的最高和最低价格
                                    self.cursor.execute('''
                                        UPDATE stock_data
                                        SET highest_price=?, 
                                            highest_price_date=?,
                                            highest_price_change_rate=?,
                                            highest_price_days=?,
                                            lowest_price=?,
                                            lowest_price_date=?,
                                            lowest_price_change_rate=?,
                                            lowest_price_days=?
                                        WHERE id=?
                                    ''', (highest_price, highest_price_date, highest_change_rate, highest_days,
                                         lowest_price, lowest_price_date, lowest_change_rate, lowest_days,
                                         record_id))
                        except (KeyError, ValueError) as e:
                            self.logger.error(f"处理日期时出错: {created_at}, 错误: {str(e)}")
                            continue
                
                self.conn.commit()
        except Exception as e:
            self.logger.error(f"更新价格极值时出错: {str(e)}")
            self.conn.rollback()
    
    def analyze_signals(self, df):
        """分析多个技术指标的信号"""
        signals = []
        signal_stats = {
            # KDJ信号
            'kdj_oversold': {'success': 0, 'total': 0},
            'kdj_golden_cross': {'success': 0, 'total': 0},
            'kdj_divergence': {'success': 0, 'total': 0},
            # MACD信号
            'macd_golden_cross': {'success': 0, 'total': 0},
            'macd_zero_cross': {'success': 0, 'total': 0},
            'macd_divergence': {'success': 0, 'total': 0},
            # RSI信号
            'rsi_oversold': {'success': 0, 'total': 0},
            'rsi_golden_cross': {'success': 0, 'total': 0},
            # BOLL信号
            'boll_bottom_touch': {'success': 0, 'total': 0},
            'boll_width_expand': {'success': 0, 'total': 0},
            # MA信号
            'ma_golden_cross': {'success': 0, 'total': 0},  # 短期均线上穿长期均线
            'ma_support': {'success': 0, 'total': 0},       # 价格在均线支撑位反弹
            # DMI信号
            'dmi_golden_cross': {'success': 0, 'total': 0}, # DI+上穿DI-
            'dmi_adx_strong': {'success': 0, 'total': 0},   # ADX大于某个阈值，表示趋势强烈
            # CCI信号
            'cci_oversold': {'success': 0, 'total': 0},     # CCI超卖
            'cci_zero_cross': {'success': 0, 'total': 0},   # CCI上穿零轴
            # ROC信号
            'roc_zero_cross': {'success': 0, 'total': 0},   # ROC上穿零轴
            'roc_divergence': {'success': 0, 'total': 0}    # ROC底背离
        }
        
        # 确保数据按日期排序
        df = df.sort_index()
        
        # 检查数据量是否足够
        if len(df) < 16:  # 至少需要16天的数据
            return {
                'signal_stats': {},
                'overall_success_rate': 0,
                'total_signals': 0,
                'total_success': 0,
                'signals': [],
                'recent_signals': []
            }
        
        for i in range(1, len(df)-16):
            current_row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            signal = None
            signal_type = None
            
            # KDJ信号判断
            if current_row['K_9_3'] < 20 and current_row['D_9_3'] < 20:
                signal = 'KDJ超卖'
                signal_type = 'kdj_oversold'
            elif (prev_row['K_9_3'] < prev_row['D_9_3'] and 
                  current_row['K_9_3'] > current_row['D_9_3']):
                signal = 'KDJ金叉'
                signal_type = 'kdj_golden_cross'
            elif (current_row['close'] < df.iloc[i-5:i]['close'].min() and 
                  current_row['K_9_3'] > df.iloc[i-5:i]['K_9_3'].min()):
                signal = 'KDJ底背离'
                signal_type = 'kdj_divergence'
                
            # MACD信号判断
            elif (prev_row.get('MACD_12_26_9') is not None and 
                  prev_row['MACD_12_26_9'] < prev_row['MACDs_12_26_9'] and 
                  current_row['MACD_12_26_9'] > current_row['MACDs_12_26_9']):
                signal = 'MACD金叉'
                signal_type = 'macd_golden_cross'
            elif (prev_row.get('MACD_12_26_9') is not None and 
                  prev_row['MACD_12_26_9'] < 0 and 
                  current_row['MACD_12_26_9'] > 0):
                signal = 'MACD零轴上穿'
                signal_type = 'macd_zero_cross'
            elif (current_row['close'] < df.iloc[i-5:i]['close'].min() and 
                  current_row['MACD_12_26_9'] > df.iloc[i-5:i]['MACD_12_26_9'].min()):
                signal = 'MACD底背离'
                signal_type = 'macd_divergence'
                
            # RSI信号判断
            elif current_row['RSI_6'] < 20:
                signal = 'RSI超卖'
                signal_type = 'rsi_oversold'
            elif (prev_row['RSI_6'] < prev_row['RSI_12'] and 
                  current_row['RSI_6'] > current_row['RSI_12']):
                signal = 'RSI金叉'
                signal_type = 'rsi_golden_cross'
                
            # BOLL信号判断
            elif (current_row['close'] <= current_row['BBL_20_2.0'] * 1.01):  # 接近下轨
                signal = 'BOLL下轨支撑'
                signal_type = 'boll_bottom_touch'
            elif (current_row['BBB_20_2.0'] > prev_row['BBB_20_2.0'] * 1.1):  # 带宽扩张
                signal = 'BOLL带宽扩张'
                signal_type = 'boll_width_expand'
            
            # MA信号判断
            elif (prev_row['SMA_5'] < prev_row['SMA_20'] and 
                  current_row['SMA_5'] > current_row['SMA_20']):
                signal = 'MA5上穿MA20'
                signal_type = 'ma_golden_cross'
            elif (current_row['close'] > current_row['SMA_20'] * 0.99 and 
                  current_row['close'] < current_row['SMA_20'] * 1.01):
                signal = 'MA20支撑'
                signal_type = 'ma_support'
            
            # DMI信号判断
            elif (prev_row['DMP_14'] < prev_row['DMN_14'] and 
                  current_row['DMP_14'] > current_row['DMN_14'] and 
                  current_row['ADX_14'] > 20):
                signal = 'DMI金叉'
                signal_type = 'dmi_golden_cross'
            elif current_row['ADX_14'] > 30:  # ADX大于30表示趋势强烈
                signal = 'ADX强势'
                signal_type = 'dmi_adx_strong'
            
            # CCI信号判断
            elif current_row['CCI_20'] < -100:  # CCI超卖
                signal = 'CCI超卖'
                signal_type = 'cci_oversold'
            elif (prev_row['CCI_20'] < 0 and current_row['CCI_20'] > 0):  # CCI上穿零轴
                signal = 'CCI零轴上穿'
                signal_type = 'cci_zero_cross'
            
            # ROC信号判断
            elif (prev_row['ROC_12'] < 0 and current_row['ROC_12'] > 0):  # ROC上穿零轴
                signal = 'ROC零轴上穿'
                signal_type = 'roc_zero_cross'
            elif (current_row['close'] < df.iloc[i-5:i]['close'].min() and 
                  current_row['ROC_12'] > df.iloc[i-5:i]['ROC_12'].min()):  # ROC底背离
                signal = 'ROC底背离'
                signal_type = 'roc_divergence'

            if signal:
                signal_stats[signal_type]['total'] += 1
                
                # 检查未来10天是否有5%以上涨幅
                future_prices_10 = df.iloc[i+1:i+11]['close']
                max_future_return = ((future_prices_10.max() - current_row['close']) / 
                                   current_row['close'] * 100)
                
                success = max_future_return >= 5
                
                if success:
                    signal_stats[signal_type]['success'] += 1
                    
                signals.append({
                    'date': df.index[i],
                    'signal_type': signal_type,
                    'signal': signal,
                    'close': current_row['close'],
                    'k_value': current_row.get('K_9_3'),
                    'd_value': current_row.get('D_9_3'),
                    'j_value': current_row.get('J_9_3'),
                    'macd': current_row.get('MACD_12_26_9'),
                    'macd_signal': current_row.get('MACDs_12_26_9'),
                    'rsi_6': current_row.get('RSI_6'),
                    'rsi_12': current_row.get('RSI_12'),
                    'cci': current_row.get('CCI_20'),
                    'roc': current_row.get('ROC_12'),
                    'dmi_plus': current_row.get('DMP_14'),
                    'dmi_minus': current_row.get('DMN_14'),
                    'adx': current_row.get('ADX_14'),
                    'max_return': max_future_return,
                    'success': success
                })

        # 计算总体统计
        total_success = sum(stats['success'] for stats in signal_stats.values())
        total_signals = sum(stats['total'] for stats in signal_stats.values())
        overall_success_rate = (total_success / total_signals * 100) if total_signals > 0 else 0
        
        # 计算每种信号的成功率
        success_rates = {}
        for signal_type, stats in signal_stats.items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            success_rates[signal_type] = {
                'success_rate': success_rate,
                'total_signals': stats['total'],
                'success_count': stats['success']
            }

        # 最近信号检查部分
        recent_signals = []
        if len(df) >= 4:  # 改为4天以确保有足够数据计算3天的信号
            last_3_days = df.iloc[-3:].copy()  # 改为最近3天
            for i in range(len(last_3_days)):
                current_row = last_3_days.iloc[i]
                if i > 0:
                    prev_row = last_3_days.iloc[i-1]
                else:
                    prev_row = df.iloc[-4]  # 获取第4天前的数据为首日的前一天
                
                signal = None
                signal_type = None
                
                # [这里重复上面的信号判断逻辑，但使用last_3_days的数据]
                # KDJ信号判断
                if current_row['K_9_3'] < 20 and current_row['D_9_3'] < 20:
                    signal = 'KDJ超卖'
                    signal_type = 'kdj_oversold'
                elif (prev_row['K_9_3'] < prev_row['D_9_3'] and 
                      current_row['K_9_3'] > current_row['D_9_3']):
                    signal = 'KDJ金叉'
                    signal_type = 'kdj_golden_cross'
                elif (current_row['close'] < df.iloc[-3:].iloc[:i+1]['close'].min() and 
                      current_row['K_9_3'] > df.iloc[-3:].iloc[:i+1]['K_9_3'].min()):
                    signal = 'KDJ底背离'
                    signal_type = 'kdj_divergence'
                    
                # MACD信号判断
                elif (prev_row.get('MACD_12_26_9') is not None and 
                      prev_row['MACD_12_26_9'] < prev_row['MACDs_12_26_9'] and 
                      current_row['MACD_12_26_9'] > current_row['MACDs_12_26_9']):
                    signal = 'MACD金叉'
                    signal_type = 'macd_golden_cross'
                elif (prev_row.get('MACD_12_26_9') is not None and 
                      prev_row['MACD_12_26_9'] < 0 and 
                      current_row['MACD_12_26_9'] > 0):
                    signal = 'MACD零轴上穿'
                    signal_type = 'macd_zero_cross'
                elif (current_row['close'] < df.iloc[-3:].iloc[:i+1]['close'].min() and 
                      current_row['MACD_12_26_9'] > df.iloc[-3:].iloc[:i+1]['MACD_12_26_9'].min()):
                    signal = 'MACD底背离'
                    signal_type = 'macd_divergence'
                    
                # RSI信号判断
                elif current_row['RSI_6'] < 20:
                    signal = 'RSI超卖'
                    signal_type = 'rsi_oversold'
                elif (prev_row['RSI_6'] < prev_row['RSI_12'] and 
                      current_row['RSI_6'] > current_row['RSI_12']):
                    signal = 'RSI金叉'
                    signal_type = 'rsi_golden_cross'
                    
                # BOLL信号判断
                elif (current_row['close'] <= current_row['BBL_20_2.0'] * 1.01):  # 接近下轨
                    signal = 'BOLL下轨支撑'
                    signal_type = 'boll_bottom_touch'
                elif (current_row['BBB_20_2.0'] > prev_row['BBB_20_2.0'] * 1.1):  # 带宽扩张
                    signal = 'BOLL带宽扩张'
                    signal_type = 'boll_width_expand'
                
                # MA信号判断
                elif (prev_row['SMA_5'] < prev_row['SMA_20'] and 
                      current_row['SMA_5'] > current_row['SMA_20']):
                    signal = 'MA5上穿MA20'
                    signal_type = 'ma_golden_cross'
                elif (current_row['close'] > current_row['SMA_20'] * 0.99 and 
                      current_row['close'] < current_row['SMA_20'] * 1.01):
                    signal = 'MA20支撑'
                    signal_type = 'ma_support'
                
                # DMI信号判断
                elif (prev_row['DMP_14'] < prev_row['DMN_14'] and 
                      current_row['DMP_14'] > current_row['DMN_14'] and 
                      current_row['ADX_14'] > 20):
                    signal = 'DMI金叉'
                    signal_type = 'dmi_golden_cross'
                elif current_row['ADX_14'] > 30:  # ADX大于30表示趋势强烈
                    signal = 'ADX强势'
                    signal_type = 'dmi_adx_strong'
                
                # CCI信号判断
                elif current_row['CCI_20'] < -100:  # CCI超卖
                    signal = 'CCI超卖'
                    signal_type = 'cci_oversold'
                elif (prev_row['CCI_20'] < 0 and current_row['CCI_20'] > 0):  # CCI上穿零轴
                    signal = 'CCI零轴上穿'
                    signal_type = 'cci_zero_cross'
                
                # ROC信号判断
                elif (prev_row['ROC_12'] < 0 and current_row['ROC_12'] > 0):  # ROC上穿零轴
                    signal = 'ROC零轴上穿'
                    signal_type = 'roc_zero_cross'
                elif (current_row['close'] < df.iloc[-3:].iloc[:i+1]['close'].min() and 
                      current_row['ROC_12'] > df.iloc[-3:].iloc[:i+1]['ROC_12'].min()):  # ROC底背离
                    signal = 'ROC底背离'
                    signal_type = 'roc_divergence'

                if signal:
                    signal_stats[signal_type]['total'] += 1
                    
                    # 检查未来10天是否有5%以上涨幅
                    future_prices_10 = df.iloc[i+1:i+11]['close']
                    max_future_return = ((future_prices_10.max() - current_row['close']) / 
                                           current_row['close'] * 100)
                    
                    success = max_future_return >= 5
                    
                    if success:
                        signal_stats[signal_type]['success'] += 1
                        
                    signals.append({
                        'date': df.index[i],
                        'signal_type': signal_type,
                        'signal': signal,
                        'close': current_row['close'],
                        'k_value': current_row.get('K_9_3'),
                        'd_value': current_row.get('D_9_3'),
                        'j_value': current_row.get('J_9_3'),
                        'macd': current_row.get('MACD_12_26_9'),
                        'macd_signal': current_row.get('MACDs_12_26_9'),
                        'rsi_6': current_row.get('RSI_6'),
                        'rsi_12': current_row.get('RSI_12'),
                        'cci': current_row.get('CCI_20'),
                        'roc': current_row.get('ROC_12'),
                        'dmi_plus': current_row.get('DMP_14'),
                        'dmi_minus': current_row.get('DMN_14'),
                        'adx': current_row.get('ADX_14'),
                        'max_return': max_future_return,
                        'success': success
                    })

                if (signal and 
                    signal_stats[signal_type]['total'] > 8 and 
                    success_rates[signal_type]['success_rate'] >= 60 and  
                    overall_success_rate >= 50):
                    
                    # 根据信号类型收集对应的指标数据
                    signal_data = {
                        'date': last_3_days.index[i],
                        'signal_type': signal_type,
                        'signal': signal,
                        'close': current_row['close'],
                        'signal_total': signal_stats[signal_type]['total'],
                        'signal_success_rate': success_rates[signal_type]['success_rate'],
                        'overall_success_rate': overall_success_rate
                    }
                    
                    # 添加对应的技术指标数据
                    if signal_type.startswith('kdj'):
                        signal_data.update({
                            'k_value': current_row.get('K_9_3'),
                            'd_value': current_row.get('D_9_3'),
                            'j_value': current_row.get('J_9_3')
                        })
                    elif signal_type.startswith('macd'):
                        signal_data.update({
                            'macd': current_row.get('MACD_12_26_9'),
                            'macd_signal': current_row.get('MACDs_12_26_9')
                        })
                    elif signal_type.startswith('rsi'):
                        signal_data.update({
                            'RSI_6': current_row.get('RSI_6'),
                            'RSI_12': current_row.get('RSI_12')
                        })
                    elif signal_type.startswith('boll'):
                        signal_data.update({
                            'BBL_20_2.0': current_row.get('BBL_20_2.0'),
                            'BBM_20_2.0': current_row.get('BBM_20_2.0'),
                            'BBU_20_2.0': current_row.get('BBU_20_2.0')
                        })
                    elif signal_type.startswith('ma'):
                        signal_data.update({
                            'SMA_5': current_row.get('SMA_5'),
                            'SMA_20': current_row.get('SMA_20')
                        })
                    elif signal_type.startswith('dmi'):
                        signal_data.update({
                            'DMP_14': current_row.get('DMP_14'),
                            'DMN_14': current_row.get('DMN_14'),
                            'ADX_14': current_row.get('ADX_14')
                        })
                    elif signal_type.startswith('cci'):
                        signal_data.update({
                            'CCI_20': current_row.get('CCI_20')
                        })
                    elif signal_type.startswith('roc'):
                        signal_data.update({
                            'ROC_12': current_row.get('ROC_12')
                        })
                    
                    recent_signals.append(signal_data)

        return {
            'signal_stats': success_rates,
            'overall_success_rate': overall_success_rate,
            'total_signals': total_signals,
            'total_success': total_success,
            'signals': signals,
            'recent_signals': recent_signals
        }
    
    def close(self, reason):
        """关闭数据库连接"""
        self.conn.close()
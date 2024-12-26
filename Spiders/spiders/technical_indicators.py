# technical_indicators.py
import pandas as pd
import pandas_ta as ta
import numpy as np

class TechnicalIndicators:
    @staticmethod
    def calculate_kdj(df, period=9, signal=3):
        """计算KDJ指标"""
        # 计算KDJ
        df.ta.kdj(high='high', low='low', close='close', period=period, signal=signal, append=True)
        return df
    
    @classmethod
    def calculate_macd(cls, df, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        # 计算快线和慢线的指数移动平均
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()
        
        # 计算MACD线（快线与慢线的差）
        macd = exp1 - exp2
        # 计算信号线（MACD的移动平均线）
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        # 计算MACD柱状图（MACD线与信号线的差）
        histogram = macd - signal_line
        
        # 创建一个新的DataFrame来存储结果
        macd_df = pd.DataFrame({
            f'MACD_{fast}_{slow}_{signal}': macd,
            f'MACDs_{fast}_{slow}_{signal}': signal_line,
            f'MACDh_{fast}_{slow}_{signal}': histogram
        })
        
        # 直接将结果列添加到原始DataFrame
        df[f'MACD_{fast}_{slow}_{signal}'] = macd
        df[f'MACDs_{fast}_{slow}_{signal}'] = signal_line
        df[f'MACDh_{fast}_{slow}_{signal}'] = histogram
        
        return df
    
    @staticmethod
    def calculate_rsi(df, periods=[6, 12, 24]):
        """计算RSI指标"""
        for period in periods:
            df.ta.rsi(close='close', length=period, append=True)
        return df
    
    @staticmethod
    def calculate_boll(df, period=20, std=2):
        """计算布林带指标"""
        df.ta.bbands(close='close', length=period, std=std, append=True)
        return df
    
    @staticmethod
    def calculate_ma(df, periods=[5, 10, 20, 30, 60]):
        """计算移动平均线"""
        for period in periods:
            df.ta.sma(close='close', length=period, append=True)
        return df
    
    @staticmethod
    def calculate_ema(df, periods=[5, 10, 20, 30, 60]):
        """计算指数移动平均线"""
        for period in periods:
            df.ta.ema(close='close', length=period, append=True)
        return df
    
    @staticmethod
    def calculate_wma(df, periods=[5, 10, 20, 30, 60]):
        """计算加权移动平均线"""
        for period in periods:
            df.ta.wma(close='close', length=period, append=True)
        return df
    
    @staticmethod
    def calculate_vwap(df):
        """计算成交量加权平均价格"""
        try:
            # 确保数据按日期排序
            df = df.sort_index()
            
            # 计算典型价格 (typical price)
            df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
            
            # 计算成交量乘以典型价格的累计和
            cumulative_tp_vol = (df['typical_price'] * df['volume']).cumsum()
            
            # 计算成交量的累计和
            cumulative_vol = df['volume'].cumsum()
            
            # 计算VWAP
            df['VWAP'] = cumulative_tp_vol / cumulative_vol
            
            # 删除临时列
            df = df.drop('typical_price', axis=1)
            
            return df
        except Exception as e:
            print(f"计算VWAP时出错: {str(e)}")
            return df
    
    @staticmethod
    def calculate_atr(df, period=14):
        """计算平均真实波幅"""
        df.ta.atr(high='high', low='low', close='close', length=period, append=True)
        return df
    
    @staticmethod
    def calculate_dmi(df, length=14, signal=14):
        """计算动向指标"""
        df.ta.adx(high='high', low='low', close='close', length=length, signal=signal, append=True)
        return df
    
    @staticmethod
    def calculate_cci(df, length=20):
        """计算顺势指标"""
        try:
            # 确保数据按日期排序
            df = df.sort_index()
            
            # 计算典型价格
            tp = (df['high'] + df['low'] + df['close']) / 3
            
            # 计算移动平均
            ma = tp.rolling(window=length).mean()
            
            # 计算平均偏差
            md = tp.rolling(window=length).apply(lambda x: abs(x - x.mean()).mean())
            
            # 计算CCI
            df['CCI_20'] = (tp - ma) / (0.015 * md)
            
            return df
        except Exception as e:
            print(f"计算CCI时出错: {str(e)}")
            return df
    
    @staticmethod
    def calculate_obv(df):
        """计算能量潮指标"""
        df.ta.obv(close='close', volume='volume', append=True)
        return df
    
    @staticmethod
    def calculate_roc(df, length=12):
        """计算变动率指标"""
        df.ta.roc(close='close', length=length, append=True)
        return df
    
    @classmethod
    def calculate_all(cls, df, config):
        """计算所有技术指标"""
        # 确保数据按时间排序
        df = df.sort_index()
        
        # 计算KDJ
        df = cls.calculate_kdj(df, 
                              period=config['kdj']['period'],
                              signal=config['kdj']['signal'])
        
        # 计算MACD
        df = cls.calculate_macd(df,
                               fast=config['macd']['fast'],
                               slow=config['macd']['slow'],
                               signal=config['macd']['signal'])
        
        # 计算RSI
        df = cls.calculate_rsi(df, periods=config['rsi']['periods'])
        
        # 计算布林带
        df = cls.calculate_boll(df,
                               period=config['boll']['period'],
                               std=config['boll']['std'])
        
        # 计算其他指标
        if 'ma' in config:
            df = cls.calculate_ma(df, periods=config['ma']['periods'])
        if 'ema' in config:
            df = cls.calculate_ema(df, periods=config['ema']['periods'])
        if 'wma' in config:
            df = cls.calculate_wma(df, periods=config['wma']['periods'])
        if 'vwap' in config:
            df = cls.calculate_vwap(df)
        if 'atr' in config:
            df = cls.calculate_atr(df, period=config['atr']['period'])
        if 'dmi' in config:
            df = cls.calculate_dmi(df, length=config['dmi']['length'], signal=config['dmi']['signal'])
        if 'cci' in config:
            df = cls.calculate_cci(df, length=config['cci']['length'])
        if 'obv' in config:
            df = cls.calculate_obv(df)
        if 'roc' in config:
            df = cls.calculate_roc(df, length=config['roc']['length'])
        
        return df

def predict_limit_up_probability(self, stock_code: str, market: str = "sh", symbol: str = None) -> dict:
    """
    优化后的股票涨停概率预测，增加历史涨停概率评分项
    """
    try:
        # 获取股票数据
        file_path = f'{self.downloader.folder}/{stock_code}_{self.downloader.stocks[stock_code]}_{self.downloader.start_date}_{self.downloader.end_date}.csv'
        stock_data = self.downloader.read_csv(file_path)

        if stock_data is None or stock_data.empty:
            return {"probability": 0, "status": "数据不足"}

        # 获取最近 30 天的数据
        recent_data = stock_data.tail(30)
        if len(recent_data) < 3:
            return {"probability": 0, "status": "数据不足"}

        this_day = recent_data.iloc[-1]
        last_day = recent_data.iloc[-2]

        # 1. 价格变动评分 (20%)
        price_change = ((float(this_day['收盘']) - float(last_day['收盘'])) / float(last_day['收盘'])) * 100
        price_score = 100 / (1 + abs(price_change - 3))  # 非线性评分

        # 2. 换手率评分 (15%)
        turnover = float(this_day['换手率'])
        turnover_score = 100 / (1 + abs(turnover - 3))  # 非线性评分

        # 3. 资金流向评分 (25%)
        # 获取近30日资金流向数据
        fund_flow = ak.stock_individual_fund_flow(stock=stock_code, market=market)
        fund_flow = fund_flow.tail(30)  # 取最近30天数据

        if fund_flow.empty:
            fund_score = 50  # 默认值
        else:
            # 主力资金净流入评分
            main_net_inflow = fund_flow['主力净流入'].astype(float)
            main_inflow_score = (
                100 if main_net_inflow.iloc[-1] > 0 and main_net_inflow.diff().iloc[-1] > 0 else
                80 if main_net_inflow.iloc[-1] > 0 else
                50
            )

            # 大单买入占比评分
            big_order_ratio = fund_flow['大单买入占比'].astype(float)
            big_order_score = (
                100 if big_order_ratio.iloc[-1] > 20 else
                80 if 10 <= big_order_ratio.iloc[-1] <= 20 else
                50
            )

            # 资金流向趋势评分
            slope = np.polyfit(range(len(fund_flow)), fund_flow['主力净流入'].astype(float), 1)[0]
            trend_score = 100 if slope > 0 else 50

            # 资金流向综合评分
            fund_score = (
                main_inflow_score * 0.4 +  # 主力资金净流入权重 40%
                big_order_score * 0.3 +    # 大单买入占比权重 30%
                trend_score * 0.3          # 资金流向趋势权重 30%
            )

        # 4. 市场情绪评分 (20%)
        # 获取近30日市场情绪数据
        if symbol is None:
            symbol = f"SZ{stock_code}" if market == "sz" else f"SH{stock_code}"
        emotion_data = ak.stock_hot_rank_detail_em(symbol=symbol)
        emotion_data = emotion_data.tail(30)  # 取最近30天数据

        if emotion_data.empty:
            emotion_score = 50  # 默认值
        else:
            # 排名评分
            rank = emotion_data['排名'].astype(float)
            rank_score = (
                100 if rank.iloc[-1] <= rank.quantile(0.1).iloc[-1] else
                80 if rank.iloc[-1] <= rank.quantile(0.2).iloc[-1] else
                50
            )

            # 新晋粉丝评分
            new_fans = emotion_data['新晋粉丝'].astype(float)
            new_fans_slope = np.polyfit(range(len(new_fans)), new_fans, 1)[0]
            new_fans_score = (
                100 if new_fans_slope > 0 else
                80 if new_fans.iloc[-1] > new_fans.iloc[-2] else
                50
            )

            # 铁杆粉丝评分
            loyal_fans = emotion_data['铁杆粉丝'].astype(float)
            loyal_fans_slope = np.polyfit(range(len(loyal_fans)), loyal_fans, 1)[0]
            loyal_fans_score = (
                100 if loyal_fans_slope > 0 else
                80 if loyal_fans.iloc[-1] > loyal_fans.iloc[-2] else
                50
            )

            # 情绪趋势评分
            emotion_slope = np.polyfit(range(len(emotion_data)), emotion_data['排名'].astype(float), 1)[0]
            emotion_trend_score = 100 if emotion_slope < 0 else 50  # 排名下降表示情绪上升

            # 市场情绪综合评分
            emotion_score = (
                rank_score * 0.3 +         # 排名权重 30%
                new_fans_score * 0.25 +   # 新晋粉丝权重 25%
                loyal_fans_score * 0.25 + # 铁杆粉丝权重 25%
                emotion_trend_score * 0.2 # 情绪趋势权重 20%
            )

        # 5. 技术指标评分 (20%)
        # MACD
        recent_data['DIF'], recent_data['DEA'], recent_data['MACD'] = talib.MACD(
            recent_data['收盘'].astype(float), fastperiod=12, slowperiod=26, signalperiod=9
        )
        macd_score = 100 if this_day['DIF'] > this_day['DEA'] and this_day['MACD'] > 0 else 50

        # KDJ
        recent_data['K'], recent_data['D'] = talib.STOCH(
            recent_data['最高'].astype(float), recent_data['最低'].astype(float), recent_data['收盘'].astype(float),
            fastk_period=9, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0
        )
        recent_data['J'] = 3 * recent_data['K'] - 2 * recent_data['D']
        kdj_score = (
            100 if this_day['K'] > this_day['D'] and this_day['J'] > 80 else
            80 if this_day['K'] > this_day['D'] else
            50
        )

        # CCI
        recent_data['CCI'] = talib.CCI(
            recent_data['最高'].astype(float), recent_data['最低'].astype(float), recent_data['收盘'].astype(float),
            timeperiod=14
        )
        cci_score = 100 if this_day['CCI'] > 100 else 80 if this_day['CCI'] > 0 else 50

        # 均线角度变化
        recent_data['MA5'] = recent_data['收盘'].astype(float).rolling(window=5).mean()
        ma_slope = np.polyfit(range(3), recent_data['MA5'].tail(3), 1)[0]  # 计算斜率
        ma_score = (
            100 if ma_slope > 0 and ma_slope > np.polyfit(range(2), recent_data['MA5'].tail(2), 1)[0] else
            80 if ma_slope > 0 else
            50
        )

        # 技术指标综合评分
        tech_score = (
            macd_score * 0.4 +  # MACD 权重 40%
            kdj_score * 0.3 +   # KDJ 权重 30%
            cci_score * 0.2 +   # CCI 权重 20%
            ma_score * 0.1      # 均线角度变化权重 10%
        )

        # 6. 历史涨停概率评分 (10%)
        # 获取个股和相关股票的历史交易数据
        def get_limit_up_info(history_data):
            limit_up_count = 0
            open_limit_count = 0
            for i in range(1, 6):
                if float(history_data.iloc[-i]['涨跌幅']) >= 9.9:
                    limit_up_count += 1
                    if float(history_data.iloc[-i]['最高']) != float(history_data.iloc[-i]['收盘']):
                        open_limit_count += 1
            return limit_up_count, open_limit_count

        # 个股历史涨停评分
        stock_history = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date="20240501", end_date="20240531", adjust="")
        stock_limit_up_count, stock_open_limit_count = get_limit_up_info(stock_history)
        stock_limit_up_score = (
            100 if stock_limit_up_count > 0 and stock_open_limit_count == 0 else
            80 if stock_limit_up_count > 0 and stock_open_limit_count > 0 else
            50
        )

        # 相关股票历史涨停评分
        related_stocks = ak.stock_hot_rank_relate_em(symbol=symbol)
        related_limit_up_score = 50  # 默认值
        if not related_stocks.empty:
            related_stocks_list = related_stocks['相关股票代码'].tolist()
            related_scores = []
            for related_code in related_stocks_list:
                related_history = ak.stock_zh_a_hist(symbol=related_code, period="daily", start_date="20240501", end_date="20240531", adjust="")
                limit_up_count, open_limit_count = get_limit_up_info(related_history)
                score = (
                    100 if limit_up_count > 0 and open_limit_count == 0 else
                    80 if limit_up_count > 0 and open_limit_count > 0 else
                    50
                )
                related_scores.append(score)
            related_limit_up_score = np.mean(related_scores)

        # 历史涨停概率综合评分
        limit_up_score = (
            stock_limit_up_score * 0.6 +  # 个股历史涨停权重 60%
            related_limit_up_score * 0.4   # 相关股票历史涨停权重 40%
        )

        # 计算最终得分
        final_score = (
            price_score * 0.20 +
            turnover_score * 0.15 +
            fund_score * 0.25 +
            emotion_score * 0.2 +
            limit_up_score * 0.10 +
            tech_score * 0.20
         )

         probability = min(round(final_score, 2), 100)

         # 返回结果
         return {
             "probability": probability,
             "risk_level": ("极强" if probability >= 85 else
                           "强烈" if probability >= 70 else
                           "中等" if probability >= 50 else "较弱"),
             "indicators": {
                 "price_change": round(price_change, 2),
                 "turnover": round(turnover, 2),
                 "main_net_inflow": round(float(fund_flow['主力净流入'].iloc[-1]), 2) if not fund_flow.empty else "无数据",
                 "big_order_ratio": round(float(fund_flow['大单买入占比'].iloc[-1]), 2) if not fund_flow.empty else "无数据",
                 "fund_trend_slope": round(slope, 2) if not fund_flow.empty else "无数据",
                 "rank": round(float(emotion_data['排名'].iloc[-1]), 2) if not emotion_data.empty else "无数据",
                 "new_fans": round(float(emotion_data['新晋粉丝'].iloc[-1]), 2) if not emotion_data.empty else "无数据",
                 "loyal_fans": round(float(emotion_data['铁杆粉丝'].iloc[-1]), 2) if not emotion_data.empty else "无数据",
                 "emotion_trend_slope": round(emotion_slope, 2) if not emotion_data.empty else "无数据",
                 "stock_limit_up_count": stock_limit_up_count,
                 "stock_open_limit_count": stock_open_limit_count,
                 "related_limit_up_score": related_limit_up_score,
                 "dif": round(float(this_day['DIF']), 2),
                 "dea": round(float(this_day['DEA']), 2),
                 "macd": round(float(this_day['MACD']), 2),
                 "k": round(float(this_day['K']), 2),
                 "d": round(float(this_day['D']), 2),
                 "j": round(float(this_day['J']), 2),
                 "cci": round(float(this_day['CCI']), 2),
                 "ma_slope": round(ma_slope, 2)
             },
             "date": this_day['日期'],
             "stock_name": self.downloader.stocks[stock_code],
             "status": "success"
         }
     except Exception as e:
         return {"probability": 0, "status": f"计算失败: {str(e)}"}
            

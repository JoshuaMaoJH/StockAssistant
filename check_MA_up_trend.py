import numpy as np
import math

def calculate_ma_angles(prices):
    # 确保输入价格数据足够计算5日均线和后续分析
    if len(prices) < 7:  # 5日均线需要5天数据，加上2天计算3个角度
        return "数据不足，需要至少7天价格数据"
    
    # 计算5日移动平均线
    ma5 = []
    for i in range(len(prices) - 4):
        ma5.append(np.mean(prices[i:i+5]))
    
    # 计算连续3日的角度
    if len(ma5) < 3:
        return "均线数据不足，无法计算连续3日角度"
    
    # 取最后3天的均线数据
    last_three_ma = ma5[-3:]
    
    # 计算角度（使用arctan函数，转换为度）
    angles = []
    for i in range(len(last_three_ma)-1):
        # 假设横轴单位为1，纵轴为价格变化
        price_diff = last_three_ma[i+1] - last_three_ma[i]
        angle = math.degrees(math.atan(price_diff/1))
        angles.append(angle)
    
    # 判断角度是否逐步扩大
    is_expanding = True
    for i in range(len(angles)-1):
        if angles[i+1] <= angles[i]:
            is_expanding = False
            break
            
    return {
        "angles": angles,
        "is_expanding": is_expanding,
        "last_three_ma": last_three_ma
    }

# 示例使用
if __name__ == "__main__":
    # 模拟价格数据（7天数据）
    sample_prices = [100, 102, 105, 107, 110, 114, 119]
    
    result = calculate_ma_angles(sample_prices)
    
    print("最后三天的5日均线值:", result["last_three_ma"])
    print("连续三天的角度:", result["angles"])
    print("角度是否逐步扩大:", "是" if result["is_expanding"] else "否")

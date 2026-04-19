#!/usr/bin/env python3
"""
火柴棒等式生成器 v9（严格1根版）
关键：移动的火柴是同一个段，从A数字移到B数字
"""

DIGIT_SEGMENTS = {
    '0': {1,2,3,5,6,7},  # 6段
    '1': {3,6},           # 2段
    '2': {1,3,4,5,7},     # 5段
    '3': {1,3,4,6,7},     # 5段
    '4': {2,3,4,6},       # 4段
    '5': {1,2,4,6,7},     # 5段
    '6': {1,2,4,5,6,7},   # 6段
    '7': {1,3,6},         # 3段
    '8': {1,2,3,4,5,6,7}, # 7段
    '9': {1,2,3,4,6,7},   # 6段
}

# 预计算"移除1段"变换: 数字A移除段X变成数字B
# 例如: 8移除段4变成0, 8移除段3变成6
REMOVE_TRANSFORMS = {}
for d1 in '0123456789':
    for seg in DIGIT_SEGMENTS[d1]:
        new_segs = DIGIT_SEGMENTS[d1] - {seg}
        for d2 in '0123456789':
            if d2 == d1:
                continue
            if DIGIT_SEGMENTS[d2] == new_segs:
                REMOVE_TRANSFORMS[(d1, d2)] = seg

def apply_transform(num_str, idx, new_digit):
    return num_str[:idx] + new_digit + num_str[idx+1:]

def check_eq(num1, op, num2, result):
    if op == '+':
        return int(num1) + int(num2) == int(result)
    else:
        return int(num1) - int(num2) == int(result)

def count_matchsticks(num_str):
    total = 0
    for c in num_str:
        total += len(DIGIT_SEGMENTS.get(c, {}))
    return total

def generate_puzzles():
    """生成题目：严格从A数字取1根移到B数字（同一根火柴）"""
    puzzles = []
    
    # 正确答案等式库
    correct_eqs = [
        ('1', '+', '1', '2'),
        ('7', '+', '1', '8'),
        ('3', '+', '3', '6'),
        ('8', '-', '4', '4'),
        ('6', '+', '5', '11'),
        ('5', '+', '2', '7'),
        ('7', '-', '3', '4'),
        ('4', '+', '4', '8'),
        ('8', '-', '7', '1'),
        ('9', '-', '1', '8'),
        ('15', '+', '1', '16'),
        ('10', '+', '7', '17'),
        ('25', '+', '1', '26'),
        ('30', '+', '6', '36'),
        ('12', '+', '7', '19'),
        ('18', '+', '1', '19'),
        ('41', '+', '1', '42'),
        ('50', '+', '5', '55'),
        ('23', '+', '6', '29'),
        ('34', '+', '5', '39'),
        ('10', '-', '1', '9'),
        ('16', '-', '7', '9'),
        ('19', '-', '10', '9'),
        ('28', '-', '19', '9'),
        ('37', '-', '28', '9'),
        ('55', '-', '46', '9'),
        ('73', '-', '64', '9'),
        ('86', '-', '77', '9'),
        ('94', '-', '85', '9'),
        ('61', '-', '52', '9'),
        ('9', '+', '9', '18'),
        ('7', '+', '7', '14'),
        ('3', '+', '8', '11'),
        ('6', '+', '9', '15'),
        ('5', '+', '9', '14'),
        ('8', '+', '9', '17'),
        ('15', '-', '6', '9'),
        ('24', '+', '6', '30'),
        ('47', '-', '38', '9'),
        ('99', '-', '90', '9'),
        ('78', '+', '1', '79'),
        ('66', '+', '3', '69'),
        ('83', '+', '6', '89'),
        ('57', '-', '48', '9'),
        ('91', '+', '8', '99'),
        ('76', '-', '67', '9'),
        ('29', '+', '70', '99'),
    ]
    
    import random
    random.seed(2024)
    
    # 段编号说明：
    # 段1=上横, 段2=左上竖, 段3=右上竖, 段4=中横
    # 段5=左下竖, 段6=右下竖, 段7=下横
    SEG_NAMES = {1: '上横', 2: '左上竖', 3: '右上竖', 4: '中横',
                 5: '左下竖', 6: '右下竖', 7: '下横'}
    
    for num1, op, num2, result in correct_eqs:
        assert check_eq(num1, op, num2, result)
        original_total = count_matchsticks(num1) + count_matchsticks(num2) + count_matchsticks(result)
        
        candidates = []
        
        # 遍历所有"从A数字取1根给B数字"的方案
        # A: 数字a在位置(i, pos_type)，变成a'
        # B: 数字b在位置(j, pos_type2)，变成b'
        # 条件: a'比a少1段(被取走), b'比b多1段(被给予)
        
        all_digits = []
        for idx, d in enumerate(num1):
            all_digits.append(('num1', idx, d))
        for idx, d in enumerate(num2):
            all_digits.append(('num2', idx, d))
        for idx, d in enumerate(result):
            all_digits.append(('result', idx, d))
        
        for a_pos, a_idx, a_digit in all_digits:
            # a_digit移除1段能变成什么？
            for a_new, seg_removed in REMOVE_TRANSFORMS.items():
                if a_new[0] != a_digit:
                    continue
                a_new_digit = a_new[1]
                
                # 尝试给B数字加这1段
                for b_pos, b_idx, b_digit in all_digits:
                    if b_pos == a_pos and b_idx == a_idx:
                        continue  # 不能是同一个位置
                    
                    # b_digit添加seg_removed能变成什么？
                    for b_new, seg_added in REMOVE_TRANSFORMS.items():
                        if b_new[1] != b_digit:
                            continue
                        if seg_added != seg_removed:
                            continue  # 必须使用同一根火柴！
                        b_new_digit = b_new[0]
                        
                        # 构建错误等式
                        if a_pos == 'num1':
                            wrong_num1 = apply_transform(num1, a_idx, a_new_digit)
                        else:
                            wrong_num1 = num1
                        
                        if a_pos == 'num2':
                            wrong_num2 = apply_transform(num2, a_idx, a_new_digit)
                        else:
                            wrong_num2 = num2
                        
                        if a_pos == 'result':
                            wrong_result = apply_transform(result, a_idx, a_new_digit)
                        else:
                            wrong_result = result
                        
                        if b_pos == 'num1':
                            wrong_num1 = apply_transform(wrong_num1, b_idx, b_new_digit)
                        
                        if b_pos == 'num2':
                            wrong_num2 = apply_transform(wrong_num2, b_idx, b_new_digit)
                        
                        if b_pos == 'result':
                            wrong_result = apply_transform(wrong_result, b_idx, b_new_digit)
                        
                        # 错误等式必须不成立
                        if check_eq(wrong_num1, op, wrong_num2, wrong_result):
                            continue
                        
                        # 火柴棒总数必须不变
                        wrong_total = count_matchsticks(wrong_num1) + count_matchsticks(wrong_num2) + count_matchsticks(wrong_result)
                        if wrong_total != original_total:
                            continue
                        
                        # 构建描述
                        a_desc = f"{'第1个数' if a_pos=='num1' else '第2个数' if a_pos=='num2' else '结果'}第{a_idx+1}位"
                        b_desc = f"{'第1个数' if b_pos=='num1' else '第2个数' if b_pos=='num2' else '结果'}第{b_idx+1}位"
                        
                        candidates.append({
                            'wrong': f"{wrong_num1}{op}{wrong_num2}={wrong_result}",
                            'correct': f"{num1}{op}{num2}={result}",
                            'move': f"把{a_desc}的{a_digit}的{SEG_NAMES[seg_removed]}移到{b_desc}的{b_digit}上"
                        })
        
        if candidates:
            random.shuffle(candidates)
            puzzles.append(candidates[0])
    
    return puzzles

if __name__ == '__main__':
    puzzles = generate_puzzles()
    print(f"生成了 {len(puzzles)} 道严格1根移动的题目\n")
    
    print("=== 火柴棒思维训练10题 ===\n")
    for i, p in enumerate(puzzles[:10], 1):
        print(f"第{i}题")
        print(f"  错误等式: {p['wrong']} ❌")
        print(f"  正确答案: {p['correct']} ✅")
        print(f"  解法: {p['move']}")
        print()

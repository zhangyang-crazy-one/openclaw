#!/usr/bin/env python3
"""
火柴棒等式生成器 v7（最终版）
正确理解变换方向
"""

DIGIT_SEGMENTS = {
    '0': {1,2,3,5,6,7},
    '1': {3,6},
    '2': {1,3,4,5,7},
    '3': {1,3,4,6,7},
    '4': {2,3,4,6},
    '5': {1,2,4,6,7},
    '6': {1,2,4,5,6,7},
    '7': {1,3,6},
    '8': {1,2,3,4,5,6,7},
    '9': {1,2,3,4,6,7},
}

# 验证过的变换：错误数字 → 正确数字（移除1根）
# 例如：8→0表示"8移除中横(4)变成0"
ERROR_TO_CORRECT = {
    '8': {'0': 4, '6': 3, '9': 5},   # 8移除不同段变成不同数字
    '9': {'5': 3, '3': 2},           # 9移除右上竖→5, 移除左上竖→3
    '6': {'5': 5},                    # 6移除左下竖→5
    '7': {'1': 1},                    # 7移除上横→1
}

# 反向映射：正确数字 → 错误数字（添加1根）
# 例如：0→8表示"0添加中横(4)变成8"
CORRECT_TO_ERROR = {
    '0': {'8': 4},   # 0添加中横→8
    '1': {'7': 1},   # 1添加上横→7
    '3': {'9': 2},   # 3添加左上竖→9
    '5': {'6': 5, '9': 3},  # 5添加不同段变成不同数字
    '6': {'8': 3},   # 6添加右上竖→8
    '9': {'8': 5},   # 9添加左下竖→8
}

# 变换描述
TRANSFORM_DESC = {
    ('8', '0'): '8去中间横变0',
    ('8', '6'): '8去右上竖变6',
    ('8', '9'): '8去左下竖变9',
    ('9', '5'): '9去右上竖变5',
    ('9', '3'): '9去左上竖变3',
    ('6', '5'): '6去左下竖变5',
    ('7', '1'): '7去上横变1',
    ('0', '8'): '0加中间横变8',
    ('1', '7'): '1加上横变7',
    ('3', '9'): '3加左上竖变9',
    ('5', '6'): '5加左下竖变6',
    ('5', '9'): '5加右上竖变9',
    ('6', '8'): '6加右上竖变8',
    ('9', '8'): '9加左下竖变8',
}

def apply_transform(num_str, idx, new_digit):
    return num_str[:idx] + new_digit + num_str[idx+1:]

def check_eq(num1, op, num2, result):
    if op == '+':
        return int(num1) + int(num2) == int(result)
    else:
        return int(num1) - int(num2) == int(result)

def generate_puzzles():
    """生成题目：把正确等式中的某个数字替换成需要添加火柴的版本"""
    puzzles = []
    
    # 正确答案等式库
    correct_eqs = [
        # 简单
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
        # 两位数
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
        # 减法得9
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
        # 进阶
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
    
    for num1, op, num2, result in correct_eqs:
        # 确保原等式成立
        assert check_eq(num1, op, num2, result)
        
        # 找所有可以"添加火柴变成错误"的位
        candidates = []
        for i, d in enumerate(num1):
            if d in CORRECT_TO_ERROR:
                for error_digit, seg_id in CORRECT_TO_ERROR[d].items():
                    candidates.append(('L', i, d, error_digit, seg_id))
        for i, d in enumerate(num2):
            if d in CORRECT_TO_ERROR:
                for error_digit, seg_id in CORRECT_TO_ERROR[d].items():
                    candidates.append(('R', i, d, error_digit, seg_id))
        for i, d in enumerate(result):
            if d in CORRECT_TO_ERROR:
                for error_digit, seg_id in CORRECT_TO_ERROR[d].items():
                    candidates.append(('S', i, d, error_digit, seg_id))
        
        if not candidates:
            continue
        
        random.shuffle(candidates)
        
        for pos_type, idx, correct_digit, error_digit, seg_id in candidates:
            # 构建错误等式：把正确数字替换成错误数字
            if pos_type == 'L':
                wrong_num1 = apply_transform(num1, idx, error_digit)
                wrong_num2 = num2
                wrong_result = result
                position_desc = f"左边第{idx+1}位"
            elif pos_type == 'R':
                wrong_num1 = num1
                wrong_num2 = apply_transform(num2, idx, error_digit)
                wrong_result = result
                position_desc = f"中间第{idx+1}位"
            else:  # S
                wrong_num1 = num1
                wrong_num2 = num2
                wrong_result = apply_transform(result, idx, error_digit)
                position_desc = f"右边第{idx+1}位"
            
            # 错误等式必须不成立
            if check_eq(wrong_num1, op, wrong_num2, wrong_result):
                continue
            
            # 正确等式必须成立
            if not check_eq(num1, op, num2, result):
                continue
            
            transform_key = (error_digit, correct_digit)
            desc = TRANSFORM_DESC.get(transform_key, f'{error_digit}变{correct_digit}')
            
            puzzles.append({
                'wrong': f"{wrong_num1}{op}{wrong_num2}={wrong_result}",
                'correct': f"{num1}{op}{num2}={result}",
                'transform': f"把{position_desc}的{correct_digit}变成{error_digit}（{desc}）",
            })
            break  # 每题只取第一个有效变换
    
    return puzzles

if __name__ == '__main__':
    puzzles = generate_puzzles()
    print(f"生成了 {len(puzzles)} 道题\n")
    
    # 选10题（3简单+4中等+3困难）
    simple = [p for p in puzzles if '1' in p['correct'] or '2' in p['correct'] or '3' in p['correct']][:3]
    medium = puzzles[10:20]
    hard = puzzles[25:28]
    
    selected = simple + medium + hard
    if len(selected) < 10:
        selected = puzzles[:10]
    
    print("=== 火柴棒思维训练10题 ===\n")
    for i, p in enumerate(selected[:10], 1):
        print(f"第{i}题")
        print(f"  错误等式: {p['wrong']} ❌")
        print(f"  正确答案: {p['correct']} ✅")
        print(f"  解法: {p['transform']}")
        print()

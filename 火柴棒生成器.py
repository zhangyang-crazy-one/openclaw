#!/usr/bin/env python3
"""
火柴棒等式生成器 v4（最终版）
只生成真正能"移动一根"修正的题
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

# 预计算：哪些数字对之间只差1根火柴
# 格式：{(数字A, 数字B): (从A到B需要的操作, 段ID)}
# 操作: 'remove' 表示从A移除该段得到B
ONE_STICK_TRANSFORMS = {}

for d1 in '0123456789':
    for d2 in '0123456789':
        if d1 == d2:
            continue
        segs1 = DIGIT_SEGMENTS[d1]
        segs2 = DIGIT_SEGMENTS[d2]
        
        # 差1段的情况
        if len(segs1) - len(segs2) == 1:
            diff = segs1 - segs2
            if len(diff) == 1:
                ONE_STICK_TRANSFORMS[(d1, d2)] = ('remove', diff.pop())
        elif len(segs2) - len(segs1) == 1:
            diff = segs2 - segs1
            if len(diff) == 1:
                ONE_STICK_TRANSFORMS[(d1, d2)] = ('add', diff.pop())

# 对称化：只要知道A能变成B，就记录B也能变成A
ALL_TRANSFORMS = {}
for (a, b), (op, seg) in ONE_STICK_TRANSFORMS.items():
    ALL_TRANSFORMS[(a, b)] = (op, seg)
    ALL_TRANSFORMS[(b, a)] = ('add' if op == 'remove' else 'remove', seg)

def can_transform(d1, d2):
    """检查d1是否能通过移动一根火柴变成d2"""
    if d1 == d2:
        return False
    return (d1, d2) in ALL_TRANSFORMS

def get_transform(d1, d2):
    """获取变换信息"""
    return ALL_TRANSFORMS.get((d1, d2), None)

def apply_transform(num_str, idx, new_digit):
    return num_str[:idx] + new_digit + num_str[idx+1:]

def check_eq(num1, op, num2, result):
    if op == '+':
        return int(num1) + int(num2) == int(result)
    else:
        return int(num1) - int(num2) == int(result)

def generate_valid_puzzles():
    """只生成真正有解的题"""
    puzzles = []
    
    # 正确等式库
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
        ('9', '-', '1', '8'),
        ('5', '+', '9', '14'),
        ('8', '+', '9', '17'),
        ('15', '-', '6', '9'),
        ('24', '+', '6', '30'),
        ('47', '-', '38', '9'),
        ('99', '-', '90', '9'),
        ('69', '-', '60', '9'),
        ('78', '+', '1', '79'),
        ('66', '+', '3', '69'),
        ('100', '-', '1', '99'),
        ('83', '+', '6', '89'),
        ('57', '-', '48', '9'),
        ('91', '+', '8', '99'),
        ('76', '-', '67', '9'),
        ('29', '+', '70', '99'),
    ]
    
    import random
    random.seed(42)
    
    for num1, op, num2, result in correct_eqs:
        # 确保原等式成立
        assert check_eq(num1, op, num2, result), f"原等式不成立: {num1}{op}{num2}={result}"
        
        # 遍历每个数字的每一位，尝试变成另一个数字
        all_positions = []
        for i, d in enumerate(num1):
            all_positions.append((num1, 'L', i, d, result, num2))
        for i, d in enumerate(num2):
            all_positions.append((num2, 'R', i, d, result, num1))
        for i, d in enumerate(result):
            all_positions.append((result, 'S', i, d, None, None))
        
        random.shuffle(all_positions)
        
        for base_num, pos_type, idx, correct_digit, other_num, other_name in all_positions:
            if correct_digit not in '0123456789':
                continue
            
            # 找所有可以通过移动一根火柴变成的正确数字
            for error_digit in '0123456789':
                if error_digit == correct_digit:
                    continue
                
                # 检查是否能从错误数字变换到正确数字
                transform = get_transform(error_digit, correct_digit)
                if transform is None:
                    continue
                
                op_type, seg_id = transform
                
                # 构建错误等式
                if pos_type == 'L':
                    wrong_num1 = apply_transform(num1, idx, error_digit)
                    wrong_num2 = num2
                    wrong_result = result
                elif pos_type == 'R':
                    wrong_num1 = num1
                    wrong_num2 = apply_transform(num2, idx, error_digit)
                    wrong_result = result
                else:  # S - result
                    wrong_num1 = num1
                    wrong_num2 = num2
                    wrong_result = apply_transform(result, idx, error_digit)
                
                # 错误等式必须不成立
                if check_eq(wrong_num1, op, wrong_num2, wrong_result):
                    continue
                
                # 验证新数字是否有效
                test_digit = wrong_result[idx] if pos_type == 'S' else (wrong_num1[idx] if pos_type == 'L' else wrong_num2[idx])
                if test_digit not in DIGIT_SEGMENTS:
                    continue
                
                puzzles.append({
                    'wrong': f"{wrong_num1}{op}{wrong_num2}={wrong_result}",
                    'correct': f"{num1}{op}{num2}={result}",
                })
                break  # 只取每题第一个有效变换
    
    return puzzles

if __name__ == '__main__':
    puzzles = generate_valid_puzzles()
    print(f"生成了 {len(puzzles)} 道经验证的题目\n")
    
    for i, p in enumerate(puzzles[:50], 1):
        print(f"第{i}题  {p['wrong']}❌  →  {p['correct']}✅")
    
    if len(puzzles) > 50:
        print(f"\n... 还有 {len(puzzles) - 50} 道题")

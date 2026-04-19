#!/usr/bin/env python3
"""
火柴棒等式生成器 v8（移动版）
关键：从正确等式出发，移动一根火柴到另一个数字，总数不变
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

# 预计算所有"差1段"的变换对
ONE_STICK_TRANSFORMS = {}
for d1 in '0123456789':
    for d2 in '0123456789':
        if d1 == d2:
            continue
        segs1 = DIGIT_SEGMENTS[d1]
        segs2 = DIGIT_SEGMENTS[d2]
        # 差1段
        if len(segs1) - len(segs2) == 1:
            diff = segs1 - segs2
            if len(diff) == 1:
                ONE_STICK_TRANSFORMS[(d1, d2)] = diff.pop()
        elif len(segs2) - len(segs1) == 1:
            diff = segs2 - segs1
            if len(diff) == 1:
                ONE_STICK_TRANSFORMS[(d1, d2)] = diff.pop()

def get_lose_gain_digit(d):
    """数字d移除1根后能变成什么？"""
    results = []
    for target, seg in ONE_STICK_TRANSFORMS.items():
        if target[0] == d:
            results.append((target[1], seg))
    return results  # [(目标数字, 移除的段), ...]

def get_gain_digit(d):
    """数字d添加1根后能变成什么？"""
    results = []
    for target, seg in ONE_STICK_TRANSFORMS.items():
        if target[1] == d:
            results.append((target[0], seg))
    return results  # [(源数字, 添加的段), ...]

def apply_transform(num_str, idx, new_digit):
    return num_str[:idx] + new_digit + num_str[idx+1:]

def check_eq(num1, op, num2, result):
    if op == '+':
        return int(num1) + int(num2) == int(result)
    else:
        return int(num1) - int(num2) == int(result)

def count_matchsticks(num_str):
    """计算数字串的火柴棒总数"""
    total = 0
    for c in num_str:
        total += len(DIGIT_SEGMENTS.get(c, {}))
    return total

def generate_puzzles():
    """生成题目：从正确等式出发，移动一根火柴到另一个数字"""
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
    random.seed(42)
    
    for num1, op, num2, result in correct_eqs:
        # 确保原等式成立
        assert check_eq(num1, op, num2, result)
        
        # 原始火柴棒总数
        original_total = count_matchsticks(num1) + count_matchsticks(num2) + count_matchsticks(result)
        
        # 找所有"从A移动一根到B"的方案
        candidates = []
        
        # A在num1位置
        for i, a_digit in enumerate(num1):
            loses = get_lose_gain_digit(a_digit)  # a_digit移除1根变成什么
            for a_new, seg_removed in loses:
                # B在num2位置
                for j, b_digit in enumerate(num2):
                    gains = get_gain_digit(b_digit)  # b_digit添加1根变成什么
                    for b_new, seg_added in gains:
                        # 构建错误等式
                        wrong_num1 = apply_transform(num1, i, a_new)
                        wrong_num2 = apply_transform(num2, j, b_new)
                        wrong_result = result
                        
                        # 错误等式必须不成立
                        if check_eq(wrong_num1, op, wrong_num2, wrong_result):
                            continue
                        
                        # 火柴棒总数必须不变
                        wrong_total = count_matchsticks(wrong_num1) + count_matchsticks(wrong_num2) + count_matchsticks(wrong_result)
                        if wrong_total != original_total:
                            continue
                        
                        candidates.append({
                            'wrong': f"{wrong_num1}{op}{wrong_num2}={wrong_result}",
                            'correct': f"{num1}{op}{num2}={result}",
                            'move': f"从第1个数的第{i+1}位({a_digit}→{a_new})移动到第2个数的第{j+1}位({b_digit}→{b_new})"
                        })
                
                # B在result位置
                for j, b_digit in enumerate(result):
                    gains = get_gain_digit(b_digit)
                    for b_new, seg_added in gains:
                        wrong_num1 = apply_transform(num1, i, a_new)
                        wrong_num2 = num2
                        wrong_result = apply_transform(result, j, b_new)
                        
                        if check_eq(wrong_num1, op, wrong_num2, wrong_result):
                            continue
                        
                        wrong_total = count_matchsticks(wrong_num1) + count_matchsticks(wrong_num2) + count_matchsticks(wrong_result)
                        if wrong_total != original_total:
                            continue
                        
                        candidates.append({
                            'wrong': f"{wrong_num1}{op}{wrong_num2}={wrong_result}",
                            'correct': f"{num1}{op}{num2}={result}",
                            'move': f"从第1个数的第{i+1}位({a_digit}→{a_new})移动到结果第{j+1}位({b_digit}→{b_new})"
                        })
        
        # A在num2位置
        for i, a_digit in enumerate(num2):
            loses = get_lose_gain_digit(a_digit)
            for a_new, seg_removed in loses:
                # B在num1位置
                for j, b_digit in enumerate(num1):
                    gains = get_gain_digit(b_digit)
                    for b_new, seg_added in gains:
                        wrong_num1 = apply_transform(num1, j, b_new)
                        wrong_num2 = apply_transform(num2, i, a_new)
                        wrong_result = result
                        
                        if check_eq(wrong_num1, op, wrong_num2, wrong_result):
                            continue
                        
                        wrong_total = count_matchsticks(wrong_num1) + count_matchsticks(wrong_num2) + count_matchsticks(wrong_result)
                        if wrong_total != original_total:
                            continue
                        
                        candidates.append({
                            'wrong': f"{wrong_num1}{op}{wrong_num2}={wrong_result}",
                            'correct': f"{num1}{op}{num2}={result}",
                            'move': f"从第2个数的第{i+1}位({a_digit}→{a_new})移动到第1个数的第{j+1}位({b_digit}→{b_new})"
                        })
                
                # B在result位置
                for j, b_digit in enumerate(result):
                    gains = get_gain_digit(b_digit)
                    for b_new, seg_added in gains:
                        wrong_num1 = num1
                        wrong_num2 = apply_transform(num2, i, a_new)
                        wrong_result = apply_transform(result, j, b_new)
                        
                        if check_eq(wrong_num1, op, wrong_num2, wrong_result):
                            continue
                        
                        wrong_total = count_matchsticks(wrong_num1) + count_matchsticks(wrong_num2) + count_matchsticks(wrong_result)
                        if wrong_total != original_total:
                            continue
                        
                        candidates.append({
                            'wrong': f"{wrong_num1}{op}{wrong_num2}={wrong_result}",
                            'correct': f"{num1}{op}{num2}={result}",
                            'move': f"从第2个数的第{i+1}位({a_digit}→{a_new})移动到结果第{j+1}位({b_digit}→{b_new})"
                        })
        
        # A在result位置
        for i, a_digit in enumerate(result):
            loses = get_lose_gain_digit(a_digit)
            for a_new, seg_removed in loses:
                # B在num1位置
                for j, b_digit in enumerate(num1):
                    gains = get_gain_digit(b_digit)
                    for b_new, seg_added in gains:
                        wrong_num1 = apply_transform(num1, j, b_new)
                        wrong_num2 = num2
                        wrong_result = apply_transform(result, i, a_new)
                        
                        if check_eq(wrong_num1, op, wrong_num2, wrong_result):
                            continue
                        
                        wrong_total = count_matchsticks(wrong_num1) + count_matchsticks(wrong_num2) + count_matchsticks(wrong_result)
                        if wrong_total != original_total:
                            continue
                        
                        candidates.append({
                            'wrong': f"{wrong_num1}{op}{wrong_num2}={wrong_result}",
                            'correct': f"{num1}{op}{num2}={result}",
                            'move': f"从结果第{i+1}位({a_digit}→{a_new})移动到第1个数第{j+1}位({b_digit}→{b_new})"
                        })
                
                # B在num2位置
                for j, b_digit in enumerate(num2):
                    gains = get_gain_digit(b_digit)
                    for b_new, seg_added in gains:
                        wrong_num1 = num1
                        wrong_num2 = apply_transform(num2, j, b_new)
                        wrong_result = apply_transform(result, i, a_new)
                        
                        if check_eq(wrong_num1, op, wrong_num2, wrong_result):
                            continue
                        
                        wrong_total = count_matchsticks(wrong_num1) + count_matchsticks(wrong_num2) + count_matchsticks(wrong_result)
                        if wrong_total != original_total:
                            continue
                        
                        candidates.append({
                            'wrong': f"{wrong_num1}{op}{wrong_num2}={wrong_result}",
                            'correct': f"{num1}{op}{num2}={result}",
                            'move': f"从结果第{i+1}位({a_digit}→{a_new})移动到第2个数第{j+1}位({b_digit}→{b_new})"
                        })
        
        if candidates:
            random.shuffle(candidates)
            puzzles.append(candidates[0])
    
    return puzzles

if __name__ == '__main__':
    puzzles = generate_puzzles()
    print(f"生成了 {len(puzzles)} 道火柴棒总数不变的题目\n")
    
    # 输出前10题
    print("=== 火柴棒思维训练10题（总数不变版）===\n")
    for i, p in enumerate(puzzles[:10], 1):
        print(f"第{i}题")
        print(f"  错误等式: {p['wrong']} ❌")
        print(f"  正确答案: {p['correct']} ✅")
        print(f"  解法: 移动火柴: {p['move']}")
        print()

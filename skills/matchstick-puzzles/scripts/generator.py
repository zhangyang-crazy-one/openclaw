#!/usr/bin/env python3
"""
火柴棒等式生成器（严格版）
规则：从正确等式出发，移动一根火柴到另一个数字，火柴棒总数不变

七段数码管段编号：
  段1=上横  段2=左上竖  段3=右上竖
  段4=中横  段5=左下竖  段6=右下竖  段7=下横

数字0-9的火柴棒数：
  0(6段), 1(2段), 2(5段), 3(5段), 4(4段)
  5(5段), 6(6段), 7(3段), 8(7段), 9(6段)
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

# 预计算"移除1段"变换：(新数字, 原数字) = 移除的段
REMOVE_TRANSFORMS = {}
for d1 in '0123456789':
    for seg in DIGIT_SEGMENTS[d1]:
        new_segs = DIGIT_SEGMENTS[d1] - {seg}
        for d2 in '0123456789':
            if d2 == d1:
                continue
            if DIGIT_SEGMENTS[d2] == new_segs:
                REMOVE_TRANSFORMS[(d2, d1)] = seg

SEG_NAMES = {
    1: '上横', 2: '左上竖', 3: '右上竖', 4: '中横',
    5: '左下竖', 6: '右下竖', 7: '下横'
}

def apply_transform(num_str, idx, new_digit):
    return num_str[:idx] + new_digit + num_str[idx+1:]

def check_eq(num1, op, num2, result):
    return int(num1) + int(num2) == int(result) if op == '+' else int(num1) - int(num2) == int(result)

def count_matchsticks(num_str):
    return sum(len(DIGIT_SEGMENTS.get(c, {})) for c in num_str)

def generate_puzzles(n=10, seed=2024):
    """生成n道火柴棒题目
    
    Args:
        n: 生成题目数量
        seed: 随机种子
    
    Returns:
        list of dict: {'wrong': str, 'correct': str, 'move': str}
    """
    correct_eqs = [
        ('1', '+', '1', '2'), ('7', '+', '1', '8'), ('3', '+', '3', '6'),
        ('8', '-', '4', '4'), ('6', '+', '5', '11'), ('5', '+', '2', '7'),
        ('7', '-', '3', '4'), ('4', '+', '4', '8'), ('8', '-', '7', '1'),
        ('9', '-', '1', '8'), ('15', '+', '1', '16'), ('10', '+', '7', '17'),
        ('25', '+', '1', '26'), ('30', '+', '6', '36'), ('12', '+', '7', '19'),
        ('18', '+', '1', '19'), ('41', '+', '1', '42'), ('50', '+', '5', '55'),
        ('23', '+', '6', '29'), ('34', '+', '5', '39'), ('10', '-', '1', '9'),
        ('16', '-', '7', '9'), ('19', '-', '10', '9'), ('28', '-', '19', '9'),
        ('37', '-', '28', '9'), ('55', '-', '46', '9'), ('73', '-', '64', '9'),
        ('86', '-', '77', '9'), ('94', '-', '85', '9'), ('61', '-', '52', '9'),
        ('9', '+', '9', '18'), ('7', '+', '7', '14'), ('3', '+', '8', '11'),
        ('6', '+', '9', '15'), ('5', '+', '9', '14'), ('8', '+', '9', '17'),
        ('15', '-', '6', '9'), ('24', '+', '6', '30'), ('47', '-', '38', '9'),
        ('99', '-', '90', '9'), ('78', '+', '1', '79'), ('66', '+', '3', '69'),
        ('83', '+', '6', '89'), ('57', '-', '48', '9'), ('91', '+', '8', '99'),
        ('76', '-', '67', '9'), ('29', '+', '70', '99'),
    ]
    
    import random
    random.seed(seed)
    
    puzzles = []
    
    for num1, op, num2, result in correct_eqs:
        assert check_eq(num1, op, num2, result)
        original_total = count_matchsticks(num1) + count_matchsticks(num2) + count_matchsticks(result)
        
        all_digits = []
        for idx, d in enumerate(num1):
            all_digits.append(('num1', idx, d))
        for idx, d in enumerate(num2):
            all_digits.append(('num2', idx, d))
        for idx, d in enumerate(result):
            all_digits.append(('result', idx, d))
        
        candidates = []
        
        for a_pos, a_idx, a_digit in all_digits:
            for (a_new_digit, a_digit_check), seg_removed in REMOVE_TRANSFORMS.items():
                if a_digit_check != a_digit:
                    continue
                for b_pos, b_idx, b_digit in all_digits:
                    if b_pos == a_pos and b_idx == a_idx:
                        continue
                    for (b_digit_check, b_new_digit), seg_added in REMOVE_TRANSFORMS.items():
                        if b_digit_check != b_digit:
                            continue
                        if seg_added != seg_removed:
                            continue
                        
                        # 构建错误等式
                        wrong_num1 = num1
                        wrong_num2 = num2
                        wrong_result = result
                        
                        if a_pos == 'num1':
                            wrong_num1 = apply_transform(num1, a_idx, a_new_digit)
                        elif a_pos == 'num2':
                            wrong_num2 = apply_transform(num2, a_idx, a_new_digit)
                        elif a_pos == 'result':
                            wrong_result = apply_transform(result, a_idx, a_new_digit)
                        
                        if b_pos == 'num1':
                            wrong_num1 = apply_transform(wrong_num1, b_idx, b_new_digit)
                        elif b_pos == 'num2':
                            wrong_num2 = apply_transform(wrong_num2, b_idx, b_new_digit)
                        elif b_pos == 'result':
                            wrong_result = apply_transform(wrong_result, b_idx, b_new_digit)
                        
                        if check_eq(wrong_num1, op, wrong_num2, wrong_result):
                            continue
                        
                        wrong_total = count_matchsticks(wrong_num1) + count_matchsticks(wrong_num2) + count_matchsticks(wrong_result)
                        if wrong_total != original_total:
                            continue
                        
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
    
    return puzzles[:n]

def verify_puzzle(wrong_eq, correct_eq):
    """验证火柴棒谜题的正确性
    
    检查：
    1. 正确答案等式数学上成立
    2. 错误等式数学上不成立
    3. 错误等式通过移动一根火柴可以变成正确等式
    4. 移动前后火柴棒总数不变
    """
    import re
    
    def parse_eq(eq):
        m = re.match(r'(\d+)([+-])(\d+)=(\d+)', eq)
        if not m:
            return None
        return m.group(1), m.group(2), m.group(3), m.group(4)
    
    correct_parsed = parse_eq(correct_eq)
    wrong_parsed = parse_eq(wrong_eq)
    
    if not correct_parsed or not wrong_parsed:
        return False, "等式格式错误"
    
    num1, op, num2, result = correct_parsed
    if not check_eq(num1, op, num2, result):
        return False, "正确答案等式不成立"
    
    wnum1, wop, wnum2, wresult = wrong_parsed
    if check_eq(wnum1, wop, wnum2, wresult):
        return False, "错误等式实际成立"
    
    original_total = count_matchsticks(num1) + count_matchsticks(num2) + count_matchsticks(result)
    wrong_total = count_matchsticks(wnum1) + count_matchsticks(wnum2) + count_matchsticks(wresult)
    
    if original_total != wrong_total:
        return False, f"火柴棒总数改变: {original_total} vs {wrong_total}"
    
    return True, "验证通过"

if __name__ == '__main__':
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    puzzles = generate_puzzles(n)
    
    print(f"=== 火柴棒思维训练{n}题 ===\n")
    for i, p in enumerate(puzzles, 1):
        print(f"第{i}题")
        print(f"  错误等式: {p['wrong']} ❌")
        print(f"  正确答案: {p['correct']} ✅")
        print(f"  解法: {p['move']}")
        print()
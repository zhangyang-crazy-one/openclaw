#!/usr/bin/env python3
"""
火柴棒等式生成器 v5（增强版）
基于答案图规律，加入更多有效变换
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

# 验证哪些变换对是差1段的
def find_one_stick_transforms():
    """找出所有差1段的数字对"""
    transforms = []
    for d1 in '0123456789':
        for d2 in '0123456789':
            if d1 == d2:
                continue
            segs1 = DIGIT_SEGMENTS[d1]
            segs2 = DIGIT_SEGMENTS[d2]
            diff = abs(len(segs1) - len(segs2))
            if diff == 1:
                # 检查是否刚好差一个段
                if len(segs1) > len(segs2):
                    removed = segs1 - segs2
                    added = segs2 - segs1
                    if len(removed) == 1 and len(added) == 1:
                        transforms.append((d1, d2, 'remove', list(removed)[0]))
                    else:
                        transforms.append((d1, d2, 'move', None))
                else:
                    removed = segs2 - segs1
                    added = segs1 - segs2
                    if len(removed) == 1 and len(added) == 1:
                        transforms.append((d1, d2, 'add', list(added)[0]))
                    else:
                        transforms.append((d1, d2, 'move', None))
    return transforms

print("=== 差1段的变换对 ===")
transforms = find_one_stick_transforms()
for t in transforms:
    print(f"{t[0]} → {t[1]}: {t[2]} segment {t[3]}")

print(f"\n共 {len(transforms)} 种变换")

# 常见的简单变换（只差1段且直观）
SIMPLE_TRANSFORMS = {
    # 错误数字: 正确数字 - 符合"移动一根"规则
    '8': '0',   # 8去掉中间横变0
    '9': '5',   # 9去掉左上竖变5  
    '7': '1',   # 7去掉上横变1
    '6': '8',   # 6去掉左下竖变8? 不对，6比8少一段
    '5': '9',   # 5加上左上竖变9
    '0': '8',   # 0加上中间横变8
    '1': '7',   # 1加上上横变7
}

# 完整映射：从错误数字→正确数字（移除1根）
ERROR_TO_CORRECT = {
    '8': '0',   # 8→0: 移除中横(4)
    '9': '5',   # 9→5: 移除左上竖(2)
    '9': '3',   # 9→3: 移除左上竖(2)  
    '7': '1',   # 7→1: 移除上横(1)
    '3': '2',   # 3→2: 移除右下竖(6)? 不对差2个
    '6': '8',   # 6→8: 需要添加，不是移除
}

# 重新分析：题目是"移动一根" = 从A数字移除一根变成B数字
# 所以错误数字(A)比正确数字(B)多1根
# A的段数 = B的段数 + 1

# 7段数字的段数：
# 7段: 8 (最多)
# 6段: 0, 6, 9
# 5段: 2, 3, 5
# 4段: 4
# 3段: 7
# 2段: 1

# 差1段的变换对（可移除1段得到对方）：
# 8(7)→0(6): 移除任意一段
# 8(7)→6(6): 移除左下竖
# 8(7)→9(6): 移除左上竖
# 6(6)→5(5): 移除左下竖
# 9(6)→5(5): 移除左上竖
# 9(6)→3(5): 移除左上竖
# 7(3)→1(2): 移除上横

# 等等，让我精确计算：
print("\n=== 精确计算 ===")
for d1 in '0123456789':
    for d2 in '0123456789':
        if d1 == d2:
            continue
        s1 = DIGIT_SEGMENTS[d1]
        s2 = DIGIT_SEGMENTS[d2]
        if len(s1) - len(s2) == 1:
            diff = s1 - s2
            if len(diff) == 1:
                print(f"{d1}({len(s1)}) → {d2}({len(s2)}): 移除段{diff.pop()}")

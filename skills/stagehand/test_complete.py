#!/usr/bin/env python3
"""
Stagehand V3 Complete Feature Test

对比原版 Stagehand 的所有核心功能
"""

import asyncio
import json
from scripts.minimax_browser_v3 import MiniMaxBrowserV3


async def test_stagehand_features():
    """全面测试 Stagehand V3 功能"""
    
    print("=" * 80)
    print("🎯 Stagehand V3 Complete Feature Test")
    print("=" * 80)
    
    results = {
        "passed": 0,
        "failed": 0,
        "features": {}
    }
    
    b = MiniMaxBrowserV3()
    
    # ========== 1. 初始化 ==========
    print("\n" + "=" * 80)
    print("1️⃣  INITIALIZATION")
    print("=" * 80)
    
    r = await b.initialize()
    print(f"   Status: {r.get('message')}")
    print(f"   Supported Actions: {len(r.get('supported_actions', []))} types")
    print(f"   Architecture: {r.get('architecture')}")
    
    if r.get('success'):
        results["passed"] += 1
        results["features"]["initialization"] = "✅ PASS"
    else:
        results["failed"] += 1
        results["features"]["initialization"] = f"❌ FAIL: {r.get('error')}"
    
    # ========== 2. Hybrid Accessibility Tree ==========
    print("\n" + "=" * 80)
    print("2️⃣  HYBRID ACCESSIBILITY TREE")
    print("=" * 80)
    
    await b.navigate("https://github.com")
    
    tree = await b._get_accessibility_tree()
    tree_lines = tree.split("\n")
    
    print(f"   Tree Elements: {len(tree_lines)}")
    print(f"   Tree Version: {b._tree_version}")
    print(f"   Cached: {'Yes' if b._cached_tree else 'No'}")
    
    # 显示前几个元素
    print("\n   Sample Elements:")
    for i, line in enumerate(tree_lines[:5]):
        print(f"      [{i}]: {line[:60]}")
    
    if len(tree_lines) > 0:
        results["passed"] += 1
        results["features"]["accessibility_tree"] = "✅ PASS"
    else:
        results["failed"] += 1
        results["features"]["accessibility_tree"] = "❌ FAIL: Empty tree"
    
    # ========== 3. Page Navigation ==========
    print("\n" + "=" * 80)
    print("3️⃣  PAGE NAVIGATION")
    print("=" * 80)
    
    r = await b.navigate("https://example.com")
    print(f"   URL: {r.get('url')}")
    print(f"   Title: {r.get('title')}")
    print(f"   Tree Refreshed: {r.get('tree_version', 0) > 1}")
    
    if r.get('success') and r.get('title'):
        results["passed"] += 1
        results["features"]["navigation"] = "✅ PASS"
    else:
        results["failed"] += 1
        results["features"]["navigation"] = "❌ FAIL"
    
    # ========== 4. Two-Phase Inference ==========
    print("\n" + "=" * 80)
    print("4️⃣  TWO-PHASE INFERENCE")
    print("=" * 80)
    
    # Phase 1: 找到元素
    await b.navigate("https://github.com")
    
    # Phase 2: 确定动作
    r = await b.act("点击页面上的链接")
    print(f"   Instruction: 点击页面上的链接")
    print(f"   Element ID: {r.get('action_plan', {}).get('element_id', 'N/A')}")
    print(f"   Method: {r.get('action_plan', {}).get('method', 'N/A')}")
    print(f"   Reasoning: {r.get('reasoning', 'N/A')[:80]}")
    
    if r.get('action_plan', {}).get('element_id') >= 0:
        results["passed"] += 1
        results["features"]["two_phase_inference"] = "✅ PASS"
    else:
        results["failed"] += 1
        results["features"]["two_phase_inference"] = "❌ FAIL: No element found"
    
    # ========== 5. All Actions ==========
    print("\n" + "=" * 80)
    print("5️⃣  ALL SUPPORTED ACTIONS")
    print("=" * 80)
    
    await b.navigate("https://github.com")
    
    actions = [
        ("scroll", "向下滚动"),
        ("press_key", "按回车键"),
        ("wait", "等待 1 秒"),
        ("scroll_to", "滚动到 50%"),
    ]
    
    print(f"   Testing {len(actions)} actions:")
    action_results = []
    
    for method, instruction in actions:
        r = await b.act(instruction)
        actual_method = r.get('action_plan', {}).get('method', 'N/A')
        status = "✅" if actual_method == method else "⚠️"
        print(f"      {status} {method}: {actual_method}")
        action_results.append((method, actual_method == method))
    
    if all(success for _, success in action_results):
        results["passed"] += 1
        results["features"]["all_actions"] = "✅ PASS"
    else:
        results["failed"] += 1
        results["features"]["all_actions"] = "❌ FAIL: Some actions failed"
    
    # ========== 6. Data Extraction ==========
    print("\n" + "=" * 80)
    print("6️⃣  DATA EXTRACTION")
    print("=" * 80)
    
    r = await b.extract("提取页面标题和主要描述")
    print(f"   Instruction: 提取页面标题和主要描述")
    
    data = r.get('data', {})
    print(f"   Extracted Keys: {list(data.keys())}")
    
    # 打印提取的数据
    if isinstance(data, dict) and data:
        for key, value in list(data.items())[:3]:
            if isinstance(value, str):
                print(f"      {key}: {value[:50]}...")
            else:
                print(f"      {key}: {str(value)[:50]}...")
    
    if isinstance(data, dict) and len(data) > 0:
        results["passed"] += 1
        results["features"]["data_extraction"] = "✅ PASS"
    else:
        results["failed"] += 1
        results["features"]["data_extraction"] = "❌ FAIL: No data extracted"
    
    # ========== 7. Element Observation ==========
    print("\n" + "=" * 80)
    print("7️⃣  ELEMENT OBSERVATION")
    print("=" * 80)
    
    r = await b.observe("找到登录按钮和导航链接")
    print(f"   Instruction: 找到登录按钮和导航链接")
    print(f"   Elements Found: {r.get('element_count', 0)}")
    
    analysis = r.get('analysis', {})
    if isinstance(analysis, dict):
        print(f"   Description: {str(analysis.get('description', 'N/A'))[:80]}")
    
    if r.get('element_count', 0) > 0:
        results["passed"] += 1
        results["features"]["element_observation"] = "✅ PASS"
    else:
        results["failed"] += 1
        results["features"]["element_observation"] = "❌ FAIL: No elements found"
    
    # ========== 8. Self-Healing ==========
    print("\n" + "=" * 80)
    print("8️⃣  SELF-HEALING CAPABILITY")
    print("=" * 80)
    
    initial_version = b._tree_version
    
    # 执行动作
    await b.act("向下滚动")
    
    # 检查树是否自动刷新
    after_version = b._tree_version
    
    print(f"   Initial Tree Version: {initial_version}")
    print(f"   After Scroll Version: {after_version}")
    print(f"   Auto-Refresh: {'✅ Yes' if after_version > initial_version else '⚠️ No'}")
    
    if after_version > initial_version:
        results["passed"] += 1
        results["features"]["self_healing"] = "✅ PASS"
    else:
        results["failed"] += 1
        results["features"]["self_healing"] = "❌ FAIL: Tree not refreshed"
    
    # ========== 9. DOM Caching ==========
    print("\n" + "=" * 80)
    print("9️⃣  DOM CACHING")
    print("=" * 80)
    
    # 获取树
    tree1 = await b._get_accessibility_tree()
    
    # 再次获取 (应该使用缓存)
    tree2 = await b._get_accessibility_tree()
    
    print(f"   Cache Enabled: {'✅ Yes' if b._cached_tree else '❌ No'}")
    print(f"   Same Tree: {'✅ Yes' if tree1 == tree2 else '❌ No'}")
    print(f"   Tree Length: {len(tree1)} chars")
    
    if b._cached_tree and tree1 == tree2:
        results["passed"] += 1
        results["features"]["dom_caching"] = "✅ PASS"
    else:
        results["failed"] += 1
        results["features"]["dom_caching"] = "❌ FAIL: Cache not working"
    
    # ========== 10. Complex Workflow (Agent) ==========
    print("\n" + "=" * 80)
    print("🔟  COMPLEX WORKFLOW (AGENT)")
    print("=" * 80)
    
    r = await b.agent("查看 GitHub 页面")
    print(f"   Task: 查看 GitHub 页面")
    
    plan = r.get('plan', [])
    results_ = r.get('results', [])
    
    print(f"   Plan Steps: {len(plan)}")
    print(f"   Executed Steps: {len(results_)}")
    print(f"   Self-Healing Refreshes: {r.get('self_healing', {}).get('tree_refreshes', 0)}")
    
    if len(results_) > 0:
        results["passed"] += 1
        results["features"]["agent_workflow"] = "✅ PASS"
    else:
        results["failed"] += 1
        results["features"]["agent_workflow"] = "❌ FAIL: No steps executed"
    
    # ========== Summary ==========
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n   Passed: {results['passed']}/10")
    print(f"   Failed: {results['failed']}/10")
    print(f"   Success Rate: {results['passed']*10}%")
    
    print("\n   Feature Results:")
    for feature, status in results['features'].items():
        print(f"      {status} {feature.replace('_', ' ').title()}")
    
    await b.close()
    
    print("\n" + "=" * 80)
    if results['failed'] == 0:
        print("🎉 ALL TESTS PASSED! Stagehand V3 is fully functional!")
    elif results['passed'] >= 8:
        print("✅ MOST TESTS PASSED! Stagehand V3 is working well!")
    else:
        print("⚠️  SOME TESTS FAILED. Please review the results.")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    asyncio.run(test_stagehand_features())

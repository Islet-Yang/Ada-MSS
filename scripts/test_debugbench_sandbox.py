#!/usr/bin/env python3
"""
DebugBench 测试脚本示例
使用 multiprocessing 沙箱安全执行 LLM 生成的候选补丁。
"""

import json
from ada_mss.sandbox_evaluator import parse_inputs, run_multiple_tests

def main():
    # 示例：链表反转题目
    # 假设从JSON加载测试用例
    test_cases_raw = [
        {
            "inputs": ["[1,2,3,4,5]"],  # 字符串形式
            "expected": "[5,4,3,2,1]"  # 期望输出为数组
        },
        {
            "inputs": ["[]"],
            "expected": "[]"
        }
    ]

    # 解析输入和期望输出
    patches_and_tests = []
    for case in test_cases_raw:
        # 解析输入字符串
        parsed_inputs = parse_inputs(case["inputs"])  # [[1,2,3,4,5]]

        # patched_code使用build_list构建链表，返回serialize_list
        patched_code = """
def reverseList(arr):
    head = build_list(arr)
    # 反转链表逻辑
    prev = None
    curr = head
    while curr:
        next_temp = curr.next
        curr.next = prev
        prev = curr
        curr = next_temp
    return serialize_list(prev)
        """

        test_inputs = parsed_inputs  # [[1,2,3,4,5]]

        expected = parse_inputs([case["expected"]])[0]  # [5,4,3,2,1]

        patches_and_tests.append((patched_code, test_inputs, expected))

    # 运行测试
    entry_point = "reverseList"
    results = run_multiple_tests(patches_and_tests, entry_point, timeout=2.0, max_workers=2)

    # 输出结果
    for i, result in enumerate(results):
        print(f"Test {i+1}: {result}")
        if result and result.get('status') == 'Pass':
            print("  Passed!")
        elif result:
            print(f"  Failed: {result.get('status')}")

if __name__ == "__main__":
    main()
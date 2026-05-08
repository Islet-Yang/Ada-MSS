import multiprocessing
import traceback
import sys
import io
import ast
import collections
import inspect
import json
import re
from collections import Counter, defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

# 数据结构定义
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def build_list(arr):
    """从数组构建链表"""
    if not arr:
        return None
    head = ListNode(arr[0])
    current = head
    for val in arr[1:]:
        current.next = ListNode(val)
        current = current.next
    return head

def build_tree(arr):
    """从数组构建二叉树（层序遍历）"""
    if not arr:
        return None
    root = TreeNode(arr[0])
    queue = [root]
    i = 1
    while i < len(arr):
        node = queue.pop(0)
        if i < len(arr) and arr[i] is not None:
            node.left = TreeNode(arr[i])
            queue.append(node.left)
        i += 1
        if i < len(arr) and arr[i] is not None:
            node.right = TreeNode(arr[i])
            queue.append(node.right)
        i += 1
    return root

def serialize_list(head):
    """序列化链表为数组"""
    result = []
    while head:
        result.append(head.val)
        head = head.next
    return result

def serialize_tree(root):
    """序列化二叉树为层序数组"""
    if not root:
        return []
    result = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node:
            result.append(node.val)
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append(None)
    # 移除末尾的None
    while result and result[-1] is None:
        result.pop()
    return result

def parse_inputs(raw_inputs: list) -> list:
    """
    解析LeetCode风格的字符串输入为Python对象。
    例如: ["[1,2,3]", "5"] -> [[1,2,3], 5]
    """
    parsed = []
    for inp in raw_inputs:
        if isinstance(inp, str):
            parsed.append(normalize_literal(inp))
        else:
            parsed.append(inp)
    return parsed

def normalize_literal(value: str):
    """Parse LeetCode-style literals, including true/false/null."""
    text = value.strip()
    text = re.sub(r"\btrue\b", "True", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfalse\b", "False", text, flags=re.IGNORECASE)
    text = re.sub(r"\bnull\b", "None", text, flags=re.IGNORECASE)
    try:
        return ast.literal_eval(text)
    except Exception:
        try:
            return json.loads(value)
        except Exception:
            return value.strip().strip('"')

def split_top_level_commas(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    in_string = False
    quote = ""
    current: list[str] = []
    for ch in text:
        if ch in {'"', "'"} and (not current or current[-1] != "\\"):
            if not in_string:
                in_string = True
                quote = ch
            elif quote == ch:
                in_string = False
                quote = ""
        elif not in_string:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth = max(depth - 1, 0)
        if ch == "," and depth == 0 and not in_string:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts

def parse_example_block(block: str) -> tuple[list, object] | None:
    if "Input:" not in block or "Output:" not in block:
        return None
    input_part, output_part = block.split("Output:", 1)
    input_part = input_part.split("Input:", 1)[1].strip()
    output_line = output_part.strip().splitlines()[0].strip()
    if not input_part or not output_line:
        return None

    args = []
    for line in input_part.splitlines():
        line = line.strip().lstrip("#").strip()
        if not line:
            continue
        for part in split_top_level_commas(line):
            if not part:
                continue
            if "=" in part:
                _, value = part.split("=", 1)
                args.append(normalize_literal(value))
            else:
                args.append(normalize_literal(part))
    return args, normalize_literal(output_line)

def extract_debugbench_test_cases(test_text: str) -> list[tuple[list, object]]:
    """Extract runnable examples from DebugBench's markdown-like test field."""
    cases: list[tuple[list, object]] = []
    current: list[str] = []
    for line in test_text.splitlines():
        if "Input:" in line:
            current = [line]
        elif current:
            current.append(line)
            if "Output:" in line:
                parsed = parse_example_block("\n".join(current))
                if parsed is not None:
                    cases.append(parsed)
                current = []
    return cases

def infer_entry_point(code: str) -> str:
    match = re.search(r"def\s+([A-Za-z_]\w*)\s*\(", code)
    return match.group(1) if match else "solution"

def _sandbox_globals() -> dict:
    return {
        "__builtins__": __builtins__,
        "ListNode": ListNode,
        "TreeNode": TreeNode,
        "build_list": build_list,
        "build_tree": build_tree,
        "serialize_list": serialize_list,
        "serialize_tree": serialize_tree,
        "collections": collections,
        "deque": deque,
        "defaultdict": defaultdict,
        "Counter": Counter,
        "List": List,
        "Optional": Optional,
        "Dict": Dict,
        "Set": Set,
        "Tuple": Tuple,
    }

def _annotation_text(annotation) -> str:
    if annotation is inspect.Signature.empty:
        return ""
    return getattr(annotation, "__name__", str(annotation))

def _convert_inputs(func, test_inputs: list) -> list:
    try:
        params = list(inspect.signature(func).parameters.values())
    except (TypeError, ValueError):
        params = []

    converted = []
    for idx, value in enumerate(test_inputs):
        param = params[idx] if idx < len(params) else None
        name = param.name.lower() if param else ""
        annotation = _annotation_text(param.annotation) if param else ""
        if isinstance(value, list) and ("TreeNode" in annotation or name in {"root", "node"}):
            converted.append(build_tree(value))
        elif isinstance(value, list) and ("ListNode" in annotation or name in {"head", "linkedlist"}):
            converted.append(build_list(value))
        else:
            converted.append(value)
    return converted

def _normalize_result(result):
    if isinstance(result, ListNode):
        return serialize_list(result)
    if isinstance(result, TreeNode):
        return serialize_tree(result)
    return result

def worker_process(patched_code: str, entry_point: str, test_inputs: list, queue: multiprocessing.Queue):
    """
    子进程执行器：在一个受限环境中运行 LLM 生成的代码
    """
    try:
        # 1. 创建隔离的执行命名空间，并预置 LeetCode 常用类型和工具
        local_env = _sandbox_globals()
        
        # 将标准输出重定向，防止 LLM 代码里的 print 污染主程序的控制台日志
        captured_stdout = io.StringIO()
        sys.stdout = captured_stdout

        # 2. 编译并执行补丁代码
        exec(patched_code, local_env, local_env)

        # 3. 检查入口函数是否存在，优先支持 LeetCode 的 Solution().method(...)
        if "Solution" in local_env and hasattr(local_env["Solution"], entry_point):
            func = getattr(local_env["Solution"](), entry_point)
        elif entry_point in local_env:
            func = local_env[entry_point]
        else:
            queue.put({
                "status": "RuntimeError", 
                "error_type": "NameError", 
                "message": f"Entry point function '{entry_point}' not found in the generated patch."
            })
            return

        # 4. 执行测试用例 (假设 test_inputs 是解包后的参数列表)
        # 注意：DebugBench 的输入可能是多参数的，所以使用 *解包
        result = func(*_convert_inputs(func, test_inputs))

        # 恢复标准输出
        sys.stdout = sys.__stdout__

        # 5. 将成功运行的结果塞入队列
        queue.put({
            "status": "Success",
            "result": _normalize_result(result)
        })

    except Exception as e:
        # 恢复标准输出
        sys.stdout = sys.__stdout__
        
        # 核心：精准捕获异常类型，喂给 Ada-MSS 的 Escalation Policy
        error_type = type(e).__name__  # 例如: 'IndexError', 'TypeError'
        error_msg = str(e)
        traceback_info = traceback.format_exc()
        
        queue.put({
            "status": "RuntimeError",
            "error_type": error_type,
            "message": error_msg,
            "traceback": traceback_info
        })

def validate_with_timeout(patched_code: str, entry_point: str, test_inputs: list, expected_output: any, timeout_seconds: float = 2.0) -> dict:
    """
    主控进程：带有超时控制的验证沙箱
    """
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=worker_process,
        args=(patched_code, entry_point, test_inputs, queue)
    )

    process.start()
    process.join(timeout_seconds)

    # 如果进程在超时时间后依然存活，说明发生了死循环或严重阻塞
    if process.is_alive():
        process.terminate()  # 强制杀死子进程
        process.join()
        return {
            "status": "TimeoutError", 
            "error_type": "Timeout", 
            "message": f"Execution exceeded {timeout_seconds} seconds."
        }

    # 如果队列为空，说明子进程崩溃（如 Segmentation fault）
    if queue.empty():
         return {
             "status": "SystemError", 
             "error_type": "Crash", 
             "message": "Process died unexpectedly (possible memory overflow or segfault)."
         }

    # 获取执行结果
    worker_result = queue.get()

    if worker_result["status"] == "Success":
        # 结果比对：这里可以根据 DebugBench 的具体数据类型进行定制化比对
        # 例如对于浮点数可能需要 math.isclose()
        if worker_result["result"] == expected_output:
            return {"status": "Pass", "message": "Test passed."}
        else:
            return {
                "status": "WrongAnswer", 
                "expected": expected_output, 
                "actual": worker_result["result"]
            }

    # 直接返回 RuntimeError 给上一层，用于触发 AST 降级/升级
    return worker_result

def run_multiple_tests(patches_and_tests, entry_point, timeout=2.0, max_workers=None):
    """
    顺序运行多个测试用例（由于multiprocessing.Pool的worker是daemon，不能启动子进程）。
    patches_and_tests: list of (patched_code, test_inputs, expected_output)
    test_inputs 应为已解析的Python对象列表。
    """
    results = []
    for patch, inputs, expected in patches_and_tests:
        result = validate_with_timeout(patch, entry_point, inputs, expected, timeout)
        results.append(result)
    return results

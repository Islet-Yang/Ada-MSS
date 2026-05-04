import multiprocessing
import traceback
import sys
import io
import ast

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
            parsed.append(ast.literal_eval(inp))
        else:
            parsed.append(inp)
    return parsed

def worker_process(patched_code: str, entry_point: str, test_inputs: list, queue: multiprocessing.Queue):
    """
    子进程执行器：在一个受限环境中运行 LLM 生成的代码
    """
    try:
        # 1. 创建隔离的执行命名空间，并预置数据结构和构建函数
        local_env = {}
        local_env['ListNode'] = ListNode
        local_env['TreeNode'] = TreeNode
        local_env['build_list'] = build_list
        local_env['build_tree'] = build_tree
        local_env['serialize_list'] = serialize_list
        local_env['serialize_tree'] = serialize_tree
        
        # 将标准输出重定向，防止 LLM 代码里的 print 污染主程序的控制台日志
        captured_stdout = io.StringIO()
        sys.stdout = captured_stdout

        # 2. 编译并执行补丁代码
        exec(patched_code, local_env, local_env)

        # 3. 检查入口函数是否存在
        if entry_point not in local_env:
            queue.put({
                "status": "RuntimeError", 
                "error_type": "NameError", 
                "message": f"Entry point function '{entry_point}' not found in the generated patch."
            })
            return

        func = local_env[entry_point]

        # 4. 执行测试用例 (假设 test_inputs 是解包后的参数列表)
        # 注意：DebugBench 的输入可能是多参数的，所以使用 *解包
        result = func(*test_inputs)

        # 恢复标准输出
        sys.stdout = sys.__stdout__

        # 5. 将成功运行的结果塞入队列
        queue.put({
            "status": "Success",
            "result": result
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
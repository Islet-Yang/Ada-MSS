from ada_mss.data import RepairTask
from ada_mss.infer import run_repair


if __name__ == "__main__":
    task = RepairTask(
        task_id="demo-1",
        buggy_code="""def add(a, b):\n    # BUG: should return sum\n    return a - b\n""",
        tests="""def test_add():\n    assert add(2, 3) == 5\n""",
    )

    result = run_repair(config_path="configs/default.json", task=task)
    print("Status:", result.status)
    print("Provider:", result.provider)
    print("Model:", result.model)
    print("Final Level:", result.final_level)
    print("Attempts:", result.attempts)
    print("Trace:", " -> ".join(result.trace))
    print("Candidate Patch:\n", result.candidate_patch)

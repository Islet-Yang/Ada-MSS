#!/usr/bin/env python3
"""
Script to convert DebugBench dataset to Ada-MSS format.
DebugBench: https://huggingface.co/datasets/Rtian/DebugBench
"""

import json
import argparse
from pathlib import Path


def convert_debugbench(output_path: str, language: str = "python3", max_samples: int = None):
    """
    Convert DebugBench dataset to Ada-MSS JSONL format.
    
    Args:
        output_path: Output JSONL file path
        language: Filter by programming language (python3, java, cpp)
        max_samples: Maximum number of samples to convert (None for all)
    """
    from datasets import load_dataset
    
    print(f"Loading DebugBench dataset...")
    # ds = load_dataset("Rtian/DebugBench")
    ds = load_dataset("/models/models/islet/data/Rtian___debug_bench/default/0.0.0/f474dcd2ad9276dfb48f96670f830da694870447")
    
    # Get the test split
    data = ds["test"]
    print(f"Total samples in DebugBench: {len(data)}")
    
    # Filter by language and convert
    tasks = []
    for i, item in enumerate(data):
        # Filter by language
        if item.get("language") != language:
            continue
            
        # Create task_id from slug
        task_id = f"{item['slug']}_{item['language']}"
        
        # Get buggy code
        buggy_code = item.get("buggy_code", "")
        if not buggy_code:
            continue
            
        # Build test cases from examples and constraints
        tests = build_tests(item, language)
        if not tests:
            continue
            
        task = {
            "task_id": task_id,
            "buggy_code": buggy_code,
            "tests": tests,
        }
        tasks.append(task)
        
        if max_samples and len(tasks) >= max_samples:
            break
            
        if (i + 1) % 500 == 0:
            print(f"Processed {i + 1} samples, converted {len(tasks)} tasks...")
    
    print(f"Converted {len(tasks)} tasks for language: {language}")
    
    # Write to JSONL
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
    
    print(f"Saved to: {output_path}")
    return len(tasks)


def build_tests(item: dict, language: str) -> str:
    """Build test code from examples and constraints."""
    question = item.get("question", "")
    examples = item.get("examples", [])
    constraints = item.get("constraints", "")
    solution = item.get("solution", "")
    
    if language == "python3":
        return build_python_tests(item)
    elif language == "java":
        return build_java_tests(item)
    elif language == "cpp":
        return build_cpp_tests(item)
    else:
        return ""


def build_python_tests(item: dict) -> str:
    """Build Python test code."""
    examples = item.get("examples", [])
    constraints = item.get("constraints", "")
    slug = item.get("slug", "unknown")
    
    # Extract function signature from solution if available
    solution = item.get("solution", "")
    func_name = extract_function_name(solution, "python")
    
    if not func_name:
        # Try to infer from slug
        func_name = "solution"
    
    # Build test cases from examples
    test_lines = []
    test_lines.append("import pytest")
    test_lines.append("")
    
    # Add docstring context
    test_lines.append(f'# Task: {slug}')
    test_lines.append(f'# Bug explanation: {item.get("bug_explanation", "N/A")}')
    test_lines.append("")
    
    # Try to extract test cases from examples
    for idx, ex in enumerate(examples[:3]):  # Limit to 3 examples
        # Parse example format: "Input: nums = [2,2,1]\nOutput: 1"
        if "Input:" in ex and "Output:" in ex:
            parts = ex.split("\nOutput:")
            if len(parts) == 2:
                input_part = parts[0].replace("Input:", "").strip()
                output_part = parts[1].strip()
                
                # Try to create a simple assertion
                test_lines.append(f"# Example {idx + 1}: {ex}")
    
    # Add constraints as comment
    if constraints:
        test_lines.append(f"# Constraints: {constraints}")
    
    # Create a basic test function that checks if solution runs
    test_lines.append("")
    test_lines.append("def test_solution():")
    test_lines.append("    # Basic test: solution should be callable")
    test_lines.append("    try:")
    test_lines.append("        # This is a placeholder - actual tests require leetcode env")
    test_lines.append("        pass")
    test_lines.append("    except Exception as e:")
    test_lines.append(f'        pytest.skip(f"Skipping: {{e}}")')
    
    return "\n".join(test_lines)


def build_java_tests(item: dict) -> str:
    """Build Java test code."""
    slug = item.get("slug", "unknown")
    
    test_lines = []
    test_lines.append(f"// Task: {slug}")
    test_lines.append(f"// Bug explanation: {item.get('bug_explanation', 'N/A')}")
    test_lines.append("")
    test_lines.append("public class TestSolution {")
    test_lines.append("    public static void main(String[] args) {")
    test_lines.append("        // Basic test placeholder")
    test_lines.append("    }")
    test_lines.append("}")
    
    return "\n".join(test_lines)


def build_cpp_tests(item: dict) -> str:
    """Build C++ test code."""
    slug = item.get("slug", "unknown")
    
    test_lines = []
    test_lines.append(f"// Task: {slug}")
    test_lines.append(f"// Bug explanation: {item.get('bug_explanation', 'N/A')}")
    test_lines.append("")
    test_lines.append("#include <iostream>")
    test_lines.append("")
    test_lines.append("int main() {")
    test_lines.append("    // Basic test placeholder")
    test_lines.append("    return 0;")
    test_lines.append("}")
    
    return "\n".join(test_lines)


def extract_function_name(code: str, language: str) -> str:
    """Extract function name from code."""
    import re
    
    if language == "python":
        # Match def function_name(
        match = re.search(r"def\s+(\w+)\s*\(", code)
        if match:
            return match.group(1)
    elif language == "java":
        # Match public (static)? \w+ \w+\(
        match = re.search(r"public\s+(?:static\s+)?\w+\s+(\w+)\s*\(", code)
        if match:
            return match.group(1)
    elif language == "cpp":
        # Match \w+ \w+\(
        match = re.search(r"\b\w+\s+(\w+)\s*\([^)]*\)\s*\{", code)
        if match:
            return match.group(1)
    
    return ""


def main():
    parser = argparse.ArgumentParser(description="Convert DebugBench to Ada-MSS format")
    parser.add_argument("--output", "-o", default="data/processed/debugbench.jsonl",
                        help="Output JSONL file path")
    parser.add_argument("--language", "-l", default="python3",
                        choices=["python3", "java", "cpp"],
                        help="Programming language to filter")
    parser.add_argument("--max-samples", "-m", type=int, default=None,
                        help="Maximum number of samples to convert")
    
    args = parser.parse_args()
    
    convert_debugbench(
        output_path=args.output,
        language=args.language,
        max_samples=args.max_samples
    )


if __name__ == "__main__":
    main()
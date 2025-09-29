#!/usr/bin/env python3
"""
Comprehensive dead code and unused variable analysis for API endpoints.
"""

import ast
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor for analyzing Python code."""

    def __init__(self, filename: str):
        self.filename = filename
        self.issues = []
        self.scope_stack = []
        self.imports = set()
        self.defined_names = set()
        self.used_names = set()
        self.function_params = defaultdict(set)
        self.current_function = None
        self.line_number = 1

    def add_issue(
        self, issue_type: str, line: int, description: str, context: str = ""
    ):
        """Add an issue to the list."""
        self.issues.append(
            {
                "type": issue_type,
                "line": line,
                "description": description,
                "context": context,
                "file": self.filename,
            }
        )

    def visit_Import(self, node):
        """Track import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
            self.defined_names.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Track from imports."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
            self.defined_names.add(name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Analyze function definitions."""
        self.defined_names.add(node.name)

        # Track function parameters
        old_function = self.current_function
        self.current_function = node.name

        # Parameters
        params = set()
        for arg in node.args.args:
            params.add(arg.arg)
            self.defined_names.add(arg.arg)

        # Keyword-only arguments
        for arg in node.args.kwonlyargs:
            params.add(arg.arg)
            self.defined_names.add(arg.arg)

        # *args and **kwargs
        if node.args.vararg:
            params.add(node.args.vararg.arg)
            self.defined_names.add(node.args.vararg.arg)
        if node.args.kwarg:
            params.add(node.args.kwarg.arg)
            self.defined_names.add(node.args.kwarg.arg)

        self.function_params[node.name] = params

        # Visit function body
        old_scope = self.scope_stack.copy()
        self.scope_stack.append(f"function:{node.name}")

        for child in node.body:
            self.visit(child)

        self.scope_stack = old_scope
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node):
        """Handle async function definitions."""
        self.visit_FunctionDef(node)  # Same logic

    def visit_ClassDef(self, node):
        """Analyze class definitions."""
        self.defined_names.add(node.name)
        old_scope = self.scope_stack.copy()
        self.scope_stack.append(f"class:{node.name}")
        self.generic_visit(node)
        self.scope_stack = old_scope

    def visit_Assign(self, node):
        """Track variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defined_names.add(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        """Track annotated assignments."""
        if isinstance(node.target, ast.Name):
            self.defined_names.add(node.target.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        """Track name usage."""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            self.defined_names.add(node.id)
        self.generic_visit(node)

    def visit_For(self, node):
        """Handle for loop variables."""
        if isinstance(node.target, ast.Name):
            self.defined_names.add(node.target.id)
        self.generic_visit(node)

    def visit_comprehension(self, node):
        """Handle comprehension variables."""
        if isinstance(node.target, ast.Name):
            self.defined_names.add(node.target.id)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        """Handle exception variables."""
        if node.name:
            self.defined_names.add(node.name)
        self.generic_visit(node)

    def visit_With(self, node):
        """Handle with statement variables."""
        for item in node.items:
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                self.defined_names.add(item.optional_vars.id)
        self.generic_visit(node)

    def analyze_unused_variables(self):
        """Find unused variables."""
        unused = self.defined_names - self.used_names

        # Filter out common patterns that are OK to be unused
        filtered_unused = set()
        for name in unused:
            # Skip private variables (convention)
            if name.startswith("_"):
                continue
            # Skip imports that might be used for type hints
            if name in self.imports:
                continue
            # Skip common patterns
            if name in {"logger", "router", "app", "__name__", "__file__"}:
                continue
            filtered_unused.add(name)

        return filtered_unused

    def analyze_unused_parameters(self):
        """Find unused function parameters."""
        unused_params = []
        for func_name, params in self.function_params.items():
            for param in params:
                # Skip 'self' and 'cls'
                if param in {"self", "cls"}:
                    continue
                # Skip parameters that start with underscore
                if param.startswith("_"):
                    continue
                # Skip common dependency injection patterns
                if param in {"db", "request", "background_tasks"}:
                    continue

                if param not in self.used_names:
                    unused_params.append((func_name, param))

        return unused_params


def analyze_file(file_path: Path) -> List[Dict[str, Any]]:
    """Analyze a single Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        analyzer = CodeAnalyzer(str(file_path))
        analyzer.visit(tree)

        # Find unused variables
        unused_vars = analyzer.analyze_unused_variables()
        for var in unused_vars:
            analyzer.add_issue(
                "unused_variable",
                0,  # Would need more complex tracking for line numbers
                f"Unused variable: {var}",
                f"Variable '{var}' is defined but never used",
            )

        # Find unused parameters
        unused_params = analyzer.analyze_unused_parameters()
        for func_name, param in unused_params:
            analyzer.add_issue(
                "unused_parameter",
                0,
                f"Unused parameter: {param} in function {func_name}",
                f"Parameter '{param}' in function '{func_name}' is never used",
            )

        return analyzer.issues

    except Exception as e:
        return [
            {
                "type": "analysis_error",
                "line": 0,
                "description": f"Failed to analyze file: {str(e)}",
                "context": str(file_path),
                "file": str(file_path),
            }
        ]


def find_duplicate_code(files: List[Path]) -> List[Dict[str, Any]]:
    """Find potential duplicate code blocks."""
    # This is a simplified implementation
    # A full implementation would use more sophisticated techniques
    issues = []

    # For now, just look for identical function names
    function_names = defaultdict(list)

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_names[node.name].append(str(file_path))

        except Exception:
            continue

    # Find duplicate function names across files
    for func_name, file_list in function_names.items():
        if len(file_list) > 1:
            issues.append(
                {
                    "type": "potential_duplicate",
                    "line": 0,
                    "description": f"Function '{func_name}' appears in multiple files",
                    "context": f"Files: {', '.join(file_list)}",
                    "file": "multiple",
                }
            )

    return issues


def main():
    """Main analysis function."""
    # Endpoint files to analyze
    endpoint_files = [
        Path("src/jd_ingestion/api/endpoints/jobs.py"),
        Path("src/jd_ingestion/api/endpoints/ingestion.py"),
        Path("src/jd_ingestion/api/endpoints/search.py"),
        Path("src/jd_ingestion/api/endpoints/analytics.py"),
        Path("src/jd_ingestion/api/endpoints/analysis.py"),
        Path("src/jd_ingestion/api/endpoints/health.py"),
    ]

    all_issues = []

    print("=== DEAD CODE AND UNUSED VARIABLE ANALYSIS ===")
    print()

    for file_path in endpoint_files:
        if file_path.exists():
            print(f"Analyzing {file_path}...")
            issues = analyze_file(file_path)
            all_issues.extend(issues)
        else:
            print(f"File not found: {file_path}")

    print("\nLooking for duplicate code patterns...")
    existing_files = [f for f in endpoint_files if f.exists()]
    duplicate_issues = find_duplicate_code(existing_files)
    all_issues.extend(duplicate_issues)

    # Group issues by type
    issues_by_type = defaultdict(list)
    for issue in all_issues:
        issues_by_type[issue["type"]].append(issue)

    print(f"\n=== ANALYSIS RESULTS ({len(all_issues)} total issues) ===")

    for issue_type, issues in issues_by_type.items():
        print(f"\n{issue_type.upper().replace('_', ' ')} ({len(issues)} issues):")
        for issue in issues[:10]:  # Limit output
            file_name = (
                Path(issue["file"]).name
                if issue["file"] != "multiple"
                else "multiple files"
            )
            print(f"  - {file_name}: {issue['description']}")
            if issue["context"]:
                print(f"    Context: {issue['context']}")
        if len(issues) > 10:
            print(f"    ... and {len(issues) - 10} more")

    if not all_issues:
        print("No issues found! Code appears clean.")

    return all_issues


if __name__ == "__main__":
    main()

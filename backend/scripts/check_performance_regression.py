#!/usr/bin/env python3
"""
Performance Regression Checker

Compares current performance test results against baseline metrics
to detect performance regressions in the application.
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceRegression:
    """Performance regression detection and reporting."""

    def __init__(self, threshold_percentage: float = 10.0):
        """
        Initialize performance regression checker.

        Args:
            threshold_percentage: Maximum allowed performance degradation (default: 10%)
        """
        self.threshold = threshold_percentage / 100.0
        self.baseline_metrics = {}
        self.current_metrics = {}

    def load_current_results(self, results_file: Path) -> Dict[str, Any]:
        """Load current performance test results from JSON file."""
        logger.info(f"Loading current results from {results_file}")

        try:
            with open(results_file, 'r') as f:
                data = json.load(f)

            # Extract pytest-benchmark results
            if 'benchmarks' in data:
                metrics = {}
                for benchmark in data['benchmarks']:
                    name = benchmark['name']
                    stats = benchmark['stats']
                    metrics[name] = {
                        'mean': stats['mean'],
                        'min': stats['min'],
                        'max': stats['max'],
                        'stddev': stats['stddev'],
                        'median': stats['median'],
                        'ops_per_second': stats.get('ops', 0)
                    }
                return metrics

            logger.warning("No benchmark data found in results file")
            return {}

        except FileNotFoundError:
            logger.error(f"Results file not found: {results_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in results file: {e}")
            return {}

    def fetch_baseline_metrics(self, baseline_branch: str = "main") -> Dict[str, Any]:
        """
        Fetch baseline performance metrics from previous runs.

        This is a simplified implementation that would typically fetch from:
        - GitHub Actions artifacts
        - Performance monitoring database
        - Baseline metrics storage
        """
        logger.info(f"Fetching baseline metrics for branch: {baseline_branch}")

        # For demonstration, use mock baseline data
        # In production, this would fetch real baseline metrics
        baseline_metrics = {
            'test_search_performance': {
                'mean': 0.15,
                'min': 0.08,
                'max': 0.35,
                'stddev': 0.05,
                'median': 0.14,
                'ops_per_second': 6.67
            },
            'test_job_listing_performance': {
                'mean': 0.12,
                'min': 0.06,
                'max': 0.28,
                'stddev': 0.04,
                'median': 0.11,
                'ops_per_second': 8.33
            },
            'test_translation_memory_search': {
                'mean': 0.08,
                'min': 0.04,
                'max': 0.18,
                'stddev': 0.03,
                'median': 0.07,
                'ops_per_second': 12.5
            },
            'test_vector_similarity_search': {
                'mean': 0.25,
                'min': 0.12,
                'max': 0.45,
                'stddev': 0.08,
                'median': 0.23,
                'ops_per_second': 4.0
            }
        }

        return baseline_metrics

    def compare_metrics(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare current metrics against baseline and identify regressions."""
        regressions = []
        improvements = []

        for test_name, current_stats in current.items():
            if test_name not in baseline:
                logger.warning(f"No baseline data for test: {test_name}")
                continue

            baseline_stats = baseline[test_name]

            # Compare mean execution time (primary metric)
            current_mean = current_stats['mean']
            baseline_mean = baseline_stats['mean']

            if baseline_mean > 0:
                change_ratio = (current_mean - baseline_mean) / baseline_mean
                change_percentage = change_ratio * 100

                result = {
                    'test_name': test_name,
                    'metric': 'mean_execution_time',
                    'current_value': current_mean,
                    'baseline_value': baseline_mean,
                    'change_ratio': change_ratio,
                    'change_percentage': change_percentage,
                    'is_regression': change_ratio > self.threshold,
                    'is_improvement': change_ratio < -0.05,  # 5% improvement threshold
                }

                if result['is_regression']:
                    regressions.append(result)
                elif result['is_improvement']:
                    improvements.append(result)

            # Compare operations per second (if available)
            current_ops = current_stats.get('ops_per_second', 0)
            baseline_ops = baseline_stats.get('ops_per_second', 0)

            if baseline_ops > 0:
                ops_change_ratio = (current_ops - baseline_ops) / baseline_ops
                ops_change_percentage = ops_change_ratio * 100

                ops_result = {
                    'test_name': test_name,
                    'metric': 'operations_per_second',
                    'current_value': current_ops,
                    'baseline_value': baseline_ops,
                    'change_ratio': ops_change_ratio,
                    'change_percentage': ops_change_percentage,
                    'is_regression': ops_change_ratio < -self.threshold,  # Lower ops is regression
                    'is_improvement': ops_change_ratio > 0.05,
                }

                if ops_result['is_regression']:
                    regressions.append(ops_result)
                elif ops_result['is_improvement']:
                    improvements.append(ops_result)

        return regressions, improvements

    def generate_report(self, regressions: List[Dict[str, Any]], improvements: List[Dict[str, Any]]) -> str:
        """Generate a performance comparison report."""
        report = []
        report.append("# Performance Regression Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Threshold: {self.threshold * 100:.1f}%")
        report.append("")

        if regressions:
            report.append("## ⚠️ Performance Regressions Detected")
            report.append("")
            for regression in regressions:
                report.append(f"### {regression['test_name']} - {regression['metric']}")
                report.append(f"- **Current**: {regression['current_value']:.4f}")
                report.append(f"- **Baseline**: {regression['baseline_value']:.4f}")
                report.append(f"- **Change**: {regression['change_percentage']:.2f}% slower")
                report.append("")
        else:
            report.append("## ✅ No Performance Regressions Detected")
            report.append("")

        if improvements:
            report.append("## 🚀 Performance Improvements")
            report.append("")
            for improvement in improvements:
                report.append(f"### {improvement['test_name']} - {improvement['metric']}")
                report.append(f"- **Current**: {improvement['current_value']:.4f}")
                report.append(f"- **Baseline**: {improvement['baseline_value']:.4f}")
                report.append(f"- **Change**: {abs(improvement['change_percentage']):.2f}% faster")
                report.append("")

        return "\n".join(report)

    def check_performance(self, current_results_file: Path, baseline_branch: str) -> bool:
        """
        Main method to check for performance regressions.

        Returns:
            bool: True if no regressions found, False if regressions detected
        """
        logger.info("Starting performance regression check...")

        # Load current results
        self.current_metrics = self.load_current_results(current_results_file)
        if not self.current_metrics:
            logger.error("No current metrics found")
            return False

        # Fetch baseline metrics
        self.baseline_metrics = self.fetch_baseline_metrics(baseline_branch)
        if not self.baseline_metrics:
            logger.warning("No baseline metrics found - skipping regression check")
            return True

        # Compare metrics
        regressions, improvements = self.compare_metrics(self.current_metrics, self.baseline_metrics)

        # Generate and display report
        report = self.generate_report(regressions, improvements)
        print(report)

        # Log summary
        logger.info(f"Performance check complete: {len(regressions)} regressions, {len(improvements)} improvements")

        if regressions:
            logger.error("Performance regressions detected!")
            for regression in regressions:
                logger.error(
                    f"{regression['test_name']}: {regression['change_percentage']:.2f}% slower "
                    f"({regression['current_value']:.4f} vs {regression['baseline_value']:.4f})"
                )

        return len(regressions) == 0

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Check for performance regressions")
    parser.add_argument(
        "--current-results",
        type=Path,
        required=True,
        help="Path to current performance test results JSON file"
    )
    parser.add_argument(
        "--baseline-branch",
        type=str,
        default="main",
        help="Branch to use as performance baseline (default: main)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Performance degradation threshold percentage (default: 10.0)"
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with error code if regressions are found"
    )

    args = parser.parse_args()

    # Initialize regression checker
    checker = PerformanceRegression(threshold_percentage=args.threshold)

    # Run performance check
    no_regressions = checker.check_performance(args.current_results, args.baseline_branch)

    # Exit with appropriate code
    if args.fail_on_regression and not no_regressions:
        logger.error("Exiting with error due to performance regressions")
        sys.exit(1)

    logger.info("Performance regression check completed successfully")
    sys.exit(0)

if __name__ == "__main__":
    main()
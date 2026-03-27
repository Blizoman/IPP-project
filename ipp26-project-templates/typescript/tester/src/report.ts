import { CategoryReport, TestCaseDefinition, TestCaseReport, TestResult } from "./models.js";

interface CategoryAccumulator {
  total_points: number;
  passed_points: number;
  test_results: Record<string, TestCaseReport>;
}

export function buildCategoryResults(
  executed_tests: TestCaseDefinition[],
  executed_results: Record<string, TestCaseReport>
): Record<string, CategoryReport> {
  const accumulators: Record<string, CategoryAccumulator> = {};

  for (const test of executed_tests) {
    const test_result = executed_results[test.name];
    if (test_result === undefined) {
      continue;
    }

    const accumulator =
      accumulators[test.category] ??
      (accumulators[test.category] = {
        total_points: 0,
        passed_points: 0,
        test_results: {},
      });

    accumulator.test_results[test.name] = test_result;
    accumulator.total_points += test.points;

    if (test_result.result === TestResult.PASSED) {
      accumulator.passed_points += test.points;
    }
  }

  const reports: Record<string, CategoryReport> = {};
  for (const [category, accumulator] of Object.entries(accumulators)) {
    reports[category] = new CategoryReport(
      accumulator.total_points,
      accumulator.passed_points,
      accumulator.test_results
    );
  }

  return reports;
}

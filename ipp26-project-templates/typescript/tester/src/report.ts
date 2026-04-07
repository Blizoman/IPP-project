/**
 * This module aggregates individual test results into category-based reports.
 * It calculates the total points available and the points actually scored
 * for each category defined in the test suite.
 *
 * Author: Andrej Bližnák <xblizna00@fit.vut.cz>
 */

import { CategoryReport, TestCaseDefinition, TestCaseReport, TestResult } from "./models.js";

/**
 * Internal helper interface used to keep track of points and results
 * while iterating through the test cases of a specific category.
 */
interface CategoryAccumulator {
  total_points: number;
  passed_points: number;
  test_results: Record<string, TestCaseReport>;
}

/**
 * Groups executed tests by their category and calculates the total and passed points.
 * @param executed_tests - An array of test definitions that were actually executed.
 * @param executed_results - A map of test names to their detailed execution reports.
 * @returns A map of category names to their aggregated CategoryReport instances.
 */
export function buildCategoryResults(
  executed_tests: TestCaseDefinition[],
  executed_results: Record<string, TestCaseReport>
): Record<string, CategoryReport> {
  // Temporary storage to build up the points and results per category
  const accumulators: Record<string, CategoryAccumulator> = {};

  for (const test of executed_tests) {
    const test_result = executed_results[test.name];

    // Skip if the test doesn`t have a recorded result for some reason
    if (test_result === undefined) {
      continue;
    }

    // Get existing accumulator for this category or create a new empty one if it doesn`t exist yet
    const accumulator =
      accumulators[test.category] ??
      (accumulators[test.category] = {
        total_points: 0,
        passed_points: 0,
        test_results: {},
      });

    // Storing
    accumulator.test_results[test.name] = test_result;
    accumulator.total_points += test.points;

    // If the test passed, add its points to the achieved score
    if (test_result.result === TestResult.PASSED) {
      accumulator.passed_points += test.points;
    }
  }

  // Convert the raw accumulators into the final CategoryReport objects
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

/**
 * This module provides filtering logic for the discovered test cases.
 * It evaluates each test against a set of inclusion and exclusion rules,
 * supporting both exact string matching and regular expressions.
 *
 * Author: Andrej Bližnák <xblizna00@fit.vut.cz>
 */

import { TestCaseDefinition, UnexecutedReason, UnexecutedReasonCode } from "./models.js";

/**
 * Defines the configuration for filtering tests, usually parsed from CLI arguments.
 */
export interface FilterOptions {
  include: string[] | null;
  include_category: string[] | null;
  include_test: string[] | null;
  exclude: string[] | null;
  exclude_category: string[] | null;
  exclude_test: string[] | null;
  regex_filters: boolean;
}

/**
 * Represents the outcome of the filtering process.
 */
export interface FilterResult {
  executed_tests: TestCaseDefinition[];
  filtered_out: Record<string, UnexecutedReason>;
}

/**
 * Processes an array of tests and separates them into "executed" and "filtered_out"
 * based on the provided inclusion and exclusion rules.
 * @param tests - The array of discovered tests to be filtered.
 * @param args - The filtering criteria (whitelist and blacklist).
 * @returns A FilterResult containing the split test definitions.
 */
export function filterTests(tests: TestCaseDefinition[], args: FilterOptions): FilterResult {
  const executed_tests: TestCaseDefinition[] = [];
  const filtered_out: Record<string, UnexecutedReason> = {};

  for (const test of tests) {
    const has_include_filters =
      args.include !== null || args.include_category !== null || args.include_test !== null;

    let passed_include = false;

    // Phase 1: INCLUSION (Whitelist)
    if (!has_include_filters) {
      // If no inclusion filters are provided, everyone is welcome by default.
      passed_include = true;
    } else {
      const match_name = controler(test.name, args.include_test, args.regex_filters);
      const match_category = controler(test.category, args.include_category, args.regex_filters);
      const match_both_name = controler(test.name, args.include, args.regex_filters);
      const match_both_category = controler(test.category, args.include, args.regex_filters);

      if (match_name || match_category || match_both_name || match_both_category) {
        passed_include = true;
      }
    }

    if (!passed_include) {
      filtered_out[test.name] = new UnexecutedReason(UnexecutedReasonCode.FILTERED_OUT);
      continue;
    }

    // Phase 2: EXCLUSION (Blacklist)
    const ex_match_name = controler(test.name, args.exclude_test, args.regex_filters);
    const ex_match_category = controler(test.category, args.exclude_category, args.regex_filters);
    const ex_match_both_name = controler(test.name, args.exclude, args.regex_filters);
    const ex_match_both_category = controler(test.category, args.exclude, args.regex_filters);

    if (ex_match_name || ex_match_category || ex_match_both_name || ex_match_both_category) {
      filtered_out[test.name] = new UnexecutedReason(UnexecutedReasonCode.FILTERED_OUT);
      continue;
    }
    // If it passed the whitelist and isn't on the blacklist, it stays!
    executed_tests.push(test);
  }
  return {
    executed_tests: executed_tests,
    filtered_out: filtered_out,
  };
}

/**
 * A helper function to check if a specific string matches any of the provided filters.
 * * @param text - The string to check (e.g: test name or category).
 * @param filters - An array of filter strings to compare against.
 * @param is_regex - If true, evaluates filters as Regular Expressions.
 * @returns True if a match is found, false otherwise.
 */
function controler(text: string, filters: string[] | null, is_regex: boolean) {
  if (filters === null) {
    return false;
  }

  // Exact string matching
  if (!is_regex) {
    if (filters.includes(text)) {
      return true;
    }
    return false;
  }

  // Regular expression matching
  for (const filter of filters) {
    const regex = new RegExp(filter);
    if (regex.test(text)) {
      return true;
    }
  }
  return false;
}

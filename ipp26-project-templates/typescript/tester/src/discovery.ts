import { readdirSync, statSync, existsSync } from "node:fs";
import { join, parse } from "node:path";

import { TestCaseDefinition, UnexecutedReason, UnexecutedReasonCode } from "./models.js";
import { parseSolTestFile } from "./soltest-parser.js";

export interface DiscoveryResult {
  discovered_test_cases: TestCaseDefinition[];
  malformed_tests: Record<string, UnexecutedReason>;
}

export function discoverTests(dir_path: string, recursive: boolean): DiscoveryResult {
  const result: DiscoveryResult = {
    discovered_test_cases: [],
    malformed_tests: {},
  };

  const entries = readdirSync(dir_path);

  for (const entry of entries) {
    const full_path = join(dir_path, entry);
    const stat = statSync(full_path);

    if (stat.isDirectory()) {
      if (recursive) {
        const subResult = discoverTests(full_path, recursive);
        result.discovered_test_cases.push(...subResult.discovered_test_cases);
        Object.assign(result.malformed_tests, subResult.malformed_tests);
      }
    } else if (stat.isFile() && full_path.endsWith(".test")) {
      const parsed_path = parse(full_path);
      const test_name = parsed_path.name;
      const stdin_file = join(parsed_path.dir, `${test_name}.in`);
      const stdout_file = join(parsed_path.dir, `${test_name}.out`);

      try {
        const parsed_data = parseSolTestFile(full_path);
        const test_case = new TestCaseDefinition({
          ...parsed_data,
          name: test_name,
          test_source_path: full_path,
          stdin_file: existsSync(stdin_file) ? stdin_file : null,
          expected_stdout_file: existsSync(stdout_file) ? stdout_file : null,
        });

        result.discovered_test_cases.push(test_case);
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : String(error);

        if (message === "CANNOT_DETERMINE_TYPE") {
          result.malformed_tests[full_path] = new UnexecutedReason(
            UnexecutedReasonCode.CANNOT_DETERMINE_TYPE,
            "Failed to determine type of test"
          );
        } else {
          result.malformed_tests[full_path] = new UnexecutedReason(
            UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE,
            "Failed to read file"
          );
        }
      }
    }
  }
  return result;
}

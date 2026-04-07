/**
 * This module is responsible for parsing the custom SOLtest file format.
 * It extracts metadata (description, category, points, and expected exit codes)
 * from the header of the file and determines the overall type of the test case.
 *
 * Author: Andrej Bližnák <xblizna00@fit.vut.cz>
 */

import { readFileSync } from "node:fs";
import { TestCaseType } from "./models.js";

/**
 * Reads a `.test` file and extracts its configuration metadata.
 * The metadata block must be at the very top of the file and ends with the first blank line.
 * @param file_path - The absolute path to the `.test` file.
 * @returns An object containing the extracted test parameters and determined test type.
 * @throws {Error} If the test type cannot be determined (no expected exit codes provided).
 */
export function parseSolTestFile(file_path: string) {
  // Read the entire file and split it into individual lines
  const file_content = readFileSync(file_path, "utf-8");
  const lines = file_content.split(/\r?\n/);

  // Default set -> values
  let description = null;
  let category: string = "DEFAULT";
  let points: number = 1;
  const expected_parser_exit_codes: number[] = [];
  const expected_interpreter_exit_codes: number[] = [];

  // Parse header line by line (metadata h ends at first empty line)
  for (const line of lines) {
    if (line.trim() === "") {
      break;
    }

    if (line.startsWith("***")) {
      description = line.substring(3).trim();
    } else if (line.startsWith("+++")) {
      category = line.substring(3).trim();
    } else if (line.startsWith(">>>")) {
      points = parseInt(line.substring(3).trim(), 10);
    } else if (line.startsWith("!C!")) {
      expected_parser_exit_codes.push(parseInt(line.substring(3).trim(), 10));
    } else if (line.startsWith("!I!")) {
      expected_interpreter_exit_codes.push(parseInt(line.substring(3).trim(), 10));
    }
  }

  // What kind of test this is based on the provided exit codes
  let test_type: TestCaseType;
  const has_parser_codes = expected_parser_exit_codes.length > 0;
  const has_interpreter_codes = expected_interpreter_exit_codes.length > 0;

  if (has_parser_codes && !has_interpreter_codes) {
    test_type = TestCaseType.PARSE_ONLY;
  } else if (!has_parser_codes && has_interpreter_codes) {
    test_type = TestCaseType.EXECUTE_ONLY;
  } else if (has_parser_codes && has_interpreter_codes) {
    test_type = TestCaseType.COMBINED;
  } else {
    throw new Error("CANNOT_DETERMINE_TYPE");
  }

  return {
    test_type: test_type,
    description: description,
    category: category,
    points: points,
    expected_parser_exit_codes: expected_parser_exit_codes,
    expected_interpreter_exit_codes: expected_interpreter_exit_codes,
  };
}

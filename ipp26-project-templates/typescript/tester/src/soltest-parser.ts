/**
 * This module is responsible for parsing the custom SOLtest file format.
 * It extracts metadata (description, category, points, and expected exit codes)
 * from the header of the file and determines the overall type of the test case.
 *
 * Author: Andrej Bližnák <xblizna00@fit.vut.cz>
 */

import { readFileSync } from "node:fs";
import { TestCaseType } from "./models.js";

interface ParsedHeaderData {
  description: string | null;
  category: string;
  points: number;
  expected_parser_exit_codes: number[];
  expected_interpreter_exit_codes: number[];
}

function parseHeader(lines: string[]): ParsedHeaderData {
  let description: string | null = null;
  let category = "DEFAULT";
  let points = 1;
  const expected_parser_exit_codes: number[] = [];
  const expected_interpreter_exit_codes: number[] = [];

  for (const line of lines) {
    if (line.trim() === "") {
      break;
    }

    if (line.startsWith("***")) {
      description = line.substring(3).trim();
      continue;
    }

    if (line.startsWith("+++")) {
      category = line.substring(3).trim();
      continue;
    }

    if (line.startsWith(">>>")) {
      points = parseInt(line.substring(3).trim(), 10);
      continue;
    }

    if (line.startsWith("!C!")) {
      expected_parser_exit_codes.push(parseInt(line.substring(3).trim(), 10));
      continue;
    }

    if (line.startsWith("!I!")) {
      expected_interpreter_exit_codes.push(parseInt(line.substring(3).trim(), 10));
    }
  }

  return {
    description,
    category,
    points,
    expected_parser_exit_codes,
    expected_interpreter_exit_codes,
  };
}

function resolveTestType(has_parser_codes: boolean, has_interpreter_codes: boolean): TestCaseType {
  if (has_parser_codes && !has_interpreter_codes) {
    return TestCaseType.PARSE_ONLY;
  }
  if (!has_parser_codes && has_interpreter_codes) {
    return TestCaseType.EXECUTE_ONLY;
  }
  if (has_parser_codes && has_interpreter_codes) {
    return TestCaseType.COMBINED;
  }

  throw new Error("CANNOT_DETERMINE_TYPE");
}

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

  const {
    description,
    category,
    points,
    expected_parser_exit_codes,
    expected_interpreter_exit_codes,
  } = parseHeader(lines);

  // What kind of test this is based on the provided exit codes
  const has_parser_codes = expected_parser_exit_codes.length > 0;
  const has_interpreter_codes = expected_interpreter_exit_codes.length > 0;
  const test_type = resolveTestType(has_parser_codes, has_interpreter_codes);

  const parser_codes = has_parser_codes ? expected_parser_exit_codes : null;
  const interpreter_codes = has_interpreter_codes ? expected_interpreter_exit_codes : null;

  return {
    test_type: test_type,
    description: description,
    category: category,
    points: points,
    expected_parser_exit_codes: parser_codes,
    expected_interpreter_exit_codes: interpreter_codes,
  };
}

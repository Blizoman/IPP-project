import { readFileSync } from "node:fs";
import { TestCaseType } from "./models.js";

export function parseSolTestFile(file_path: string) {
  const file_content = readFileSync(file_path, "utf-8");
  const lines = file_content.split(/\r?\n/);

  let description = null;
  let category: string = "DEFAULT";
  let points: number = 1;
  const expected_parser_exit_codes: number[] = [];
  const expected_interpreter_exit_codes: number[] = [];

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

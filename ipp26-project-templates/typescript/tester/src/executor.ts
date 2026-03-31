import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  TestCaseDefinition,
  TestCaseType,
  TestResult,
  TestCaseReport,
  UnexecutedReason,
  UnexecutedReasonCode,
} from "./models.js";

export interface ExecutionResult {
  executed_results: Record<string, TestCaseReport>;
  failed_to_execute: Record<string, UnexecutedReason>;
}

function extractSolSource(testFilePath: string): string {
  const file_content = readFileSync(testFilePath, "utf-8");
  const lines = file_content.split(/\r?\n/);
  const first_blan_line_index = lines.findIndex((line) => line.trim() === "");

  if (first_blan_line_index < 0) {
    return file_content;
  }

  return lines.slice(first_blan_line_index + 1).join("\n");
}

function getFirstExistingPath(paths: string[]): string {
  for (const p of paths) {
    if (existsSync(p)) {
      return p;
    }
  }
  throw new Error(`None of the expected paths exist. Tried: ${paths.join(", ")}`);
}

// eslint-disable-next-line complexity
export function executeTests(tests: TestCaseDefinition[]): ExecutionResult {
  const executed_results: Record<string, TestCaseReport> = {};
  const failed_to_execute: Record<string, UnexecutedReason> = {};

  const module_directory = dirname(fileURLToPath(import.meta.url));
  const tester_root = resolve(module_directory, "..");

  let PARSER_SCRIPT: string;
  try {
    PARSER_SCRIPT = getFirstExistingPath([
      resolve(tester_root, "..", "..", "sol2xml", "sol_to_xml.py"), // Local dev
      "/src/sol2xml/sol_to_xml.py", // Docker
    ]);
  } catch {
    PARSER_SCRIPT = "NOT_FOUND_PARSER";
  }

  let INTERPRETER_SCRIPT: string;
  try {
    INTERPRETER_SCRIPT = getFirstExistingPath([
      resolve(tester_root, "..", "..", "python", "int", "src", "solint.py"), // Local dev
      "/src/int/src/solint.py", // Docker
      "/src/int/solint.py",
    ]);
  } catch {
    INTERPRETER_SCRIPT = "NOT_FOUND_INTERPRETER";
  }

  const local_venv_py = resolve(
    tester_root,
    "..",
    "..",
    "python",
    "int",
    ".venv",
    "bin",
    "python"
  );
  const PYTHON_EXECUTABLE = existsSync(local_venv_py) ? local_venv_py : "python3";

  for (const test of tests) {
    let input_data: string | undefined = undefined;
    let temp_directory: string | null = null;
    let source_path: string | null = null;

    let p_status: number | null = null;
    let p_stdout: string | null = null;
    let p_stderr: string | null = null;

    let i_status: number | null = null;
    let i_stdout: string | null = null;
    let i_stderr: string | null = null;

    let diff_out: string | null = null;

    if (test.stdin_file !== null && existsSync(test.stdin_file)) {
      input_data = readFileSync(test.stdin_file, "utf-8");
    }

    try {
      temp_directory = mkdtempSync(join(tmpdir(), "sol26-tester-"));
      source_path = join(temp_directory, `${test.name}.sol`);
      writeFileSync(source_path, extractSolSource(test.test_source_path), "utf-8");

      if (test.test_type === TestCaseType.PARSE_ONLY || test.test_type === TestCaseType.COMBINED) {
        const parser_process = spawnSync(PYTHON_EXECUTABLE, [PARSER_SCRIPT, source_path], {
          encoding: "utf-8",
        });

        if (parser_process.error) {
          throw new Error(`Unable to start Python`);
        }

        p_status = parser_process.status as number;
        p_stdout = parser_process.stdout;
        p_stderr = parser_process.stderr;

        if (
          test.expected_parser_exit_codes !== null &&
          !test.expected_parser_exit_codes.includes(p_status)
        ) {
          executed_results[test.name] = new TestCaseReport(
            TestResult.UNEXPECTED_PARSER_EXIT_CODE,
            p_status,
            null,
            p_stdout,
            p_stderr
          );
          continue;
        }

        if (test.test_type === TestCaseType.PARSE_ONLY) {
          executed_results[test.name] = new TestCaseReport(
            TestResult.PASSED,
            p_status,
            null,
            p_stdout,
            p_stderr
          );
          continue;
        }
      }

      const interpreterArgs = ["--source", source_path];

      if (test.test_type === TestCaseType.COMBINED) {
        if (p_stdout === null) {
          throw new Error("Parser produced no output for COMBINED test");
        }

        const xmlPath = join(temp_directory, `${test.name}.xml`);
        writeFileSync(xmlPath, p_stdout, "utf-8");
        interpreterArgs[1] = xmlPath;
      }

      if (test.stdin_file !== null && existsSync(test.stdin_file)) {
        interpreterArgs.push("--input", test.stdin_file);
      }

      const interpreter_process = spawnSync(
        PYTHON_EXECUTABLE,
        [INTERPRETER_SCRIPT, ...interpreterArgs],
        {
          encoding: "utf-8",
          input: input_data,
        }
      );

      if (interpreter_process.error) {
        throw new Error(`Unable to start Interpreter`);
      }

      i_status = interpreter_process.status as number;
      i_stdout = interpreter_process.stdout;
      i_stderr = interpreter_process.stderr;

      if (
        test.expected_interpreter_exit_codes !== null &&
        !test.expected_interpreter_exit_codes.includes(i_status)
      ) {
        executed_results[test.name] = new TestCaseReport(
          TestResult.UNEXPECTED_INTERPRETER_EXIT_CODE,
          p_status,
          i_status,
          p_stdout,
          p_stderr,
          i_stdout,
          i_stderr
        );
        continue;
      }

      if (
        i_status === 0 &&
        test.expected_stdout_file !== null &&
        existsSync(test.expected_stdout_file)
      ) {
        const diff_process = spawnSync("diff", [test.expected_stdout_file, "-"], {
          encoding: "utf-8",
          input: i_stdout,
        });

        if (diff_process.error) {
          throw new Error(`Unable to start diff tool`);
        }

        diff_out = diff_process.stdout;

        if (diff_process.status !== 0) {
          executed_results[test.name] = new TestCaseReport(
            TestResult.INTERPRETER_RESULT_DIFFERS,
            p_status,
            i_status,
            p_stdout,
            p_stderr,
            i_stdout,
            i_stderr,
            diff_out
          );
          continue;
        }
      }

      executed_results[test.name] = new TestCaseReport(
        TestResult.PASSED,
        p_status,
        i_status,
        p_stdout,
        p_stderr,
        i_stdout,
        i_stderr,
        diff_out
      );
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      failed_to_execute[test.name] = new UnexecutedReason(
        UnexecutedReasonCode.CANNOT_EXECUTE,
        message
      );
    } finally {
      if (temp_directory !== null) {
        rmSync(temp_directory, { recursive: true, force: true });
      }
    }
  }

  return {
    executed_results: executed_results,
    failed_to_execute: failed_to_execute,
  };
}

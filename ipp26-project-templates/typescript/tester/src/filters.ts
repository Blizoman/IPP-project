import { TestCaseDefinition, UnexecutedReason, UnexecutedReasonCode } from "./models.js"

export interface FilterOptions {
    include: string[] | null;
    include_category: string[] | null;
    include_test: string[] | null;
    exclude: string[] | null;
    exclude_category: string[] | null;
    exclude_test: string[] | null;
    regex_filters: boolean;
}

export interface FilterResult {
    executed_tests: TestCaseDefinition[];
    filtered_out: Record<string, UnexecutedReason>;
}

export function filterTests(tests: TestCaseDefinition[], args: FilterOptions): FilterResult {
    const executed_tests: TestCaseDefinition[] = []
    const filtered_out: Record<string, UnexecutedReason> = {};

    for (const test of tests) {
        const has_include_filters = args.include !== null || 
                                    args.include_category !== null || 
                                    args.include_test !== null;
        
        let passed_include = false;

        if (!has_include_filters) {
            passed_include = true;
        }
        else{
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

        const ex_match_name = controler(test.name, args.exclude_test, args.regex_filters);
        const ex_match_category = controler(test.category, args.exclude_category, args.regex_filters);
        const ex_match_both_name = controler(test.name, args.exclude, args.regex_filters);
        const ex_match_both_category = controler(test.category, args.exclude, args.regex_filters);

        if (ex_match_name || ex_match_category || ex_match_both_name || ex_match_both_category) {
            filtered_out[test.name] = new UnexecutedReason(UnexecutedReasonCode.FILTERED_OUT);
            continue;
        }

        executed_tests.push(test); 
        
    }
    return {
        executed_tests: executed_tests,
        filtered_out: filtered_out
    };
}

function controler(text: string, filters: string[] | null, is_regex: boolean) {
    if (filters === null) {
        return false;
    }

    if (!is_regex) {
        if (filters.includes(text)) {
            return true;
        }
        return false;
    }
    
    for (const filter of filters) {
        const regex = new RegExp(filter)
        if (regex.test(text)) {
            return true;
        }
    }
    return false;
}
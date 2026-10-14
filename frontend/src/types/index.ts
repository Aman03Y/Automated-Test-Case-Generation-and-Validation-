export type PriorityLevel = "Critical" | "High" | "Medium" | "Low";

export type ValidationStatus = "PASS" | "WARNING" | "FAIL";

export interface Requirement {
  id: string;
  requirement: string;
  category?: string;
  source_file?: string;
  created_at?: string;
}

export interface TestCase {
  id: string;
  title: string;
  description: string;
  steps: string[];
  expected_result: string;
  priority: PriorityLevel | string;
  requirement_ids?: string[];
  requirement_id?: string;
}

export interface DuplicateMatch {
  tc1_id: string;
  tc2_id: string;
  similarity_score: number;
  similarity_percentage: number;
  is_duplicate: boolean;
  testcase_1?: string;
  testcase_2?: string;
  similarity?: number;
  duplicate?: boolean;
}

export interface TestCaseValidationResult {
  testcase_id: string;
  status: ValidationStatus;
  score: number;
  errors: string[];
  warnings: string[];
  mapped_requirement_id?: string;
  is_duplicate: boolean;
  duplicate_with: string[];
  duplicate_matches?: Array<{
    other_tc_id: string;
    similarity_percentage: number;
    similarity_score: number;
  }>;
}

export interface CoverageResult {
  total_requirements: number;
  covered_requirements_count: number;
  coverage_percentage: number;
  covered_requirements: string[];
  missing_requirements: string[];
  mapped_test_cases: Record<string, string[]>;
  mapping?: Record<string, string[]>;
}

export interface ScoreBreakdown {
  coverage: number;
  average_quality: number;
  duplicate_penalty: number;
  formatting: number;
}

export interface QualityBreakdown {
  overall_score: number;
  grade: string;
  coverage: number;
  duplicate_rate: number;
  average_testcase_score: number;
  pass_count: number;
  warning_count: number;
  fail_count: number;
  score_breakdown: ScoreBreakdown;
  visual_summary: string;
}

export interface TestCaseRecommendation {
  testcase_id: string;
  recommendations: string[];
  priority: PriorityLevel | string;
}

export interface RecommendationsResponse {
  testcase_recommendations: TestCaseRecommendation[];
  project_recommendations: string[];
  uncovered_requirement_recommendations: string[];
}

export interface TraceabilityMatrixRow {
  requirement_id: string;
  requirement_description: string;
  mapped_testcases: string[];
  testcase_count: number;
  status: "Covered" | "Partially Covered" | "Missing";
}

export interface TraceabilityMatrixResponse {
  total_requirements: number;
  covered_count: number;
  partially_covered_count: number;
  missing_count: number;
  matrix: TraceabilityMatrixRow[];
}

export interface ValidationReportSummary {
  total_requirements: number;
  covered_requirements: number;
  total_testcases: number;
  passed_testcases: number;
  warning_testcases: number;
  failed_testcases_count: number;
  grade: string;
  visual_summary: string;
}

export interface ValidationReport {
  coverage: number;
  duplicates: number;
  quality_score: number;
  missing_requirements: string[];
  failed_testcases: Array<{
    id: string;
    title: string;
    status: string;
    score: number;
    errors: string[];
    warnings: string[];
  }>;
  score_breakdown: Record<string, any>;
  duplicate_details: DuplicateMatch[];
  recommendations: RecommendationsResponse;
  summary: ValidationReportSummary;
}

export interface RequirementUploadResponse {
  message: string;
  filename: string;
  count: number;
  requirements: Requirement[];
}

export interface TestCaseUploadResponse {
  message: string;
  count: number;
  testcases: TestCase[];
}

export interface GenerateTestCasesResponse {
  message: string;
  count: number;
  testcases: TestCase[];
}

export interface AutoFixSummary {
  total_processed: number;
  exact_duplicates_removed: number;
  semantic_duplicates_removed: number;
  orphans_flagged: number;
  final_count: number;
  duplicates_removed?: number;
  formatting_issues_fixed?: number;
}

export interface AutoFixResponse {
  summary: AutoFixSummary;
  cleaned_test_cases: any[];
  cleaned_testcases?: any[];
  validation_report: string[];
  message?: string;
}

export interface GeneratorResponse {
  message: string;
  count: number;
  cases_per_requirement: number;
  strategy: string;
  requirements_covered: number;
  testcases: TestCase[];
  testcases_dict?: any[];
}

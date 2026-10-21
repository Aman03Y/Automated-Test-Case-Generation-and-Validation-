import axios from "axios";
import type {
  RequirementUploadResponse,
  TestCaseUploadResponse,
  ValidationReport,
  RecommendationsResponse,
  TraceabilityMatrixResponse,
} from "../types";

// Use Vite proxy in dev when VITE_API_BASE_URL is not set.
// In dev: leave empty -> requests go to same origin and Vite proxies /api -> http://localhost:8000
// In prod (Vercel + Render): set VITE_API_BASE_URL=https://your-api.onrender.com
const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(
    /\/$/,
    "",
  ) || "";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Friendly network error interceptor — helps diagnose ERR_CONNECTION_REFUSED
apiClient.interceptors.response.use(undefined, (error) => {
  if (axios.isAxiosError(error) && !error.response) {
    // Network error = backend not running, CORS, or timeout
    const backendUrl = API_BASE_URL || "http://localhost:8000 (via Vite proxy)";
    console.error(
      `[API] Network Error — backend unreachable at ${backendUrl}. Is the backend running? Run: uv run uvicorn backend.app:app --reload --port 8000`,
    );
  }
  return Promise.reject(error);
});

export async function isBackendAlive(): Promise<boolean> {
  try {
    await apiClient.get("/", { timeout: 3000 });
    return true;
  } catch {
    try {
      await apiClient.get("/api/health", { timeout: 3000 });
      return true;
    } catch {
      return false;
    }
  }
}

export const apiService = {
  /**
   * Upload requirement document (.pdf, .docx, .txt, .json)
   */
  async uploadRequirements(file: File): Promise<RequirementUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiClient.post<RequirementUploadResponse>(
      "/api/requirements/upload",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      },
    );
    return response.data;
  },

  /**
   * Upload manual test cases JSON file
   */
  async uploadTestcases(file: File): Promise<TestCaseUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiClient.post<TestCaseUploadResponse>(
      "/api/testcases/upload",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      },
    );
    return response.data;
  },

  /**
   * Run full AI validation pipeline
   */
  async runValidation(payload?: {
    similarity_threshold?: number;
    semantic_threshold?: number;
  }): Promise<ValidationReport> {
    const response = await apiClient.post<ValidationReport>(
      "/api/validate",
      payload || {},
    );
    return response.data;
  },

  /**
   * Fetch JSON validation report
   */
  async getJsonReport(): Promise<ValidationReport> {
    const response = await apiClient.get<ValidationReport>("/api/report/json");
    return response.data;
  },

  /**
   * Download or URL link for PDF report
   */
  getPdfReportUrl(): string {
    return `${API_BASE_URL}/api/report/pdf`;
  },

  /**
   * Fetch Markdown report content
   */
  async getMarkdownReport(): Promise<string> {
    const response = await apiClient.get<string>("/api/report/markdown", {
      responseType: "text",
    });
    return response.data;
  },

  /**
   * Fetch AI recommendations payload
   */
  async getRecommendations(): Promise<RecommendationsResponse> {
    const response = await apiClient.get<RecommendationsResponse>(
      "/api/recommendations",
    );
    return response.data;
  },

  /**
   * Fetch Requirement Traceability Matrix (RTM)
   */
  async getTraceabilityMatrix(): Promise<TraceabilityMatrixResponse> {
    const response = await apiClient.get<TraceabilityMatrixResponse>(
      "/api/traceability-matrix",
    );
    return response.data;
  },

  /**
   * Generate test cases from requirements (legacy endpoint, now upgraded)
   */
  async generateTestCases(opts?: {
    cases_per_requirement?: number;
    include_negative?: boolean;
    include_boundary?: boolean;
    include_edge?: boolean;
    include_security?: boolean;
    strategy?: "comprehensive" | "minimal";
  }): Promise<import("../types").GenerateTestCasesResponse> {
    const response = await apiClient.post<
      import("../types").GenerateTestCasesResponse
    >("/api/requirements/generate-testcases", opts || {});
    return response.data;
  },

  // ── New Generator API (backend/routers/generator.py) ──
  async generatorOptions(): Promise<any> {
    const response = await apiClient.get("/api/generator/options");
    return response.data;
  },
  async generatorGenerate(payload: {
    requirements?: any[];
    cases_per_requirement?: number;
    include_negative?: boolean;
    include_boundary?: boolean;
    include_edge?: boolean;
    include_security?: boolean;
    include_performance?: boolean;
    strategy?: "comprehensive" | "minimal";
    requirement_ids?: string[];
    id_prefix?: string;
    save_to_session?: boolean;
  }): Promise<import("../types").GeneratorResponse> {
    const response = await apiClient.post<import("../types").GeneratorResponse>(
      "/api/generator/generate",
      payload,
    );
    return response.data;
  },
  async generatorUploadAndGenerate(
    file: File,
    opts?: {
      cases_per_requirement?: number;
      include_negative?: boolean;
      include_boundary?: boolean;
      include_edge?: boolean;
      include_security?: boolean;
      include_performance?: boolean;
      strategy?: string;
      id_prefix?: string;
    },
  ): Promise<import("../types").GeneratorResponse> {
    const fd = new FormData();
    fd.append("file", file);
    if (opts?.cases_per_requirement !== undefined)
      fd.append("cases_per_requirement", String(opts.cases_per_requirement));
    if (opts?.include_negative !== undefined)
      fd.append("include_negative", String(opts.include_negative));
    if (opts?.include_boundary !== undefined)
      fd.append("include_boundary", String(opts.include_boundary));
    if (opts?.include_edge !== undefined)
      fd.append("include_edge", String(opts.include_edge));
    if (opts?.include_security !== undefined)
      fd.append("include_security", String(opts.include_security));
    if (opts?.include_performance !== undefined)
      fd.append("include_performance", String(opts.include_performance));
    if (opts?.strategy) fd.append("strategy", opts.strategy);
    if (opts?.id_prefix) fd.append("id_prefix", opts.id_prefix);
    const response = await apiClient.post<import("../types").GeneratorResponse>(
      "/api/generator/upload-and-generate",
      fd,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return response.data;
  },
  async generatorPreview(
    payload: any,
  ): Promise<import("../types").GeneratorResponse> {
    const response = await apiClient.post<import("../types").GeneratorResponse>(
      "/api/generator/preview",
      payload,
    );
    return response.data;
  },

  /**
   * Validate and fix test cases
   */
  async validateAndFixTestcases(
    file: File,
  ): Promise<import("../types").AutoFixResponse> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiClient.post<import("../types").AutoFixResponse>(
      "/api/testcases/validate-tests",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return response.data;
  },
};

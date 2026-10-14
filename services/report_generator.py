"""
Enterprise Report Generator Service.

Module 7: Enterprise Report Generator
Aggregates validation results, requirement coverage, duplicates, quality metrics, and recommendations.
Generates 3 enterprise report formats:
  1. JSON Report (validation_report.json)
  2. Markdown Report (validation_report.md)
  3. Professional PDF Report (validation_report.pdf) using ReportLab
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

try:
    from reportlab.lib.pagesizes import letter  # type: ignore
    from reportlab.lib import colors  # type: ignore
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
    from reportlab.platypus import (  # type: ignore
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        KeepTogether,
        HRFlowable,
    )
    from reportlab.pdfgen import canvas  # type: ignore
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from models.requirement import Requirement
from models.testcase import TestCase
from models.report import ValidationReport, QualityBreakdown
from models.validation_result import CoverageResult, TestCaseValidationResult, DuplicateMatch, ValidationStatus
from services.recommendation_engine import RecommendationEngine
from utils.exceptions import ReportGenerationError
from utils.logger import get_logger

logger = get_logger("ReportGenerator")


class NumberedCanvas(canvas.Canvas if REPORTLAB_AVAILABLE else object):
    """Two-pass canvas for dynamic 'Page X of Y' numbering and running header/footer."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Any] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int) -> None:
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 750, "AI-BASED AUTOMATED TEST CASE VALIDATION REPORT")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Running Footer (All Pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)

        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Confidential - Automated Quality Audit System")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_text)
        self.restoreState()


class ReportGenerator:
    """Production-grade Enterprise Report Generator for JSON, Markdown, and PDF outputs."""

    def __init__(self, output_dir: Union[str, Path] = "outputs"):
        """Initializes ReportGenerator.

        Args:
            output_dir: Directory path where output reports are saved.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        testcases: List[TestCase],
        duplicate_matches: List[DuplicateMatch],
        coverage_result: CoverageResult,
        validation_results: List[TestCaseValidationResult],
        quality_breakdown: QualityBreakdown,
        requirements: Optional[List[Requirement]] = None,
        recommendations: Optional[Dict[str, Any]] = None,
        json_filename: str = "validation_report.json",
        md_filename: str = "validation_report.md",
        pdf_filename: str = "validation_report.pdf",
    ) -> ValidationReport:
        """Generates JSON, Markdown, and PDF validation reports.

        Args:
            requirements: List of parsed Requirement models.
            testcases: List of loaded TestCase models.
            duplicate_matches: List of DuplicateMatch models.
            coverage_result: CoverageResult model.
            validation_results: List of TestCaseValidationResult models.
            quality_breakdown: QualityBreakdown model.
            recommendations: Optional recommendations dictionary from RecommendationEngine.
            json_filename: Name of JSON output file.
            md_filename: Name of Markdown output file.
            pdf_filename: Name of PDF output file.

        Returns:
            ValidationReport object.
        """
        start_t = time.perf_counter()
        logger.info("Enterprise Report Generator started: Compiling validation report...")

        # Compute recommendations if not provided
        if recommendations is None:
            rec_engine = RecommendationEngine()
            recommendations = rec_engine.generate_recommendations(
                validation_results=validation_results,
                coverage_result=coverage_result,
                duplicate_matches=duplicate_matches,
                quality_breakdown=quality_breakdown,
            )

        duplicate_pairs_count = sum(1 for m in duplicate_matches if m.is_duplicate or m.duplicate)
        tc_dict = {tc.id: tc for tc in testcases}

        # Build failed testcase details list
        failed_testcases: List[Dict[str, Any]] = []
        for val_res in validation_results:
            if val_res.status == ValidationStatus.FAIL or len(val_res.errors) > 0:
                original_tc = tc_dict.get(val_res.testcase_id)
                failed_entry = {
                    "id": val_res.testcase_id,
                    "title": original_tc.title if original_tc else "",
                    "status": val_res.status.value,
                    "score": val_res.score,
                    "errors": val_res.errors,
                    "warnings": val_res.warnings,
                }
                failed_testcases.append(failed_entry)

        # Construct master report model
        report = ValidationReport(
            coverage=coverage_result.coverage_percentage,
            duplicates=duplicate_pairs_count,
            quality_score=quality_breakdown.overall_score,
            missing_requirements=coverage_result.missing_requirements,
            failed_testcases=failed_testcases,
            score_breakdown=quality_breakdown.to_dict(),
            duplicate_details=[m.to_dict() for m in duplicate_matches if m.is_duplicate or m.duplicate],
            recommendations=recommendations,
            summary={
                "total_requirements": coverage_result.total_requirements,
                "covered_requirements": coverage_result.covered_requirements_count,
                "total_testcases": len(testcases),
                "passed_testcases": sum(1 for v in validation_results if v.status == ValidationStatus.PASS),
                "warning_testcases": sum(1 for v in validation_results if v.status == ValidationStatus.WARNING),
                "failed_testcases_count": len(failed_testcases),
                "grade": quality_breakdown.grade,
                "visual_summary": quality_breakdown.visual_summary,
            },
        )

        # 1. Export JSON Report
        json_path = self.output_dir / json_filename
        self.generate_json_report(report, json_path)

        # 2. Export Markdown Report
        md_path = self.output_dir / md_filename
        self.generate_markdown_report(report, md_path)

        # 3. Export PDF Report
        pdf_path = self.output_dir / pdf_filename
        self.generate_pdf_report(report, pdf_path)

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        logger.info(f"Report Generation completed successfully in {elapsed_ms:.2f} ms.")

        return report

    def generate_json_report(self, report: ValidationReport, json_path: Path) -> None:
        """Saves ValidationReport to formatted JSON file."""
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, indent=4)
            logger.info(f"Generated JSON validation report at: {json_path.resolve()}")
        except Exception as e:
            logger.exception(f"Failed to generate JSON report: {e}")
            raise ReportGenerationError(f"Error saving JSON report to {json_path}", details=str(e))

    def generate_markdown_report(self, report: ValidationReport, md_path: Path) -> None:
        """Generates comprehensive Markdown validation report."""
        try:
            lines = [
                "# AI Automated Test Case Validation Report",
                "",
                "## Executive Summary",
                f"- **Overall Quality Score**: `{report.quality_score:.1f} / 100` (`{report.summary.get('grade', 'N/A')}` - **{report.summary.get('visual_summary', 'N/A')}**)",
                f"- **Requirement Coverage**: `{report.coverage:.1f}%` ({report.summary.get('covered_requirements', 0)}/{report.summary.get('total_requirements', 0)} Covered)",
                f"- **Duplicate Test Case Pairs**: `{report.duplicates}`",
                f"- **Total Test Cases Evaluated**: `{report.summary.get('total_testcases', 0)}`",
                f"- **Validation Rule Outcomes**: `PASS: {report.summary.get('passed_testcases', 0)}` | "
                f"`WARNING: {report.summary.get('warning_testcases', 0)}` | "
                f"`FAIL: {report.summary.get('failed_testcases_count', 0)}`",
                "",
                "## Weighted Quality Score Breakdown",
                f"- **Requirement Coverage (35%)**: `{report.score_breakdown.get('score_breakdown', {}).get('coverage', 0.0)} / 35`",
                f"- **Average Quality Score (35%)**: `{report.score_breakdown.get('score_breakdown', {}).get('average_quality', 0.0)} / 35`",
                f"- **Duplicate Penalty (20%)**: `{report.score_breakdown.get('score_breakdown', {}).get('duplicate_penalty', 0.0)} / 20`",
                f"- **Formatting Quality (10%)**: `{report.score_breakdown.get('score_breakdown', {}).get('formatting', 0.0)} / 10`",
                "",
                "## Missing Requirements",
            ]

            if report.missing_requirements:
                for req in report.missing_requirements:
                    lines.append(f"- ⚠️ **{req}**: Requirement is not covered by any test case.")
            else:
                lines.append(" - ✅ All requirements are covered by at least one test case.")

            # RTM Section
            rtm_md_file = self.output_dir / "traceability_matrix.md"
            if rtm_md_file.exists():
                lines.extend(["", "## Requirement Traceability Matrix (RTM)"])
                try:
                    rtm_content = rtm_md_file.read_text(encoding="utf-8")
                    # Extract table portion
                    table_lines = [l for l in rtm_content.splitlines() if l.startswith("|") or l.startswith("- **")]
                    lines.extend(table_lines)
                except Exception as e:
                    logger.warning(f"Could not append RTM content to Markdown report: {e}")

            # Recommendations Section
            lines.extend(["", "## Actionable Recommendations"])
            recs = report.recommendations
            proj_recs = recs.get("project_recommendations", [])
            uncovered_recs = recs.get("uncovered_requirement_recommendations", [])
            tc_recs = recs.get("testcase_recommendations", [])

            if proj_recs:
                lines.append("### Project-Level Guidelines")
                for pr in proj_recs:
                    lines.append(f"- 📌 {pr}")

            if uncovered_recs:
                lines.append("### Missing Requirement Actions")
                for ur in uncovered_recs:
                    lines.append(f"- 🎯 {ur}")

            if tc_recs:
                lines.append("### Specific Test Case Recommendations")
                for tr in tc_recs:
                    lines.append(f"#### `{tr['testcase_id']}` (Priority: **{tr.get('priority', 'Medium')}**)")
                    for rec_item in tr.get("recommendations", []):
                        lines.append(f"  - 💡 {rec_item}")
            elif not proj_recs and not uncovered_recs:
                lines.append(" - ✅ No action items needed! Test suite quality is excellent.")

            # Failed / Defective Test Cases
            lines.extend(["", "## Failed / Defective Test Cases"])
            if report.failed_testcases:
                for ftc in report.failed_testcases:
                    lines.append(f"### {ftc['id']}: {ftc.get('title', '')}")
                    lines.append(f"- **Status**: `{ftc['status']}` | **Score**: `{ftc.get('score', 0)} / 100`")
                    for err in ftc.get("errors", []):
                        lines.append(f"  - ❌ {err}")
                    for warn in ftc.get("warnings", []):
                        lines.append(f"  - ⚠️ {warn}")
            else:
                lines.append(" - ✅ Zero test cases failed validation rules.")

            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            logger.info(f"Generated Markdown validation report at: {md_path.resolve()}")
        except Exception as e:
            logger.exception(f"Failed to generate Markdown report: {e}")
            raise ReportGenerationError(f"Error saving Markdown report to {md_path}", details=str(e))

    def generate_pdf_report(self, report: ValidationReport, pdf_path: Path) -> None:
        """Generates enterprise-grade PDF report with ReportLab."""
        if not REPORTLAB_AVAILABLE:
            logger.warning("ReportLab library not installed. Skipping PDF generation.")
            return

        try:
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                leftMargin=54,
                rightMargin=54,
                topMargin=54,
                bottomMargin=54,
            )

            styles = getSampleStyleSheet()

            # Custom Paragraph Styles
            title_style = ParagraphStyle(
                "DocTitle",
                parent=styles["Title"],
                fontName="Helvetica-Bold",
                fontSize=22,
                leading=26,
                textColor=colors.HexColor("#0F172A"),
                alignment=0,
                spaceAfter=6,
            )
            subtitle_style = ParagraphStyle(
                "DocSubTitle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=11,
                leading=14,
                textColor=colors.HexColor("#64748B"),
                spaceAfter=15,
            )
            heading_style = ParagraphStyle(
                "SectionHeading",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=18,
                textColor=colors.HexColor("#1E293B"),
                spaceBefore=14,
                spaceAfter=8,
                keepWithNext=True,
            )
            body_style = ParagraphStyle(
                "BodyDark",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#334155"),
            )
            bold_body_style = ParagraphStyle(
                "BodyDarkBold",
                parent=body_style,
                fontName="Helvetica-Bold",
            )

            story: List[Any] = []

            # 1. Header Banner
            story.append(Paragraph("AI-Based Automated Test Case Validation Report", title_style))
            story.append(
                Paragraph(
                    "Enterprise Quality Audit & Actionable Recommendation Analysis", subtitle_style
                )
            )
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceAfter=12))

            # 2. Executive Metrics Summary Table Cards
            grade_text = f"{report.summary.get('grade', 'Grade B')} ({report.summary.get('visual_summary', 'Good')})"
            metrics_data = [
                [
                    Paragraph("<b>Overall Quality Score</b>", body_style),
                    Paragraph(f"<font color='#2563EB'><b>{report.quality_score:.1f} / 100</b></font>", bold_body_style),
                    Paragraph("<b>Grade Rating</b>", body_style),
                    Paragraph(f"<b>{grade_text}</b>", bold_body_style),
                ],
                [
                    Paragraph("<b>Requirement Coverage</b>", body_style),
                    Paragraph(f"<b>{report.coverage:.1f}%</b>", body_style),
                    Paragraph("<b>Duplicate Pairs</b>", body_style),
                    Paragraph(f"<b>{report.duplicates}</b>", body_style),
                ],
                [
                    Paragraph("<b>Evaluated Test Cases</b>", body_style),
                    Paragraph(f"<b>{report.summary.get('total_testcases', 0)}</b>", body_style),
                    Paragraph("<b>Rule Breakdown</b>", body_style),
                    Paragraph(
                        f"PASS: {report.summary.get('passed_testcases', 0)} | WARN: {report.summary.get('warning_testcases', 0)} | FAIL: {report.summary.get('failed_testcases_count', 0)}",
                        body_style,
                    ),
                ],
            ]

            summary_table = Table(metrics_data, colWidths=[1.8 * 72, 1.6 * 72, 1.5 * 72, 2.1 * 72])
            summary_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(summary_table)
            story.append(Spacer(1, 14))

            # 3. Quality Score Component Breakdown Table
            story.append(Paragraph("Weighted Quality Score Breakdown", heading_style))
            sb = report.score_breakdown.get("score_breakdown", {})
            score_table_data = [
                [
                    Paragraph("<b>Scoring Metric</b>", bold_body_style),
                    Paragraph("<b>Target Weight</b>", bold_body_style),
                    Paragraph("<b>Achieved Score</b>", bold_body_style),
                ],
                [
                    Paragraph("Requirement Coverage", body_style),
                    Paragraph("35%", body_style),
                    Paragraph(f"{sb.get('coverage', 0.0):.1f} / 35.0", body_style),
                ],
                [
                    Paragraph("Average Test Case Quality Score", body_style),
                    Paragraph("35%", body_style),
                    Paragraph(f"{sb.get('average_quality', 0.0):.1f} / 35.0", body_style),
                ],
                [
                    Paragraph("Duplicate Test Case Penalty", body_style),
                    Paragraph("20%", body_style),
                    Paragraph(f"{sb.get('duplicate_penalty', 0.0):.1f} / 20.0", body_style),
                ],
                [
                    Paragraph("Formatting & Completeness", body_style),
                    Paragraph("10%", body_style),
                    Paragraph(f"{sb.get('formatting', 0.0):.1f} / 10.0", body_style),
                ],
            ]

            score_table = Table(score_table_data, colWidths=[3.2 * 72, 1.8 * 72, 2.0 * 72])
            score_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(score_table)
            story.append(Spacer(1, 14))

            # 4. Actionable AI Recommendations Table
            story.append(Paragraph("Actionable Recommendations", heading_style))
            recs = report.recommendations
            proj_recs = recs.get("project_recommendations", [])
            uncovered_recs = recs.get("uncovered_requirement_recommendations", [])
            tc_recs = recs.get("testcase_recommendations", [])

            rec_table_data = [
                [
                    Paragraph("<b>Target Scope / ID</b>", bold_body_style),
                    Paragraph("<b>Priority</b>", bold_body_style),
                    Paragraph("<b>Actionable Guidance</b>", bold_body_style),
                ]
            ]

            for pr in proj_recs:
                rec_table_data.append(
                    [
                        Paragraph("Project Guideline", body_style),
                        Paragraph("<font color='#2563EB'>Medium</font>", bold_body_style),
                        Paragraph(pr, body_style),
                    ]
                )

            for ur in uncovered_recs:
                rec_table_data.append(
                    [
                        Paragraph("Missing Requirement", body_style),
                        Paragraph("<font color='#EF4444'>High</font>", bold_body_style),
                        Paragraph(ur, body_style),
                    ]
                )

            for tr in tc_recs:
                p_str = tr.get("priority", "Medium")
                color_hex = "#EF4444" if p_str in ["Critical", "High"] else "#F59E0B"
                rec_text = "<br/>".join(f"• {item}" for item in tr.get("recommendations", []))
                rec_table_data.append(
                    [
                        Paragraph(f"Test Case: <b>{tr['testcase_id']}</b>", body_style),
                        Paragraph(f"<font color='{color_hex}'>{p_str}</font>", bold_body_style),
                        Paragraph(rec_text, body_style),
                    ]
                )

            if len(rec_table_data) > 1:
                rec_table = Table(rec_table_data, colWidths=[1.8 * 72, 1.2 * 72, 4.0 * 72])
                rec_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ]
                    )
                )
                story.append(rec_table)
            else:
                story.append(
                    Paragraph(
                        "<b>✅ Zero high-priority action items. All test cases met quality compliance rules!</b>",
                        body_style,
                    )
                )

            story.append(Spacer(1, 14))

            # 5. Failed / Defective Test Cases Section
            story.append(Paragraph("Failed / Defective Test Cases", heading_style))
            if report.failed_testcases:
                fail_table_data = [
                    [
                        Paragraph("<b>Test Case ID</b>", bold_body_style),
                        Paragraph("<b>Title</b>", bold_body_style),
                        Paragraph("<b>Rule Violations & Error Messages</b>", bold_body_style),
                    ]
                ]
                for ftc in report.failed_testcases:
                    err_text = "<br/>".join(f"❌ {err}" for err in ftc.get("errors", []))
                    if ftc.get("warnings"):
                        err_text += "<br/>" + "<br/>".join(f"⚠️ {w}" for w in ftc.get("warnings", []))

                    fail_table_data.append(
                        [
                            Paragraph(f"<b>{ftc['id']}</b>", bold_body_style),
                            Paragraph(ftc.get("title", ""), body_style),
                            Paragraph(err_text, body_style),
                        ]
                    )

                fail_table = Table(fail_table_data, colWidths=[1.2 * 72, 2.0 * 72, 3.8 * 72])
                fail_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEE2E2")),
                            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FCA5A5")),
                            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FECACA")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ]
                    )
                )
                story.append(fail_table)
            else:
                story.append(
                    Paragraph(
                        "<b>✅ Zero test cases failed validation rules!</b>",
                        body_style,
                    )
                )

            # Build document using NumberedCanvas
            doc.build(story, canvasmaker=NumberedCanvas)
            logger.info(f"Successfully generated PDF validation report at: {pdf_path.resolve()}")

        except Exception as e:
            logger.exception(f"Failed to generate PDF report: {e}")
            raise ReportGenerationError(f"Error generating PDF report at {pdf_path}", details=str(e))

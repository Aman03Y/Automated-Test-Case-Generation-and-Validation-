import { jsPDF } from 'jspdf';
import type { AutoFixResponse } from '../types';

/**
 * Generates an enterprise-grade, multi-page vector PDF validation report
 * containing summary metrics, ALL error & auto-fix logs, and full test cases.
 */
export function generatePdfReport(result: AutoFixResponse, filename = 'AI_Validation_Full_Report.pdf'): void {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 14;
  const contentWidth = pageWidth - margin * 2;
  let currentY = margin;

  const qualityScore = Math.max(
    0,
    Math.round(100 - (result.summary.orphans_flagged / Math.max(result.summary.final_count, 1)) * 100)
  );

  // Helper to check page break and draw running header
  const ensureSpace = (requiredHeight: number) => {
    if (currentY + requiredHeight > pageHeight - margin - 10) {
      doc.addPage();
      currentY = margin;
      drawRunningHeader();
    }
  };

  const drawRunningHeader = () => {
    doc.setFillColor(15, 23, 42); // slate-900
    doc.rect(margin, currentY, contentWidth, 8, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(148, 163, 184); // slate-400
    doc.text('AI VALIDATOR  |  CONTINUED AUDIT LOG', margin + 3, currentY + 5.5);
    currentY += 12;
  };

  // --------------------------------------------------------------------------
  // PAGE 1: TITLE & EXECUTIVE SUMMARY
  // --------------------------------------------------------------------------

  // Top Accent Banner
  doc.setFillColor(79, 70, 229); // Indigo 600
  doc.rect(margin, currentY, contentWidth, 3, 'F');
  currentY += 6;

  // Title & Subtitle
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(20);
  doc.setTextColor(15, 23, 42); // Slate 900
  doc.text('AI TEST CASE VALIDATION REPORT', margin, currentY + 6);
  currentY += 10;

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(100, 116, 139); // Slate 500
  const dateStr = new Date().toLocaleString();
  doc.text(`Autonomous QA Engine  •  Generated on: ${dateStr}`, margin, currentY + 3);
  currentY += 10;

  // Executive KPI Grid (4 Cards across)
  const cardWidth = (contentWidth - 6) / 3;
  const cardHeight = 18;

  // KPI 1: Quality Score
  doc.setFillColor(248, 250, 252); // slate-50
  doc.setDrawColor(226, 232, 240); // slate-200
  doc.roundedRect(margin, currentY, cardWidth, cardHeight, 2, 2, 'FD');
  doc.setFontSize(7.5);
  doc.setTextColor(100, 116, 139);
  doc.setFont('helvetica', 'bold');
  doc.text('QUALITY SCORE', margin + 4, currentY + 6);
  doc.setFontSize(14);
  if (qualityScore >= 80) doc.setTextColor(16, 185, 129); // emerald
  else if (qualityScore >= 50) doc.setTextColor(245, 158, 11); // amber
  else doc.setTextColor(239, 68, 68); // rose
  doc.text(`${qualityScore} / 100`, margin + 4, currentY + 14);

  // KPI 2: Total Processed
  const kpi2X = margin + cardWidth + 3;
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(kpi2X, currentY, cardWidth, cardHeight, 2, 2, 'FD');
  doc.setFontSize(7.5);
  doc.setTextColor(100, 116, 139);
  doc.text('TOTAL PROCESSED', kpi2X + 4, currentY + 6);
  doc.setFontSize(14);
  doc.setTextColor(15, 23, 42);
  doc.text(`${result.summary.total_processed}`, kpi2X + 4, currentY + 14);

  // KPI 3: Final Cleaned
  const kpi3X = kpi2X + cardWidth + 3;
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(kpi3X, currentY, cardWidth, cardHeight, 2, 2, 'FD');
  doc.setFontSize(7.5);
  doc.setTextColor(100, 116, 139);
  doc.text('FINAL CLEANED SUITE', kpi3X + 4, currentY + 6);
  doc.setFontSize(14);
  doc.setTextColor(79, 70, 229);
  doc.text(`${result.summary.final_count}`, kpi3X + 4, currentY + 14);

  currentY += cardHeight + 4;

  // KPI Row 2: Defects Identified
  // Exact Dups
  doc.setFillColor(254, 242, 242); // rose-50
  doc.setDrawColor(254, 202, 202);
  doc.roundedRect(margin, currentY, cardWidth, cardHeight, 2, 2, 'FD');
  doc.setFontSize(7.5);
  doc.setTextColor(225, 29, 72);
  doc.text('EXACT DUPLICATES REMOVED', margin + 4, currentY + 6);
  doc.setFontSize(14);
  doc.text(`${result.summary.exact_duplicates_removed}`, margin + 4, currentY + 14);

  // Semantic Merges
  doc.setFillColor(254, 243, 199); // amber-50
  doc.setDrawColor(253, 230, 138);
  doc.roundedRect(kpi2X, currentY, cardWidth, cardHeight, 2, 2, 'FD');
  doc.setFontSize(7.5);
  doc.setTextColor(217, 119, 6);
  doc.text('SEMANTIC CLONES MERGED', kpi2X + 4, currentY + 6);
  doc.setFontSize(14);
  doc.text(`${result.summary.semantic_duplicates_removed}`, kpi2X + 4, currentY + 14);

  // Orphans Flagged
  doc.setFillColor(255, 247, 237); // orange-50
  doc.setDrawColor(254, 215, 170);
  doc.roundedRect(kpi3X, currentY, cardWidth, cardHeight, 2, 2, 'FD');
  doc.setFontSize(7.5);
  doc.setTextColor(194, 65, 12);
  doc.text('ORPHANS (NO REQUIREMENT)', kpi3X + 4, currentY + 6);
  doc.setFontSize(14);
  doc.text(`${result.summary.orphans_flagged}`, kpi3X + 4, currentY + 14);

  currentY += cardHeight + 8;

  // --------------------------------------------------------------------------
  // SECTION 2: COMPLETE AUDIT LOG & ERRORS
  // --------------------------------------------------------------------------

  ensureSpace(16);
  doc.setFillColor(15, 23, 42); // slate-900
  doc.rect(margin, currentY, contentWidth, 7, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(255, 255, 255);
  doc.text(
    `DETAILED AUDIT LOGS & DETECTED ERRORS (${result.validation_report.length} ENTRIES)`,
    margin + 4,
    currentY + 5
  );
  currentY += 10;

  if (result.validation_report.length === 0) {
    doc.setFont('helvetica', 'italic');
    doc.setFontSize(9);
    doc.setTextColor(100, 116, 139);
    doc.text('No errors or duplicate entries detected. Dataset is fully sanitized.', margin + 2, currentY + 4);
    currentY += 8;
  } else {
    // Print EVERY SINGLE error log with word wrapping and multi-page continuation
    result.validation_report.forEach((log) => {
      const isExact = log.includes('[EXACT_DUPLICATE]');
      const isSemantic = log.includes('[SEMANTIC_MERGE]');
      const isOrphan = log.includes('[ORPHAN_FLAG]');
      const isCleaned = log.includes('[CLEANED]');

      const lines = doc.splitTextToSize(log, contentWidth - 8);
      const entryHeight = Math.max(lines.length * 4.2 + 3, 7);

      ensureSpace(entryHeight);

      // Light background highlight per type
      if (isExact) {
        doc.setFillColor(254, 242, 242); // rose-50
        doc.setDrawColor(254, 202, 202);
      } else if (isSemantic) {
        doc.setFillColor(254, 243, 199); // amber-50
        doc.setDrawColor(253, 230, 138);
      } else if (isOrphan) {
        doc.setFillColor(255, 247, 237); // orange-50
        doc.setDrawColor(254, 215, 170);
      } else if (isCleaned) {
        doc.setFillColor(240, 253, 244); // emerald-50
        doc.setDrawColor(187, 247, 208);
      } else {
        doc.setFillColor(248, 250, 252);
        doc.setDrawColor(226, 232, 240);
      }

      doc.roundedRect(margin, currentY, contentWidth, entryHeight, 1, 1, 'FD');

      doc.setFont('courier', 'normal');
      doc.setFontSize(7.5);
      if (isExact) doc.setTextColor(190, 18, 60);
      else if (isSemantic) doc.setTextColor(180, 83, 9);
      else if (isOrphan) doc.setTextColor(194, 65, 12);
      else if (isCleaned) doc.setTextColor(21, 128, 61);
      else doc.setTextColor(51, 65, 85);

      lines.forEach((lineText: string, idx: number) => {
        doc.text(lineText, margin + 3, currentY + 4 + idx * 4);
      });

      currentY += entryHeight + 2;
    });
  }

  currentY += 4;

  // --------------------------------------------------------------------------
  // SECTION 3: SANITIZED TEST CASE INVENTORY (ALL CASES)
  // --------------------------------------------------------------------------

  ensureSpace(20);
  doc.setFillColor(15, 23, 42); // slate-900
  doc.rect(margin, currentY, contentWidth, 7, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(255, 255, 255);
  doc.text(
    `SANITIZED TEST CASE INVENTORY (${result.cleaned_test_cases.length} TOTAL)`,
    margin + 4,
    currentY + 5
  );
  currentY += 10;

  // Table Headers
  const colX = {
    id: margin + 2,
    priority: margin + 32,
    title: margin + 60,
    reqs: margin + 140,
  };

  const drawTableHeader = () => {
    doc.setFillColor(241, 245, 249); // slate-100
    doc.rect(margin, currentY, contentWidth, 6, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7.5);
    doc.setTextColor(71, 85, 105);
    doc.text('TEST CASE ID', colX.id, currentY + 4.2);
    doc.text('PRIORITY', colX.priority, currentY + 4.2);
    doc.text('TITLE / SCENARIO', colX.title, currentY + 4.2);
    doc.text('REQUIREMENT MAPPING', colX.reqs, currentY + 4.2);
    currentY += 8;
  };

  drawTableHeader();

  // Print all test cases
  result.cleaned_test_cases.forEach((tc, index) => {
    const titleLines = doc.splitTextToSize(tc.title || 'Untitled', 75);
    const reqsText = (tc.requirement_ids && tc.requirement_ids.length > 0)
      ? tc.requirement_ids.join(', ')
      : 'NONE';
    const reqLines = doc.splitTextToSize(reqsText, 38);

    const rowHeight = Math.max(titleLines.length * 3.8, reqLines.length * 3.8, 6.5) + 2;

    ensureSpace(rowHeight);

    // Alternate row zebra tint
    if (index % 2 === 1) {
      doc.setFillColor(248, 250, 252);
      doc.rect(margin, currentY - 1, contentWidth, rowHeight, 'F');
    }

    // ID
    doc.setFont('courier', 'bold');
    doc.setFontSize(7.5);
    doc.setTextColor(30, 41, 59);
    doc.text(tc.id || `TC-${index + 1}`, colX.id, currentY + 3.5);

    // Priority
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7);
    const p = (tc.priority || 'medium').toLowerCase();
    if (p === 'critical' || p === 'high') doc.setTextColor(225, 29, 72);
    else if (p === 'medium') doc.setTextColor(79, 70, 229);
    else doc.setTextColor(100, 116, 139);
    doc.text((tc.priority || 'MEDIUM').toUpperCase(), colX.priority, currentY + 3.5);

    // Title
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(51, 65, 85);
    titleLines.forEach((tLine: string, tIdx: number) => {
      doc.text(tLine, colX.title, currentY + 3.5 + tIdx * 3.8);
    });

    // Reqs
    const hasOrphan = reqsText.includes('ORPHAN') || reqsText === 'NONE';
    if (hasOrphan) {
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(225, 29, 72);
    } else {
      doc.setFont('courier', 'normal');
      doc.setTextColor(71, 85, 105);
    }
    doc.setFontSize(7);
    reqLines.forEach((rLine: string, rIdx: number) => {
      doc.text(rLine, colX.reqs, currentY + 3.5 + rIdx * 3.8);
    });

    currentY += rowHeight;
  });

  // --------------------------------------------------------------------------
  // FOOTER NUMBERING ACROSS ALL PAGES
  // --------------------------------------------------------------------------
  const totalPages = (doc.internal as any).getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(148, 163, 184); // slate-400
    doc.text(
      `AI Validator Engine  •  Confidential Test Automation Report  •  Page ${i} of ${totalPages}`,
      pageWidth / 2,
      pageHeight - 6,
      { align: 'center' }
    );
  }

  // Save the PDF
  doc.save(filename);
}

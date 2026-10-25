// Render Manuscript Blocks Revision.json to Word. Usage: node "build manuscript revision.js" <output.docx> [anonymised]
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  BorderStyle, ShadingType, Footer, PageNumber, HeadingLevel, PageBreak, TableLayoutType,
} = require("docx");

const out = process.argv[2];
const anon = process.argv[3] === "anonymised";
const B = JSON.parse(fs.readFileSync(path.join(__dirname, "Manuscript Blocks Revision.json"), "utf8"));
if (anon) {
  // blind the author's own work: in-text citations and the reference entry
  B.body.forEach((b) => { if (typeof b.value === "string") b.value = b.value.replace(/Enang, 2026/g, "Author, 2026"); });
  B.references = B.references.map((r) => (r.startsWith("Enang, I.") ? "Author (2026), details removed for anonymised review." : r));
}
const FONT = "Calibri Light";
const BODY = 20; // half-points: 10 pt
const PAGE_W = 11906, MARGIN = 1247; // A4, 2.2 cm margins
const TEXT_W = PAGE_W - 2 * MARGIN;

const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: o.size || BODY, bold: o.bold, italics: o.italics, color: o.color });
const para = (t, o = {}) => new Paragraph({
  children: Array.isArray(t) ? t : [run(t, o)], alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after ?? 120, before: o.before ?? 0, line: o.line || 276 }, keepNext: o.keepNext, heading: o.heading,
});
const heading = (t) => new Paragraph({
  children: [run(t, { bold: true, size: 24, color: "1F2A44" })], heading: HeadingLevel.HEADING_1,
  spacing: { before: 240, after: 120 }, keepNext: true,
});
const thin = { style: BorderStyle.SINGLE, size: 4, color: "9AA0A8" };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };

function table(T) {
  const total = T.widths.reduce((a, b) => a + b, 0);
  const widths = T.widths.map((w) => Math.round((w / total) * TEXT_W));
  const fix = TEXT_W - widths.reduce((a, b) => a + b, 0);
  widths[0] += fix;
  const mkCell = (txt, i, hdr, bold) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: hdr ? { type: ShadingType.CLEAR, color: "auto", fill: "E8EBF0" } : undefined,
    borders: { top: hdr ? thin : none, bottom: thin, left: none, right: none },
    margins: { top: 40, bottom: 40, left: 70, right: 70 },
    children: [new Paragraph({
      alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, spacing: { after: 0, line: 240 },
      children: [run(String(txt), { size: 16, bold: hdr || bold })],
    })],
  });
  const rows = [new TableRow({ tableHeader: true, children: T.header.map((h, i) => mkCell(h, i, true)) })];
  T.rows.forEach((r, k) => rows.push(new TableRow({
    cantSplit: true, children: r.map((c, i) => mkCell(c, i, false, (T.bold_rows || []).includes(k))),
  })));
  return [
    para(T.caption, { bold: true, align: AlignmentType.LEFT, after: 80, keepNext: true, before: 120 }),
    new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED, rows }),
    para(T.note, { size: 16, align: AlignmentType.LEFT, after: 200, before: 60, color: "4A4F57" }),
  ];
}

function figure(F) {
  const buf = fs.readFileSync(F.file);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  const width = 600; // px at 96 dpi, about 15.9 cm
  return [
    para(F.caption, { bold: true, align: AlignmentType.LEFT, after: 80, keepNext: true, before: 120 }),
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { after: 60 },
      children: [new ImageRun({ type: "png", data: buf, transformation: { width, height: Math.round((width * h) / w) } })] }),
    para(F.note, { size: 16, align: AlignmentType.LEFT, after: 200, color: "4A4F57" }),
  ];
}

const kids = [];
kids.push(para(B.title, { bold: true, size: 32, align: AlignmentType.LEFT, after: 200, line: 300 }));
if (!anon) {
  kids.push(para("Imo J. Enang", { size: 22, align: AlignmentType.LEFT, after: 240 }));
}
kids.push(para("Structured abstract", { bold: true, size: 22, align: AlignmentType.LEFT, after: 80 }));
for (const [label, txt] of B.abstract) {
  kids.push(para([run(label + ". ", { bold: true }), run(txt)], { after: 80 }));
}
kids.push(para([run("Keywords. ", { bold: true }), run(B.keywords)], { after: 80, align: AlignmentType.LEFT }));
kids.push(para([run("Paper type. ", { bold: true }), run("Research paper")], { after: 200, align: AlignmentType.LEFT }));
kids.push(new Paragraph({ children: [new PageBreak()] }));

for (const b of B.body) {
  if (b.kind === "h1") kids.push(heading(b.value));
  else if (b.kind === "p") kids.push(para(b.value, { italics: /^H[123]\. /.test(b.value) }));
  else if (b.kind === "table") kids.push(...table(B.tables[b.value]));
  else if (b.kind === "figure") kids.push(...figure(B.figures[b.value]));
}

kids.push(heading("Declarations"));
const repo = anon ? "the author's repository (link withheld for anonymised review)"
  : "https://github.com/Imomazin/research-projects (branch revision/strategic-risk, folder Strategy and Strategic Management/Strategy and Leadership/Managing Emerging Strategic Risks; extracted filing text on branch data/strategic-risk)";
kids.push(para([run("Data availability. ", { bold: true }), run(`All data come from public sources: SEC EDGAR filings and XBRL company facts and the published Geopolitical Risk, Economic Policy Uncertainty, World Uncertainty and Global Supply Chain Pressure indices. Collection scripts, retrieval manifests with checksums, the analysis plan with its dated deviations, derived datasets, the response coding manual, validation samples with blank sheets for human coders, a reproduction report and analysis code are available at ${repo}.`)]));
kids.push(para([run("Use of generative artificial intelligence. ", { bold: true }), run("Claude (Anthropic) was used to write the data-collection and analysis code, to run the analyses, to draft the manuscript text and to assign the reference labels for the dictionary audit (Table A1) and the response validation sample (Table 3). Those labels are not independent human annotation. A zero-shot natural language inference model was used as one of the four response classifiers. Every reported number is generated by versioned code from the archived data.")]));

kids.push(heading("References"));
for (const r of B.references) {
  kids.push(new Paragraph({ children: [run(r, { size: 18 })], alignment: AlignmentType.LEFT,
    indent: { left: 360, hanging: 360 }, spacing: { after: 60, line: 252 } }));
}
kids.push(heading("Appendix"));
for (const k of B.appendix) kids.push(...table(B.tables[k]));

const doc = new Document({
  creator: anon ? "Author" : "Imo Enang", lastModifiedBy: anon ? "Author" : "Imo Enang", title: B.title, description: "Manuscript for Strategy & Leadership",
  styles: { default: { document: { run: { font: FONT, size: BODY } } } },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: 1247, bottom: 1247, left: MARGIN, right: MARGIN } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16 })] })] }) },
    children: kids,
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("written", out); });

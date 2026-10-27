// Build the Word manuscript from Manuscript Source.json (blocks) using docx-js.
// Usage: node "Build Manuscript.js" "Manuscript Source.json" "output.docx"
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, ImageRun, BorderStyle, Footer, PageNumber, TableLayoutType, VerticalAlign,
} = require("docx");

const src = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const base = path.dirname(path.resolve(process.argv[2]));
const FONT = "Calibri Light";
const BODY = 20; // half-points: 10 pt
const SMALL = 16; // 8 pt for tables
const PAGE_W = 11906, MARGIN = 1134; // A4, 2 cm margins
const TEXT_W = PAGE_W - 2 * MARGIN;

function runs(text, size = BODY, extra = {}) {
  // **bold**, *italic*, ^superscript^, ~subscript~
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|\^[^^]+\^|~[^~]+~)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, size, ...extra }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, font: FONT, size, ...extra }));
    else if (t.startsWith("*")) out.push(new TextRun({ text: t.slice(1, -1), italics: true, font: FONT, size, ...extra }));
    else if (t.startsWith("^")) out.push(new TextRun({ text: t.slice(1, -1), superScript: true, font: FONT, size, ...extra }));
    else out.push(new TextRun({ text: t.slice(1, -1), subScript: true, font: FONT, size, ...extra }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, size, ...extra }));
  return out;
}

const thin = { style: BorderStyle.SINGLE, size: 4, color: "8C8C8C" };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };

function table(block) {
  const ncol = block.header.length;
  const weights = block.widths || Array(ncol).fill(1);
  const total = weights.reduce((a, b) => a + b, 0);
  const widths = weights.map((w) => Math.floor((TEXT_W * w) / total));
  widths[widths.length - 1] += TEXT_W - widths.reduce((a, b) => a + b, 0);
  const mk = (cells, header) => new TableRow({
    tableHeader: header,
    children: cells.map((c, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      verticalAlign: VerticalAlign.CENTER,
      shading: header ? { type: ShadingType.CLEAR, color: "auto", fill: "EEF2F6" } : undefined,
      margins: { top: 40, bottom: 40, left: 70, right: 70 },
      borders: { top: header ? thin : none, bottom: thin, left: none, right: none },
      children: [new Paragraph({ spacing: { before: 0, after: 0 },
        alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.LEFT,
        children: runs(String(c), SMALL, header ? { bold: true } : {}) })],
    })),
  });
  return new Table({
    width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED,
    rows: [mk(block.header, true), ...block.rows.map((r) => mk(r, false))],
  });
}

const children = [];
for (const b of src.blocks) {
  if (b.type === "title") {
    children.push(new Paragraph({ spacing: { after: 160 }, children: runs(b.text, 32, { bold: true }) }));
  } else if (b.type === "meta") {
    children.push(new Paragraph({ spacing: { after: 60 }, children: runs(b.text, 18) }));
  } else if (b.type === "h1") {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 240, after: 100 },
      children: runs(b.text, 24, { bold: true, color: "1F2A44" }) }));
  } else if (b.type === "h2") {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 160, after: 80 },
      children: runs(b.text, 21, { bold: true, color: "1F2A44" }) }));
  } else if (b.type === "p") {
    children.push(new Paragraph({ spacing: { after: 100, line: 264 }, alignment: AlignmentType.JUSTIFIED,
      children: runs(b.text) }));
  } else if (b.type === "eq") {
    children.push(new Paragraph({ spacing: { before: 60, after: 60 }, alignment: AlignmentType.CENTER,
      children: runs(b.text, BODY, { font: "Cambria Math" }) }));
  } else if (b.type === "code") {
    for (const line of b.lines) {
      children.push(new Paragraph({ spacing: { after: 0 }, indent: { left: 360 },
        children: [new TextRun({ text: line, font: "Consolas", size: 16 })] }));
    }
    children.push(new Paragraph({ spacing: { after: 100 }, children: [] }));
  } else if (b.type === "caption") {
    children.push(new Paragraph({ spacing: { before: 60, after: 120 }, keepNext: b.keepNext || false,
      children: runs(b.text, 18) }));
  } else if (b.type === "table") {
    if (b.caption) children.push(new Paragraph({ spacing: { before: 120, after: 60 }, keepNext: true, children: runs(b.caption, 18) }));
    children.push(table(b));
    if (b.note) children.push(new Paragraph({ spacing: { before: 40, after: 140 }, children: runs(b.note, 16) }));
    else children.push(new Paragraph({ spacing: { after: 100 }, children: [] }));
  } else if (b.type === "figure") {
    const file = path.resolve(base, b.path);
    const data = fs.readFileSync(file);
    const w = data.readUInt32BE(16), h = data.readUInt32BE(20);
    const maxW = b.width_px || 620;
    const scale = maxW / w;
    children.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120 },
      children: [new ImageRun({ type: "png", data, transformation: { width: Math.round(w * scale), height: Math.round(h * scale) },
        altText: { title: b.alt || "Figure", description: b.alt || "Figure", name: b.alt || "Figure" } })] }));
    children.push(new Paragraph({ spacing: { before: 60, after: 160 }, children: runs(b.caption, 18) }));
  } else if (b.type === "refs") {
    b.items.forEach((r, i) => children.push(new Paragraph({ spacing: { after: 40 }, indent: { left: 400, hanging: 400 },
      children: runs(`${i + 1}.\t${r}`, 17) })));
  }
}

const doc = new Document({
  creator: "Imo Enang", title: src.title, description: src.description || "",
  styles: { default: { document: { run: { font: FONT, size: BODY } } } },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16 })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(process.argv[3], buf); console.log("written", process.argv[3]); });

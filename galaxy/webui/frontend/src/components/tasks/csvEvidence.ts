import { parse } from 'csv-parse/browser/esm/sync';

const maxInputLength = 64 * 1024;
const maxExamples = 5;

export function looksLikeInlineCsv(value: unknown): value is string {
  if (typeof value !== 'string' || value.length > maxInputLength || !value.includes(',') || !/[\r\n]/.test(value)) {
    return false;
  }
  const table = readCsvTable(value);
  if ('reason' in table) return false;

  // Unlabelled numeric rows and lines of prose can both parse as CSV.
  const [header, firstRow] = table;
  const lastColumn = header.length - 1;
  const endsSentence = /[.!?。！？]\s*$/;
  return header.some(name => /\p{L}/u.test(name)) &&
    !(endsSentence.test(header[lastColumn]) && endsSentence.test(firstRow[lastColumn]));
}

type DuplicateCheck =
  | { status: 'inconclusive'; reason: string }
  | {
      status: 'checked';
      recordCount: number;
      duplicateCount: number;
      examples: { first: number; duplicate: number }[];
    };

function readCsvTable(text: string): string[][] | { status: 'inconclusive'; reason: string } {
  if (text.length > maxInputLength) {
    return { status: 'inconclusive', reason: 'CSV exceeds the 65,536-character review limit.' };
  }

  let records: string[][];
  try {
    records = parse(text, { bom: true });
  } catch {
    return { status: 'inconclusive', reason: 'Could not read the CSV. Check the quoting and column counts.' };
  }

  const headers = records[0]?.map(name => name.trim()) ?? [];
  if (headers.length < 2 || headers.includes('') || new Set(headers).size !== headers.length) {
    return { status: 'inconclusive', reason: 'Expected at least two columns with distinct, nonempty names.' };
  }
  if (records.length < 2) {
    return { status: 'inconclusive', reason: 'The CSV contains a header but no data records.' };
  }
  return records;
}

export function checkCsvDuplicates(text: string): DuplicateCheck {
  const records = readCsvTable(text);
  if ('reason' in records) return records;
  const firstRecord = new Map<string, number>();
  const examples: { first: number; duplicate: number }[] = [];
  let duplicateCount = 0;
  // Index 0 is the header. Quoted newlines do not start a new data record.
  for (let i = 1; i < records.length; i++) {
    const key = JSON.stringify(records[i]);
    const first = firstRecord.get(key);
    if (first === undefined) {
      firstRecord.set(key, i);
    } else {
      duplicateCount++;
      if (examples.length < maxExamples) examples.push({ first, duplicate: i });
    }
  }
  return { status: 'checked', recordCount: records.length - 1, duplicateCount, examples };
}

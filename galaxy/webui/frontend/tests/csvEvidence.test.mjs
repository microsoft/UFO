import assert from 'node:assert/strict';
import test from 'node:test';
import { loadModule } from './loadModule.mjs';

const { looksLikeInlineCsv, checkCsvDuplicates } = await loadModule('/src/components/tasks/csvEvidence.ts');

test('offers the check for rectangular inline tables with column names', () => {
  assert.equal(looksLikeInlineCsv('id,name\r1,Chen'), true);
  assert.equal(looksLikeInlineCsv('订单编号,客户姓名\nA1,林晓'), true);
  assert.equal(looksLikeInlineCsv('Customer name,Order number\nJane Smith,A1'), true);
  for (const value of [
    'reports/orders.csv', { path: 'orders.csv' }, null, 'id,name',
    'Results are in reports/orders.csv, ready for review.\nThere were no errors.',
    'The export is ready, including the summary.\nThe original is untouched, and validation passed.',
    '1,2\n3,4',
  ]) {
    assert.equal(looksLikeInlineCsv(value), false);
  }
});

test('numbers duplicates by data record even when fields span lines', () => {
  const csv = [
    '\uFEFFid,note',
    '01,"comma, quote ""here"""',
    '02,"first line\r\nsecond line"',
    '01,"comma, quote ""here"""',
    '02,"first line\r\nsecond line"',
  ].join('\r\n');
  assert.equal(looksLikeInlineCsv(csv), true);
  assert.deepEqual(checkCsvDuplicates(csv), {
    status: 'checked',
    recordCount: 4,
    duplicateCount: 2,
    examples: [{ first: 1, duplicate: 3 }, { first: 2, duplicate: 4 }],
  });
});

test('compares every field and preserves spaces, boundaries and leading zeroes', () => {
  const csv = ['id,item', '01,a', '1,a', '1, a', '"a,b",c', 'a,"b,c"'].join('\n');
  assert.deepEqual(checkCsvDuplicates(csv), {
    status: 'checked', recordCount: 5, duplicateCount: 0, examples: [],
  });
});

test('declines malformed, empty, or ambiguous tables without reporting a partial result', () => {
  for (const csv of [
    'report.csv',
    'id\n1\n2',
    'id,amount\n',
    'id,  \n1,2',
    'id, id \n1,2',
    'id,amount\n1,2\n1,2\n3',
    'id,amount\n1,"unfinished',
    'id,amount\n1,2\n\n3,4',
    'id,amount\n1,' + 'x'.repeat(65536),
  ]) {
    assert.equal(looksLikeInlineCsv(csv), false);
    assert.equal(checkCsvDuplicates(csv).status, 'inconclusive');
  }
});

test('caps the examples but counts all repeated records', () => {
  const csv = ['id,item', ...Array(9).fill('1,apple')].join('\n');
  const result = checkCsvDuplicates(csv);
  assert.equal(result.status, 'checked');
  assert.equal(result.duplicateCount, 8);
  assert.deepEqual(result.examples, [2, 3, 4, 5, 6].map(duplicate => ({ first: 1, duplicate })));
});

import assert from 'node:assert/strict';
import test from 'node:test';
import { loadModule } from './loadModule.mjs';

const { reviewTaskResult, getTaskResultText } = await loadModule('/src/components/tasks/taskResultReview.ts');

const task = { id: 'orders', status: 'completed' };
const evaluation = {
  type: 'evaluation_result',
  level: 'session',
  request: 'Remove duplicate orders',
  complete: 'no',
  reason: 'Order A03 still occurs twice.',
  sub_scores: [
    { name: 'Duplicate order IDs removed', evaluation: 'no' },
    { name: 'Amount column retained', evaluation: 'yes' },
  ],
};
const csv = 'order_id,amount\nA03,14\nA03,14';
const round = { request: 'Remove duplicate orders', result: csv };
const wrap = result => ({ task_id: task.id, status: 'completed', result });

test('reads the evaluator record after the device session rounds', () => {
  const selected = { ...task, result: wrap([round, evaluation]) };
  const review = reviewTaskResult(selected);
  assert.equal(review.source, 'session');
  assert.equal(review.verdict, 'rework');
  assert.equal(review.reason, evaluation.reason);
  assert.deepEqual(review.checks, [
    { name: 'Duplicate order IDs removed', verdict: 'rework' },
    { name: 'Amount column retained', verdict: 'pass' },
  ]);
  assert.deepEqual(getTaskResultText(selected), [{ label: 'Round 1', text: csv }]);
});

test('preserves yes and unsure from raw session results', () => {
  for (const [complete, verdict] of [['yes', 'pass'], ['unsure', 'inconclusive']]) {
    const result = { ...evaluation, complete, reason: 'The evaluator inspected the final screen.' };
    const review = reviewTaskResult({ ...task, result: [result] });
    assert.equal(review.verdict, verdict);
    assert.equal(review.reason, result.reason);
  }
});

test('an ordinary round, a path, or a completion claim cannot impersonate the evaluator', () => {
  for (const result of [
    'orders.csv',
    evaluation,
    [{ type: 'evaluation_result', level: 'session', complete: 'yes', reason: 'Done' }],
    [{ request: round.request, result: evaluation }],
    { complete: 'yes', reason: 'Done' },
    [{ ...evaluation, level: 'round' }],
    null,
  ]) {
    const review = reviewTaskResult({ ...task, result: wrap(result), output: evaluation });
    assert.equal(review.verdict, 'inconclusive');
    assert.equal(review.source, 'none');
  }
});

test('empty or ambiguous records never produce a pass', () => {
  for (const result of [
    [{ ...evaluation, complete: 'yes', reason: ' ', sub_scores: [] }],
    [{ ...evaluation, complete: 'perhaps' }],
    [{ ...evaluation, request: null, complete: 'yes' }],
    [{ ...evaluation, request: ' ', complete: 'yes' }],
    [evaluation, { ...evaluation, complete: 'yes' }],
  ]) {
    assert.equal(reviewTaskResult({ ...task, result }).verdict, 'inconclusive');
  }
});

test('the reported device error takes precedence over the result', () => {
  const selected = {
    ...task,
    status: 'failed',
    result: { ...wrap([evaluation]), status: 'failed', error: 'Device disconnected' },
  };
  assert.equal(reviewTaskResult(selected).source, 'execution');
  assert.match(reviewTaskResult(selected).reason, /Device disconnected/);
  assert.deepEqual(getTaskResultText(selected), []);
  assert.match(reviewTaskResult({ ...task, status: 'failed', error: 'Timeout' }).reason, /Timeout/);
});

test('a different task envelope or an unfinished attempt cannot supply evidence', () => {
  for (const selected of [
    { ...task, result: { ...wrap([round, evaluation]), task_id: 'other' } },
    { ...task, status: 'running', result: wrap([round, evaluation]) },
  ]) {
    assert.equal(reviewTaskResult(selected).verdict, 'inconclusive');
    assert.deepEqual(getTaskResultText(selected), []);
  }
});

test('returns text from each round without treating reviewer notes as output', () => {
  const result = wrap([round, { ...round, result: null }, { ...round, result: 'second' }, evaluation]);
  assert.deepEqual(getTaskResultText({ ...task, result }), [
    { label: 'Round 1', text: csv },
    { label: 'Round 3', text: 'second' },
  ]);
  assert.deepEqual(getTaskResultText({ ...task, output: csv }), [{ label: 'Task output', text: csv }]);
});

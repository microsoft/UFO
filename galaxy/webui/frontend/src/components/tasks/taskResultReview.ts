import type { Task } from '../../store/galaxyStore';

type ResultTask = Pick<Task, 'id' | 'status' | 'result' | 'output' | 'error'>;
export type ReviewVerdict = 'pass' | 'rework' | 'inconclusive';

export interface TaskResultReview {
  verdict: ReviewVerdict;
  reason: string;
  checks: { name: string; verdict: ReviewVerdict }[];
  source: 'session' | 'execution' | 'none';
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function executionEnvelope(result: unknown) {
  return isRecord(result) && 'task_id' in result && 'status' in result ? result : undefined;
}

function asVerdict(value: unknown): ReviewVerdict | undefined {
  switch (value) {
    case 'yes': return 'pass';
    case 'no': return 'rework';
    case 'unsure': return 'inconclusive';
  }
}

function noEvidence(reason: string): TaskResultReview {
  return { source: 'none', verdict: 'inconclusive', reason, checks: [] };
}

export function reviewTaskResult(task: ResultTask): TaskResultReview {
  if (task.status !== 'completed' && task.status !== 'failed') {
    return noEvidence('No completed result is available for this task.');
  }
  const envelope = executionEnvelope(task.result);
  if (envelope && envelope.task_id !== task.id) {
    return noEvidence('The returned result belongs to another task.');
  }
  const error = task.error || envelope?.error;
  if (task.status === 'failed' || envelope?.status === 'failed' || error) {
    return {
      source: 'execution',
      verdict: 'rework',
      reason: typeof error === 'string' && error.trim() ? error : 'The task failed without an error message.',
      checks: [],
    };
  }
  if (envelope && envelope.status !== 'completed') {
    return noEvidence('No completed result is available for this task.');
  }

  // BaseSession appends its evaluation alongside the round results. A round's
  // own result is task output, even when it looks like an evaluation.
  const result: unknown = envelope ? envelope.result : task.result;
  const records = (Array.isArray(result) ? result : [])
    .filter(isRecord)
    .filter(record => record.type === 'evaluation_result' && record.level === 'session');
  if (!records.length) return noEvidence('No session evaluation was returned for this task.');
  if (records.length > 1) return noEvidence('This result contains more than one session evaluation.');

  const record = records[0];
  if (typeof record.request !== 'string' || !record.request.trim()) {
    return noEvidence('The session evaluation has no request.');
  }
  const verdict = asVerdict(record.complete);
  if (!verdict) return noEvidence('The session evaluation has no recognized verdict.');
  const reason = typeof record.reason === 'string' ? record.reason.trim() : '';
  const checks: TaskResultReview['checks'] = [];
  if (Array.isArray(record.sub_scores)) {
    for (const score of record.sub_scores) {
      if (!isRecord(score) || typeof score.name !== 'string' || !score.name.trim()) continue;
      const scoreVerdict = asVerdict(score.evaluation);
      if (scoreVerdict) checks.push({ name: score.name.trim(), verdict: scoreVerdict });
    }
  }
  if (!reason && !checks.length) return noEvidence('The session evaluation included no reason or checks.');
  return { source: 'session', verdict, reason, checks };
}

export function getTaskResultText(task: ResultTask): { label: string; text: string }[] {
  const envelope = executionEnvelope(task.result);
  if (
    task.status !== 'completed' || task.error ||
    (envelope && (envelope.task_id !== task.id || envelope.status !== 'completed' || envelope.error))
  ) {
    return [];
  }
  const texts: { label: string; text: string }[] = [];
  if (typeof task.output === 'string') texts.push({ label: 'Task output', text: task.output });
  const result: unknown = envelope ? envelope.result : task.result;
  if (typeof result === 'string') texts.push({ label: 'Task result', text: result });
  if (Array.isArray(result)) {
    let roundNumber = 0;
    for (const round of result) {
      if (isRecord(round) && typeof round.request === 'string' && 'result' in round) {
        roundNumber++;
        if (typeof round.result === 'string') texts.push({ label: `Round ${roundNumber}`, text: round.result });
      }
    }
  }
  return texts;
}

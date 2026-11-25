import { useMemo, useState } from 'react';
import type { Task } from '../../store/galaxyStore';
import { checkCsvDuplicates, looksLikeInlineCsv } from './csvEvidence';
import { getTaskResultText, reviewTaskResult } from './taskResultReview';

const verdictLabel = {
  pass: 'Passed',
  rework: 'Needs rework',
  inconclusive: 'Insufficient evidence',
};

const sourceLabel = {
  session: 'Session evaluation',
  execution: 'Execution result',
  none: 'Session evaluation unavailable',
};

const buttonStyle = 'rounded border border-white/20 px-2 py-1 text-xs text-slate-200 hover:bg-white/10';

export default function ResultReview({ task }: { task: Task }) {
  const review = reviewTaskResult(task);
  const csvOutputs = useMemo(
    () => getTaskResultText(task).filter(output => looksLikeInlineCsv(output.text)),
    [task],
  );
  const [outputLabel, setOutputLabel] = useState('');
  const [checked, setChecked] = useState<{ label: string; text: string; result: ReturnType<typeof checkCsvDuplicates> }>();
  const [copyStatus, setCopyStatus] = useState<{ feedback: string; copied: boolean }>();
  const output = csvOutputs.find(item => item.label === outputLabel) ?? csvOutputs[0];
  const csv = output && checked?.label === output.label && checked.text === output.text ? checked.result : undefined;
  const source = sourceLabel[review.source];
  const csvNotes: string[] = [];
  if (csv?.status === 'inconclusive') csvNotes.push(csv.reason);
  if (csv?.status === 'checked') {
    csvNotes.push(`${csv.duplicateCount} duplicate ${csv.duplicateCount === 1 ? 'record' : 'records'} in ${csv.recordCount} data records.`);
    for (const pair of csv.examples) csvNotes.push(`Record ${pair.duplicate} repeats record ${pair.first}.`);
  }

  const feedback = [
    `${task.name} (${task.constellationId} / ${task.id})`,
    task.description,
    `${source}: ${verdictLabel[review.verdict]}`,
    review.reason,
    ...review.checks.map(check => `${check.name}: ${verdictLabel[check.verdict]}`),
    ...(csvNotes.length ? [`${output.label} — duplicate CSV records`, ...csvNotes] : []),
  ].filter(Boolean).join('\n');

  async function copyFeedback() {
    try {
      await navigator.clipboard.writeText(feedback);
      setCopyStatus({ feedback, copied: true });
    } catch {
      setCopyStatus({ feedback, copied: false });
    }
  }

  return (
    <section aria-label="Task result review" className="space-y-3 text-xs leading-relaxed text-slate-200">
      <div>
        <p className="text-slate-400">{source}</p>
        <p className="font-semibold text-white">{verdictLabel[review.verdict]}</p>
        {review.reason && <p className="mt-1 whitespace-pre-wrap break-words">{review.reason}</p>}
      </div>
      {review.checks.length > 0 && (
        <ul className="list-disc space-y-1 pl-4">
          {review.checks.map((check, i) => (
            <li key={i}>{check.name} · {verdictLabel[check.verdict]}</li>
          ))}
        </ul>
      )}
      {output && (
        <div className="space-y-1.5 border-t border-white/10 pt-2">
          {csvOutputs.length > 1 ? (
            <label className="block">Returned text{' '}
              <select className="rounded bg-slate-800" value={output.label} onChange={e => setOutputLabel(e.target.value)}>
                {csvOutputs.map(item => <option key={item.label}>{item.label}</option>)}
              </select>
            </label>
          ) : <p className="text-slate-400">{output.label}</p>}
          <button type="button" className={buttonStyle} onClick={() => setChecked({ ...output, result: checkCsvDuplicates(output.text) })}>
            Check duplicate CSV records
          </button>
          <div aria-live="polite">
            {csvNotes.map(note => <p key={note}>{note}</p>)}
          </div>
        </div>
      )}
      <button type="button" onClick={copyFeedback} className={buttonStyle}>Copy feedback</button>
      <div role="status">
        {copyStatus?.feedback === feedback && (copyStatus.copied ? 'Feedback copied.' : (
          <label>Copy this feedback manually
            <textarea className="mt-1 block w-full rounded bg-slate-900 p-2" readOnly rows={4} value={feedback} onFocus={e => e.target.select()} />
          </label>
        ))}
      </div>
    </section>
  );
}

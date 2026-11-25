import assert from 'node:assert/strict';
import test from 'node:test';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { loadModule } from './loadModule.mjs';

const { default: TaskDetailPanel } = await loadModule('/src/components/tasks/TaskDetailPanel.tsx');
const { useTaskReviewPreference } = await loadModule('/src/hooks/useTaskReviewPreference.ts');

function TaskPanel({ status }) {
  const [taskReviewEnabled] = useTaskReviewPreference();
  return createElement(TaskDetailPanel, {
    taskReviewEnabled,
    task: {
      id: 'export', constellationId: 'daily-report', name: 'Export orders', status,
      dependencies: [], dependents: [], logs: [],
    },
  });
}

test('only an explicit browser opt-in shows the review button on finished tasks', (t) => {
  const localStorage = { getItem: () => null };
  const previous = Object.getOwnPropertyDescriptor(globalThis, 'window');
  Object.defineProperty(globalThis, 'window', { configurable: true, value: { localStorage } });
  t.after(() => {
    if (previous) Object.defineProperty(globalThis, 'window', previous);
    else delete globalThis.window;
  });

  const reviewButton = />Review result<\/button>/;
  const render = status => renderToStaticMarkup(createElement(TaskPanel, { status }));
  for (const stored of [null, 'false', 'invalid', 'true']) {
    localStorage.getItem = key => {
      assert.equal(key, 'galaxy.webui.taskResultReview');
      return stored;
    };
    for (const status of ['completed', 'failed']) {
      assert.equal(reviewButton.test(render(status)), stored === 'true');
    }
    for (const status of ['pending', 'running']) {
      assert.doesNotMatch(render(status), reviewButton);
    }
  }

  localStorage.getItem = () => { throw new Error('Storage unavailable'); };
  assert.doesNotMatch(render('completed'), reviewButton);
});

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from galaxy.constellation.enums import TaskStatus
from galaxy.constellation.orchestrator.orchestrator import TaskConstellationOrchestrator
from galaxy.constellation.task_constellation import TaskConstellation
from galaxy.constellation.task_star import TaskStar
from galaxy.core.types import ExecutionResult
from galaxy.webui.websocket_observer import EventSerializer


class TaskResultEventTests(IsolatedAsyncioTestCase):
    async def execute(self, result):
        task = TaskStar(task_id=result.task_id, target_device_id="windows")
        constellation = TaskConstellation()
        constellation.add_task(task)
        manager = AsyncMock()
        manager.assign_task_to_device.return_value = result
        bus = AsyncMock()
        orchestrator = TaskConstellationOrchestrator(device_manager=manager, event_bus=bus)
        await orchestrator._execute_task_with_events(task, constellation)
        serializer = EventSerializer()
        event = bus.publish_event.await_args.args[0]
        payload = json.loads(json.dumps(serializer.serialize_event(event)))
        snapshot = serializer.serialize_value(constellation)["tasks"][task.task_id]
        return payload, snapshot

    async def test_failure_reason_survives_the_next_constellation_snapshot(self):
        error = "Device disconnected"
        event, snapshot = await self.execute(ExecutionResult("export", "failed", error=error))
        self.assertEqual(event["result"]["error"], error)
        self.assertEqual(snapshot["error"], error)

    async def test_local_device_timeout_is_a_json_serializable_failure(self):
        result = ExecutionResult("export", TaskStatus.FAILED, error=TimeoutError("Device timed out"))
        event, snapshot = await self.execute(result)
        self.assertEqual(event["event_type"], "task_failed")
        self.assertEqual(event["status"], "failed")
        self.assertEqual(event["result"]["status"], "failed")
        self.assertEqual(snapshot["error"], "Device timed out")

    async def test_completed_results_keep_the_device_session_rounds(self):
        rounds = [{"request": "Export", "result": "receipt"}]
        for status in ("completed", TaskStatus.COMPLETED):
            with self.subTest(status=status):
                event, snapshot = await self.execute(ExecutionResult("export", status, result=rounds))
                self.assertEqual(event["event_type"], "task_completed")
                self.assertEqual(event["status"], "completed")
                self.assertEqual(event["result"]["result"], rounds)
                self.assertEqual(snapshot["result"], event["result"])

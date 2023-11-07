import logging
from typing import List

from simulator.entities.batch import Batch
from simulator.entities.batch_stage import BatchStage
from simulator.events import BaseEvent
from simulator.plotting import MetricsStore
from simulator.scheduler import BaseGlobalScheduler
from simulator.types import EventType

logger = logging.getLogger(__name__)


class BatchStageEndEvent(BaseEvent):
    def __init__(
        self,
        time: float,
        replica_id: int,
        stage_id: int,
        is_last_stage: bool,
        batch: Batch,
        batch_stage: BatchStage,
    ):
        super().__init__(time)

        self._replica_id = replica_id
        self._stage_id = stage_id
        self._is_last_stage = is_last_stage

        self._batch = batch
        self._batch_stage = batch_stage

    @property
    def event_type(self):
        return EventType.BATCH_STAGE_END

    def handle_event(
        self, scheduler: BaseGlobalScheduler, metrics_store: MetricsStore
    ) -> List[BaseEvent]:
        from simulator.events.batch_end_event import BatchEndEvent
        from simulator.events.batch_stage_arrival_event import BatchStageArrivalEvent
        from simulator.events.replica_stage_schedule_event import (
            ReplicaStageScheduleEvent,
        )
        scheduler.get_replica_stage_scheduler(
            self._replica_id, self._stage_id
        ).on_stage_end()

        self._batch_stage.on_stage_end(self.time)
        metrics_store.on_batch_stage_end(self.time, self._replica_id, self._stage_id)

        next_events = [
            ReplicaStageScheduleEvent(
                self.time,
                self._replica_id,
                self._stage_id,
            ),
        ]

        if self._is_last_stage:
            return next_events + [
                BatchEndEvent(self.time, self._replica_id, self._batch)
            ]

        return next_events + [
            BatchStageArrivalEvent(
                self.time,
                self._replica_id,
                self._stage_id + 1,
                self._batch,
            )
        ]

    def to_dict(self):
        return {
            "time": self.time,
            "event_type": self.event_type,
            "replica_id": self._replica_id,
            "stage_id": self._stage_id,
            "batch_id": self._batch.id,
            "batch_stage_id": self._batch_stage.id,
            "is_last_stage": self._is_last_stage,
        }

    def to_chrome_trace(self) -> dict:
        return self._batch_stage.to_chrome_trace(self.time)

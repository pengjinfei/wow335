# Scripted Event Scenario Design

## Goal

Extend mod-raidtest for normal-rule escort/story/defense encounters without hard-coding a specific dungeon. A scripted event is not a creature-death encounter: its start is an in-world interaction and its result is an instance state transition.

## Declarative contract

```ini
EventStarterEntry = <creature entry>
EventStarterRole = tank
EventStartState = <instance boss-state id expected before first interaction>
EventPhases = <state-id>:<state>,...
EventCompletionState = <instance boss-state id>
EventCompletionValue = 3
EventFailureEscortEntry = <creature entry>
EventTrackEntries = <entry>,...
```

`EventPhases` is an ordered list. Each phase is reached only after the declared instance state is observed. A phase may declare a normal gossip interaction with the configured starter. No direct AI `DoAction`, `SetBossState`, fixture, or teleport through event geometry is permitted.

## Runtime state machine

1. Position the roster at the configured ordinary preparation point.
2. Resolve the starter NPC in the active instance and verify it is gossip-capable.
3. Invoke its normal gossip-select handler for the configured role; record the menu state and interaction.
4. Await each declared instance-state transition. At a phase boundary, require the NPC to be gossip-capable again before the next normal gossip-select.
5. During the active event, sample declared escort NPC health/state and dynamically observed hostile sources (entry, spawnId, summoner).
6. Complete only when `EventCompletionState == EventCompletionValue`; fail on escort death, all-player death, state rollback, or timeout.

## Evidence rules

- Event completion is distinct from boss death; it never uses the ordinary `BossDeathSeen` condition.
- All interactions and observed state transitions are persisted as `state` events.
- A first run is an event-lifecycle smoke test, not a stability or full-dungeon result.
- Configured tracked entries are observation-only. They neither despawn nor alter targeting/AI.

## First consumer: Tribunal of Ages

- starter: Brann Bronzebeard (28070)
- phase 1: normal gossip starts escort; await `BRANN_BRONZEBEARD == DONE`
- phase 2: normal gossip starts defense; await `BOSS_TRIBUNAL_OF_AGES == DONE`
- failure escort: Brann (28070)
- tracked dynamic sources: captured from first run before any completeness claim.

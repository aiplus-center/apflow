# Task Orchestration Architecture

## The Dual Model: Structure Tree + Execution DAG

apflow uses two independent, complementary mechanisms to organize and execute tasks. This is not a compromise — it is the correct design for an orchestration engine that supports creation, execution, reuse, and archival of workflows.

```
parent_id    → Structure Tree (who belongs to whom)
dependencies → Execution DAG  (who waits for whom)
```

### Why Two Models?

Think of it like a car:

```
Physical structure:  Engine parts belong to the engine assembly,
                     which belongs to the powertrain system.

Electrical wiring:   Battery powers the starter motor,
                     ECU controls the fuel injectors.

You don't throw away the assembly diagram just because
you have a wiring diagram. They serve different purposes.
```

In apflow:

| Mechanism | Field | Purpose | Supports |
|-----------|-------|---------|----------|
| **Structure Tree** | `parent_id` | Organizational hierarchy — which tasks form a group | Create, Copy, Link, Archive, Mixed, Progress aggregation |
| **Execution DAG** | `dependencies` | Execution ordering — which tasks must complete first | Parallel execution, Fan-in, Fan-out, Result injection |

### The Operation Matrix

```
                Create   Execute   Copy   Link   Archive   Mixed
Structure Tree    ✅       -        ✅     ✅      ✅       ✅
Execution DAG     -        ✅       -      -       -        -
```

The structure tree supports 5 core operations. The execution DAG supports 1. Removing the tree to make the DAG "purer" would lose 5 of 6 capabilities.

---

## Task Lifecycle: Five Creation Modes

### 1. Create — Build from scratch

```python
tasks = [
    {"id": "fetch", "name": "Fetch Data", "priority": 1},
    {"id": "process", "name": "Process", "parent_id": "fetch", "priority": 2},
]
tree = await task_creator.create_task_tree_from_array(tasks)
```

Validates uniqueness, resolves name→ID references, detects circular dependencies, persists to database, builds in-memory tree.

### 2. Link — Reference a completed workflow (read-only pointer)

```python
tree = await task_creator.from_link(original_task, user_id="new_user")
```

- Creates new tasks that **point to** the originals via `original_task_id`
- Result/params/inputs/schemas are cleared (the link reads from the original)
- Requires entire source tree to be `completed`
- Does not duplicate data — minimal storage cost

**Use case:** Multiple users referencing the same completed analysis.

### 3. Copy — Clone a workflow (modifiable)

```python
tree = await task_creator.from_copy(original_task, priority=0, inputs={"url": "new_url"})
```

- Creates a full copy with new UUIDs
- All `dependencies` IDs are automatically remapped to new IDs
- Upstream dependencies are auto-included (`_auto_include_deps=True`)
- Override any field via `**reset_kwargs`

**Use case:** "Run yesterday's pipeline again with different parameters."

### 4. Archive — Freeze a workflow (immutable snapshot)

```python
tree = await task_creator.from_archive(original_task)
```

- Marks tasks as `origin_type=archive` (frozen, read-only)
- Preserves all data including results
- Requires entire tree to be `completed`

**Use case:** Audit trail, compliance records, production snapshots.

### 5. Mixed — Partial copy + partial link

```python
tree = await task_creator.from_mixed(
    original_task,
    _link_task_ids=["expensive_step_1", "expensive_step_3"],
    inputs={"param": "new_value"},
)
```

- Tasks in `_link_task_ids` are linked (referenced, not copied)
- All other tasks are copied (modifiable)
- Dependency remapping handles both linked and copied IDs

**Use case:** Re-run a 10-step pipeline but skip the expensive steps that haven't changed — link to their existing results, copy and re-execute only the changed steps.

---

## Execution Model

### Priority + Dependency Hybrid

TaskManager uses **both** priority and dependencies to determine execution order:

```
1. Group children by priority (0=urgent → 3=low)
2. For each priority group:
   a. Check each task's dependencies → separate into ready vs waiting
   b. Ready tasks → asyncio.gather() (parallel execution)
   c. Waiting tasks → deferred (triggered later by cascade)
3. After all children complete → execute parent if its dependencies are satisfied
4. Cascade: when any task completes, scan for newly-ready waiting tasks
```

### Execution Order: Children First, Then Parent

```
      A (priority=2)
     / \
    B   C (priority=1)

Execution: B and C execute first (priority 1) → then A executes (priority 2)
```

This means `parent_id` semantics are **"A is the aggregation point for B and C"**, not "A triggers B and C". The parent is the final step that receives children's results.

### DAG Patterns

**Fan-out (one triggers many):**
```python
{"id": "A", "name": "Root"},
{"id": "B", "parent_id": "A", "priority": 1},  # B and C
{"id": "C", "parent_id": "A", "priority": 1},  # execute in parallel
```

**Fan-in (many feed one):**
```python
{"id": "B", "name": "Step B", "priority": 1},
{"id": "C", "name": "Step C", "priority": 1},
{"id": "D", "name": "Merge", "parent_id": "B", "priority": 2,
 "dependencies": [{"id": "B"}, {"id": "C"}]},  # D waits for both
```

**Cross-tree dependencies:**
```python
{"id": "A", "name": "Tree 1 Root"},
{"id": "B", "name": "Tree 2 Root"},
{"id": "C", "parent_id": "A",
 "dependencies": [{"id": "B"}]},  # C is in Tree 1, depends on Tree 2's B
```

### Dependency Result Injection

When task D depends on B and C, their results are automatically merged into D's inputs before execution:

```
B completes → result: {"price": 9.99}
C completes → result: {"price": 19.99}
D starts    → inputs: {"B_id": {"price": 9.99}, "C_id": {"price": 19.99}}
```

The injection is schema-aware — if input/output schemas are defined, fields are mapped by name. Without schemas, results are merged as-is.

### Cascade Triggering

After any task completes, `execute_after_task()` scans all pending tasks in the same tree. If any task's dependencies are now satisfied, it executes immediately. This handles complex DAG patterns where tasks become ready only after multiple predecessors complete.

---

## Validation Pipeline

All validation happens at **creation time**, not execution time:

| Check | When | Method |
|-------|------|--------|
| Name uniqueness | Create | `task_dicts_to_task_models()` |
| ID uniqueness | Create | `task_dicts_to_task_models()` |
| Name→ID resolution | Create | Automatic mapping |
| Circular dependency detection | Create | DFS in `detect_circular_dependencies()` |
| Reference validity | Create | All parent_id and dependency IDs must exist in array |
| DB existence check | Create | Non-UUID IDs checked against database |
| External dependency validation | Copy/Link | `_validate_no_external_dependencies()` |

---

## The Tesla Analogy (Revisited)

```
Tesla's physical assembly   = apflow's structure tree (parent_id)
  Which parts belong to which system, how to replace a module,
  what to ship as a unit.

Tesla's CAN bus wiring      = apflow's execution DAG (dependencies)
  Which systems communicate, signal flow, execution timing.

Tesla's FSD                 = AI agents (Claude, Gemini, any)
  The intelligence that perceives and controls the car.

Tesla's CAN protocol        = apcore (Module Standard)
  Makes every system perceivable and controllable by FSD.
```

apflow doesn't build FSD. It builds the best car that FSD can drive.

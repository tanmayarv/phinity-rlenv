# Bug Finding Strategy for Hardware Tasks

## Background

### Repository Context
This repository contains RL environments where AI agents autonomously work on tasks and get graded. The hardware-tasks environment specifically tests SystemVerilog hardware verification and debugging tasks using:
- **Hidden Harness Paradigm**: Test infrastructure is hidden from agents
- **Dual Grading**: 50% cocotb functional tests + 50% LLM code quality (currently disabled)
- **Target Calibration**: Tasks should have 10-30% success rate (1-3 passes out of 10 attempts)

### Task Calibration Goals
- Start with hard tasks, add hints to calibrate easier
- If agent fails all 10 times → add hints
- If agent succeeds 1-3 times → task is well-calibrated
- **Critical**: Distinguish between legitimate failures vs. our setup issues

## Failure Categories

Agent failures can be caused by:

### Our Side (A-D):
- **A. Prompt/spec inconsistent with test harness** - Specification contradicts what tests expect
- **B. Test harness requires unknown standards** - Tests assume knowledge agent couldn't have (e.g., timescale directives, specific file naming)
- **C. Prompt missing crucial file layout info** - Agent doesn't know where files should be or what structure to use
- **D. Prompt missing crucial design information** - Specification omits critical details agent couldn't infer

### Agent Side (Legitimate Failures):
- Missing domain knowledge they should have
- Logical/comprehension errors
- Bad assumptions in chain of thought
- Implementation mistakes despite having correct information

## Analysis Methodology

### Step 1: Document the Discrepancy
**Key Question**: What's the gap between agent's result and expected result?

Look for:
- Agent's self-verification results vs. hidden harness results
- Example: Agent shows 10/10 tests passed, but grading shows 0/6 passed

**Red Flag**: Large discrepancy suggests interface or fundamental mismatch, likely categories A, B, or C.

### Step 2: Identify the Specification
**Key Questions**: 
- What does the specification explicitly state?
- What interface/behavior is required?
- Is the requirement clear and unambiguous?

**Process**:
1. Read the relevant spec file (`/workdir/docs/Specification.md`)
2. Extract exact interface requirements
3. Note any explicit constraints or behavioral requirements
4. Check for ambiguities or missing details

### Step 3: Examine Agent's Implementation
**Key Questions**:
- What did the agent actually implement?
- How does it differ from the specification?
- Did the agent add/remove/change anything?

**Process**:
1. Review agent's final code submission
2. Compare interface to spec requirements
3. Note any deviations (extra signals, different behavior, etc.)
4. Check if agent acknowledged these changes in their reasoning

### Step 4: Review the Hidden Test Harness
**Key Questions**:
- What interface does the test harness expect?
- Does it match the specification or deviate?
- Are there implicit assumptions in the test?

**Process**:
1. Examine test files in `problem_files/{problem_id}/harness/`
2. Check cocotb test expectations
3. Look for port connections, signal names, expected behavior
4. Identify any undocumented requirements

### Step 5: Categorize the Failure

**Decision Tree**:

```
Does specification clearly define the requirement?
├─ YES → Did test harness follow specification?
│  ├─ YES → Agent's fault (didn't follow spec)
│  └─ NO → Category A (spec/test inconsistency)
└─ NO → Could agent reasonably infer it?
   ├─ YES → Agent's fault (should have inferred correctly)
   └─ NO → Category D (spec missing crucial info)

Did test require undocumented standards?
└─ YES → Category B (unknown standards)

Did prompt explain file layout/structure?
└─ NO (and it mattered) → Category C (missing layout info)
```

### Step 6: Document the Root Cause

**If Our Fault (A-D)**:
- Identify which category
- Quote specific spec ambiguity or missing info
- Propose fix (update spec, add to prompt, align test harness)

**If Agent's Fault**:
Document three components:

1. **Symptoms**: Observable evidence of the problem
   - Test results, error messages, output mismatches
   - Agent's claimed success vs. actual failure

2. **Bug/Error**: The technical mistake
   - Incorrect interface (extra/missing signals)
   - Wrong algorithm implementation  
   - Violated requirements
   - Connect symptoms to this bug

3. **Bad Assumption/Missed Insight**: The reasoning failure
   - What did agent assume that was wrong?
   - What insight did they miss?
   - Where in their chain of thought did they go astray?
   - What should they have done instead?

## Case Study: Problem 7 RC5 LFSR Interface

### The Discrepancy
- Agent's tests: 10/10 passed (100%)
- Hidden harness: 0/6 passed (0%)

### Specification Review
**Lines 147-153 in Specification.md explicitly define**:
```
The interface of `lfsr_8bit.sv` module is given below:
module lfsr_8bit(
    input wire clock,
    input wire reset,
    input wire [7:0] lfsr_seed,
    output reg [7:0] lfsr_out
);
```

**Lines 135**: "When the reset is at active LOW, the LFSR Flip-Flops will be initialized with the bits of the 8-bit initial seed"

### Agent's Implementation
**What agent created**:
```systemverilog
module lfsr_8bit (
    input  logic       clock,
    input  logic       reset,
    input  logic [7:0] seed,
    input  logic       load,        // ← EXTRA SIGNAL
    input  logic       enable,
    output logic [7:0] lfsr_out
);
```

**Behavior change**:
- Spec: Load seed when `reset` is LOW
- Agent: Clear to 0 when `reset` is LOW, load seed when `load` is HIGH

### Categorization
**Result**: Agent's Fault

**Why not category A-D**:
- Spec clearly defined interface (4 ports, not 5)
- Spec explicitly stated reset behavior
- No ambiguity or missing information

### Root Cause Documentation

**Symptoms**:
- Agent verification: 10/10 tests passed
- Hidden harness: 0/6 tests failed
- Complete failure despite agent confidence

**Bug/Error**:
- Added unauthorized `load` signal to LFSR interface (5 ports instead of 4)
- Changed reset behavior from "load seed" to "clear to zero"
- Module interface doesn't match specification

**Bad Assumption & Missed Insight**:
- **Bad Assumption**: "There's a timing race when loading seed during reset, so I need a synchronous load signal"
- **Missed Insight**: The spec explicitly states seed should be loaded during active-LOW reset. The testbench timing issue (seed changing after reset) was a testbench problem, not a design problem. Agent should have fixed testbench timing, not modified the module interface.
- **Chain of Thought Failure**: Agent prioritized making their own testbench work over adhering to the specification's explicit interface requirements. Standard hardware practice is to ensure inputs are stable before releasing reset.

## Quick Reference Checklist

When analyzing a failure:

- [ ] Record discrepancy (agent claim vs. actual grade)
- [ ] Read spec carefully for explicit requirements
- [ ] Examine agent's implementation for deviations
- [ ] Check test harness expectations
- [ ] Look for specification ambiguities or omissions
- [ ] Determine if agent had sufficient information
- [ ] Categorize: A, B, C, D, or Agent's fault
- [ ] Document symptoms → bug → reasoning failure

## Common Patterns

### Indicators of Category A (Spec/Test Mismatch):
- Spec says one thing, tests check something different
- Port names differ between spec and test expectations
- Behavioral requirements conflict

### Indicators of Category B (Unknown Standards):
- Tests fail on syntax/directive issues
- Timescale mismatches
- File naming conventions not documented
- Tool-specific requirements not mentioned

### Indicators of Category C (Missing Layout Info):
- Agent creates files in wrong locations
- Doesn't know to create multiple files vs. single file
- Unsure about directory structure

### Indicators of Category D (Missing Design Info):
- Spec omits critical behavioral details
- No guidance on edge cases
- Undefined requirements that agent must guess

### Indicators of Agent's Fault:
- Spec is clear, but agent implemented differently
- Agent added unauthorized features
- Agent made unjustified assumptions
- Agent's reasoning ignored explicit spec statements
- Agent over-engineered a solution

## Tips for Effective Analysis

1. **Start with the spec** - It's the source of truth
2. **Look for exact quotes** - Cite line numbers when documenting
3. **Compare interfaces first** - Port mismatches cause complete failures
4. **Check agent's reasoning** - Read their thought process for where they went wrong
5. **Be precise** - Quote specific lines, signals, and behaviors
6. **Propose fixes** - If it's our fault, suggest concrete improvements

## When to Add Hints vs. Fix Task

**Add Hints When**:
- Task is legitimately hard (agent lacks knowledge)
- Agent makes understandable comprehension errors
- Success rate is 0/10 but problem is well-formed

**Fix Task When**:
- Category A, B, C, or D issue identified
- Specification is ambiguous or contradictory
- Tests expect undocumented behavior
- Problem setup is fundamentally flawed

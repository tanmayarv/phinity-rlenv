# Asynchronous FIFO with Gray Code Pointers - RL Task

## Task Type
**Specification to RTL** - Implement a complete async FIFO from architectural specification

## Difficulty
Medium-Hard

## Overview
This task challenges the model to implement a production-grade asynchronous FIFO optimized for Clock Domain Crossing (CDC). The implementation requires understanding of:

- Metastability and CDC principles
- Gray code encoding for safe pointer synchronization
- Dual-clock domain management
- Full/empty detection with wraparound logic
- Two-stage synchronizer design
- Parameterized RTL design

## Why This Task Matters

Asynchronous FIFOs are fundamental building blocks in:
- FPGA/ASIC designs with multiple clock domains
- High-speed communication interfaces
- SoC interconnects
- Data buffering between asynchronous subsystems

This task tests whether LLMs can:
1. Translate architectural concepts (Gray code, CDC) into correct RTL
2. Handle subtle corner cases in full/empty detection
3. Implement proper synchronizers for metastability mitigation
4. Create parameterized, synthesizable designs

## Task Components

- `docs/Specification.md` - Complete architectural specification
- `prompt.txt` - Task description for the agent
- `hints.txt` - Optional hints for difficulty tuning
- `sources/async_fifo.sv` - Baseline (incomplete) RTL file
- `pyproject.toml` - Python dependencies for testing

## Current Status

Initial task structure created. Next steps:
1. Create golden solution (`sources/async_fifo.sv` complete implementation)
2. Create comprehensive cocotb testbench (`tests/test_async_fifo_hidden.py`)
3. Convert to HUD format (3-branch structure)
4. Validate and test with frontier models

## Design Challenges

What makes this difficult for LLMs:
- **Gray code math**: Requires understanding XOR-based binary-to-Gray conversion
- **Pointer width calculation**: Must add 1 bit for wraparound detection
- **Full logic complexity**: Non-obvious MSB comparison in Gray domain
- **Synchronizer timing**: Must balance CDC safety with latency
- **Edge cases**: Simultaneous read/write, back-to-back operations, independent resets

Expected pass@10 rate: 10-30% for Claude 4.5 Sonnet

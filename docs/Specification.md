# Asynchronous FIFO with Gray Code Pointers

## Overview

A First-In-First-Out (FIFO) buffer is a fundamental building block in digital systems, enabling data transfer between clock domains or components operating at different rates. An **asynchronous FIFO** is specifically designed to safely transfer data between two independent clock domains (Clock Domain Crossing, or CDC), making it essential for FPGA and ASIC designs where different subsystems operate on separate clocks.

The key challenge in asynchronous FIFOs is handling **metastability** — when signals cross clock domains, flip-flops may enter unstable states. To mitigate this, async FIFOs use **Gray code** for pointer synchronization, as Gray code changes only one bit at a time, minimizing the risk of misreads during clock domain crossings.

## Functionality

### Core Requirements

You must implement a parameterized asynchronous FIFO with the following specifications:

1. **Dual-Clock Operation**: Separate read and write clock domains (`wclk` and `rclk`)
2. **Parameterized Depth**: FIFO depth must be a power of 2 (parameter `DEPTH`)
3. **Parameterized Data Width**: Configurable data width (parameter `DATA_WIDTH`)
4. **Gray Code Pointers**: Write and read pointers must use Gray code encoding for CDC safety
5. **Proper Full/Empty Logic**: Accurate detection of full and empty conditions
6. **Dual-Port Memory**: Internal memory with separate read and write ports

### Module Interface

```systemverilog
module async_fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH = 16  // Must be power of 2
)(
    // Write clock domain
    input  wire                  wclk,      // Write clock
    input  wire                  wrst_n,    // Write domain reset (active low)
    input  wire                  wen,       // Write enable
    input  wire [DATA_WIDTH-1:0] wdata,     // Write data
    output wire                  wfull,     // FIFO full flag
    
    // Read clock domain
    input  wire                  rclk,      // Read clock
    input  wire                  rrst_n,    // Read domain reset (active low)
    input  wire                  ren,       // Read enable
    output wire [DATA_WIDTH-1:0] rdata,     // Read data
    output wire                  rempty     // FIFO empty flag
);
```

### Architecture Details

#### 1. Memory Array

Implement a dual-port memory array using a register array:
```systemverilog
reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
```

- **Write operation**: On `posedge wclk`, if `wen && !wfull`, write `wdata` to `mem[waddr]`
- **Read operation**: **Combinational (asynchronous) read** from `mem[raddr]` - Industry standard for FIFOs
  ```systemverilog
  assign rdata = mem[rptr_bin[ADDR_WIDTH-1:0]];
  ```
  This provides **zero-cycle read latency** - data is available immediately on the output.

#### 2. Pointer Management

You need **four pointers** to manage the FIFO:

1. **Write Pointer (Binary)** — `waddr` in write domain for memory addressing
2. **Write Pointer (Gray)** — `wptr_gray` in write domain for synchronization
3. **Read Pointer (Binary)** — `raddr` in read domain for memory addressing
4. **Read Pointer (Gray)** — `rptr_gray` in read domain for synchronization

**Pointer Width**: For a FIFO of depth `DEPTH`, pointers must be `$clog2(DEPTH) + 1` bits wide. The extra bit is crucial for distinguishing between full and empty conditions (wraparound detection).

**Example**: For `DEPTH = 16`:
- Address width = 4 bits (to address 0-15)
- Pointer width = 5 bits (for wraparound detection)

#### 3. Binary to Gray Code Conversion

Gray code ensures only one bit changes per increment, critical for CDC safety.

**Binary to Gray formula**:
```systemverilog
gray = binary ^ (binary >> 1);
```

**Example conversions**:
- Binary `0000` → Gray `0000`
- Binary `0001` → Gray `0001`
- Binary `0010` → Gray `0011`
- Binary `0011` → Gray `0010`
- Binary `0100` → Gray `0110`

#### 4. Gray to Binary Conversion

When comparing pointers across domains, you may need to convert Gray back to binary:

```systemverilog
binary[MSB] = gray[MSB];
for (int i = MSB-1; i >= 0; i--) begin
    binary[i] = binary[i+1] ^ gray[i];
end
```

#### 5. Clock Domain Crossing Synchronizers

To safely transfer Gray-coded pointers across clock domains, use **two-stage synchronizers**:

**Write pointer to read domain**:
```systemverilog
reg [PTR_WIDTH-1:0] wptr_gray_sync1, wptr_gray_sync2;

always @(posedge rclk or negedge rrst_n) begin
    if (!rrst_n) begin
        wptr_gray_sync1 <= 0;
        wptr_gray_sync2 <= 0;
    end else begin
        wptr_gray_sync1 <= wptr_gray;      // First synchronizer stage
        wptr_gray_sync2 <= wptr_gray_sync1; // Second synchronizer stage
    end
end
```

**Read pointer to write domain**: Similar synchronizer for `rptr_gray`

#### 6. Full and Empty Detection

**Empty Condition** (in read domain):
- FIFO is empty when read Gray pointer equals the synchronized write Gray pointer
```systemverilog
rempty = (rptr_gray == wptr_gray_sync2);
```

**Full Condition** (in write domain):
- FIFO is full when:
  - The MSB bits of write and read pointers differ (wraparound occurred)
  - The second MSB bits differ
  - All other bits are equal

```systemverilog
// For N-bit Gray pointers:
wfull = (wptr_gray[N-1] != rptr_gray_sync2[N-1]) &&
        (wptr_gray[N-2] != rptr_gray_sync2[N-2]) &&
        (wptr_gray[N-3:0] == rptr_gray_sync2[N-3:0]);
```

**Why this works**: When write pointer wraps around once more than read pointer, the MSBs differ, indicating full.

### Reset Behavior

- On `wrst_n` (active low), initialize write pointers to 0
- On `rrst_n` (active low), initialize read pointers to 0
- Resets are **asynchronous** but can be applied independently in each domain

### Edge Cases to Handle

1. **Simultaneous read/write**: When FIFO has exactly one slot left and both ren/wen are asserted
2. **Back-to-back operations**: Consecutive reads or writes without gaps
3. **Reset in one domain**: Ensure proper behavior if only one domain resets
4. **Initial empty state**: FIFO should report empty immediately after reset

## Working Example

### Example: 4-entry FIFO (DEPTH=4, DATA_WIDTH=8)

**Pointer width**: `$clog2(4) + 1 = 3 bits`

**Sequence**:

| Cycle | Operation | waddr | wptr (bin) | wptr (gray) | raddr | rptr (bin) | rptr (gray) | Empty | Full | Contents |
|-------|-----------|-------|------------|-------------|-------|------------|-------------|-------|------|----------|
| 0     | Reset     | 000   | 000        | 000         | 000   | 000        | 000         | 1     | 0    | []       |
| 1     | Write A   | 000   | 001        | 001         | 000   | 000        | 000         | 0     | 0    | [A]      |
| 2     | Write B   | 001   | 010        | 011         | 000   | 000        | 000         | 0     | 0    | [A,B]    |
| 3     | Write C   | 010   | 011        | 010         | 000   | 000        | 000         | 0     | 0    | [A,B,C]  |
| 4     | Write D   | 011   | 100        | 110         | 000   | 000        | 000         | 0     | 1    | [A,B,C,D]|
| 5     | Read → A  | 011   | 100        | 110         | 001   | 001        | 001         | 0     | 0    | [B,C,D]  |
| 6     | Read → B  | 011   | 100        | 110         | 010   | 010        | 011         | 0     | 0    | [C,D]    |

Note: Synchronizer delays (2 cycles) mean full/empty updates lag slightly in real implementation.

## Implementation Notes

- Use **non-blocking assignments** (`<=`) for sequential logic
- Memory write should be on `posedge wclk`
- **Memory read must be combinational** (not registered) for industry-standard zero-cycle latency:
  - Use `assign rdata = mem[raddr]` 
  - Do NOT register the read output
  - This matches behavior of commercial FIFO IPs
- Ensure all cross-domain signals use Gray code
- Synthesizable code only — avoid behavioral delays or non-synthesizable constructs
- Pre-calculate "next" pointer values for cleaner synthesis

## Design Challenges

This task tests your understanding of:
1. **Metastability and CDC**: Why Gray code matters
2. **Pointer arithmetic**: Managing wraparound with extra MSB
3. **Full/Empty logic**: Subtle differences in detection across domains
4. **Parameterization**: Making the design flexible for any power-of-2 depth
5. **Reset handling**: Independent async resets in two domains

A correct implementation will pass comprehensive testbenches covering corner cases like simultaneous operations, rapid fill/drain cycles, and randomized read/write patterns.


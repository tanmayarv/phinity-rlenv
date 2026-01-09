"""
Comprehensive testbench for asynchronous FIFO with Gray code pointers
Tests CDC safety, full/empty detection, and corner cases
Updated for combinational read output (industry standard)
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ClockCycles


@cocotb.test()
async def test_basic_write_read(dut):
    """Test basic write and read operations"""
    
    # Start clocks with different periods (async operation)
    wclk = Clock(dut.wclk, 10, unit="ns")  # 100 MHz
    rclk = Clock(dut.rclk, 15, unit="ns")  # 66.7 MHz
    cocotb.start_soon(wclk.start())
    cocotb.start_soon(rclk.start())
    
    # Reset both domains
    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    dut.wen.value = 0
    dut.ren.value = 0
    await ClockCycles(dut.wclk, 2)
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    await ClockCycles(dut.wclk, 2)
    
    # Check initial empty
    await RisingEdge(dut.rclk)
    assert dut.rempty.value == 1, f"FIFO should be empty after reset, got rempty={dut.rempty.value}"
    assert dut.wfull.value == 0, f"FIFO should not be full after reset, got wfull={dut.wfull.value}"
    
    # Write single value
    dut.wen.value = 1
    dut.wdata.value = 0xAA
    await RisingEdge(dut.wclk)
    dut.wen.value = 0
    
    # Wait for synchronization (2 sync stages + 1 for empty flag update)
    await ClockCycles(dut.rclk, 4)
    
    # Check not empty
    assert dut.rempty.value == 0, f"FIFO should not be empty after write, got rempty={dut.rempty.value}"
    
    # Read value - with combinational read, data is available immediately
    dut.ren.value = 1
    await RisingEdge(dut.rclk)
    # Data is available combinationally after rptr increments
    read_val = int(dut.rdata.value)
    assert read_val == 0xAA, f"Expected 0xAA, got {hex(read_val)}"
    dut.ren.value = 0
    
    # Wait for empty flag to update
    await ClockCycles(dut.rclk, 2)
    
    # Check empty again
    assert dut.rempty.value == 1, f"FIFO should be empty after reading all data"


@cocotb.test()
async def test_fill_and_drain(dut):
    """Test filling FIFO completely then draining"""
    
    wclk = Clock(dut.wclk, 10, unit="ns")
    rclk = Clock(dut.rclk, 12, unit="ns")
    cocotb.start_soon(wclk.start())
    cocotb.start_soon(rclk.start())
    
    # Reset
    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    dut.wen.value = 0
    dut.ren.value = 0
    await ClockCycles(dut.wclk, 2)
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    await ClockCycles(dut.wclk, 2)
    
    # Fill FIFO completely (DEPTH = 16)
    test_data = [i * 0x11 for i in range(16)]
    dut.wen.value = 1
    for data in test_data:
        if dut.wfull.value == 1:
            break
        dut.wdata.value = data
        await RisingEdge(dut.wclk)
    dut.wen.value = 0
    
    # Wait for full flag to propagate
    await ClockCycles(dut.wclk, 5)
    
    # Check full flag
    assert dut.wfull.value == 1, "FIFO should be full after 16 writes"
    
    # Wait for synchronization to read domain
    await ClockCycles(dut.rclk, 5)
    
    # Drain FIFO - with combinational read, data available immediately
    read_data = []
    for i in range(16):
        if dut.rempty.value == 1:
            break
        dut.ren.value = 1
        await RisingEdge(dut.rclk)
        # Data available combinationally
        read_data.append(int(dut.rdata.value))
        dut.ren.value = 0
        await RisingEdge(dut.rclk)  # Small gap between reads
    
    # Verify data
    assert len(read_data) == 16, f"Expected 16 reads, got {len(read_data)}"
    for i, (expected, actual) in enumerate(zip(test_data, read_data)):
        assert actual == expected, f"Mismatch at index {i}: expected {hex(expected)}, got {hex(actual)}"


@cocotb.test()
async def test_simultaneous_read_write(dut):
    """Test simultaneous reading and writing"""
    
    wclk = Clock(dut.wclk, 10, unit="ns")
    rclk = Clock(dut.rclk, 10, unit="ns")  # Same frequency
    cocotb.start_soon(wclk.start())
    cocotb.start_soon(rclk.start())
    
    # Reset
    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    dut.wen.value = 0
    dut.ren.value = 0
    await ClockCycles(dut.wclk, 2)
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    await ClockCycles(dut.wclk, 2)
    
    # Write a few items first
    dut.wen.value = 1
    for i in range(8):
        dut.wdata.value = 0x10 + i
        await RisingEdge(dut.wclk)
    dut.wen.value = 0
    
    # Wait for sync
    await ClockCycles(dut.rclk, 5)
    
    # Now do simultaneous read and write
    write_data = [0x50 + i for i in range(10)]
    read_data = []
    
    dut.wen.value = 1
    dut.ren.value = 1
    
    for i in range(10):
        dut.wdata.value = write_data[i]
        await RisingEdge(dut.wclk)
        if not dut.rempty.value:
            read_data.append(int(dut.rdata.value))
    
    dut.wen.value = 0
    dut.ren.value = 0
    
    # FIFO should have some data (verify it's not broken)
    await ClockCycles(dut.rclk, 3)
    assert len(read_data) > 0, "Should have read some data during simultaneous operations"


@cocotb.test()
async def test_wraparound(dut):
    """Test pointer wraparound behavior"""
    
    wclk = Clock(dut.wclk, 8, unit="ns")
    rclk = Clock(dut.rclk, 10, unit="ns")
    cocotb.start_soon(wclk.start())
    cocotb.start_soon(rclk.start())
    
    # Reset
    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    dut.wen.value = 0
    dut.ren.value = 0
    await ClockCycles(dut.wclk, 2)
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    await ClockCycles(dut.wclk, 2)
    
    # Perform multiple fill-drain cycles to test wraparound
    for cycle in range(3):
        # Write
        dut.wen.value = 1
        for i in range(12):
            dut.wdata.value = (cycle * 16 + i) & 0xFF
            await RisingEdge(dut.wclk)
        dut.wen.value = 0
        
        # Wait for sync
        await ClockCycles(dut.rclk, 5)
        
        # Read
        for i in range(12):
            if not dut.rempty.value:
                dut.ren.value = 1
                await RisingEdge(dut.rclk)
                dut.ren.value = 0
        
        # Wait for sync
        await ClockCycles(dut.wclk, 5)
    
    # Final check - FIFO should still be functional
    dut.wen.value = 1
    dut.wdata.value = 0xFF
    await RisingEdge(dut.wclk)
    dut.wen.value = 0
    
    await ClockCycles(dut.rclk, 5)
    assert dut.rempty.value == 0, "FIFO should not be empty after final write"


@cocotb.test()
async def test_back_to_back_operations(dut):
    """Test back-to-back writes and reads"""
    
    wclk = Clock(dut.wclk, 10, unit="ns")
    rclk = Clock(dut.rclk, 10, unit="ns")
    cocotb.start_soon(wclk.start())
    cocotb.start_soon(rclk.start())
    
    # Reset
    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    dut.wen.value = 0
    dut.ren.value = 0
    await ClockCycles(dut.wclk, 2)
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    await ClockCycles(dut.wclk, 2)
    
    # Back-to-back writes
    dut.wen.value = 1
    for i in range(10):
        dut.wdata.value = 0x20 + i
        await RisingEdge(dut.wclk)
    dut.wen.value = 0
    
    # Wait for sync
    await ClockCycles(dut.rclk, 5)
    
    # Back-to-back reads
    read_count = 0
    dut.ren.value = 1
    for i in range(12):  # Try to read more than written
        await RisingEdge(dut.rclk)
        if not dut.rempty.value:
            read_count += 1
        else:
            break
    dut.ren.value = 0
    
    assert read_count == 10, f"Expected to read 10 items, got {read_count}"


@cocotb.test()
async def test_different_clock_ratios(dut):
    """Test with very different clock frequencies"""
    
    # Fast write, slow read
    wclk = Clock(dut.wclk, 5, unit="ns")   # 200 MHz
    rclk = Clock(dut.rclk, 20, unit="ns")  # 50 MHz
    cocotb.start_soon(wclk.start())
    cocotb.start_soon(rclk.start())
    
    # Reset
    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    dut.wen.value = 0
    dut.ren.value = 0
    await ClockCycles(dut.wclk, 2)
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    await ClockCycles(dut.wclk, 5)
    
    # Fast write
    dut.wen.value = 1
    for i in range(8):
        dut.wdata.value = 0x80 + i
        await RisingEdge(dut.wclk)
    dut.wen.value = 0
    
    # Wait for sync (need more read clocks due to slow rate)
    await ClockCycles(dut.rclk, 10)
    
    # Slow read
    read_data = []
    for i in range(10):
        if not dut.rempty.value:
            dut.ren.value = 1
            await RisingEdge(dut.rclk)
            read_data.append(int(dut.rdata.value))
            dut.ren.value = 0
        await RisingEdge(dut.rclk)
    
    assert len(read_data) == 8, f"Expected 8 reads, got {len(read_data)}"


@cocotb.test()
async def test_reset_recovery(dut):
    """Test reset in one domain while other is active"""
    
    wclk = Clock(dut.wclk, 10, unit="ns")
    rclk = Clock(dut.rclk, 12, unit="ns")
    cocotb.start_soon(wclk.start())
    cocotb.start_soon(rclk.start())
    
    # Initial reset
    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    dut.wen.value = 0
    dut.ren.value = 0
    await ClockCycles(dut.wclk, 2)
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    await ClockCycles(dut.wclk, 2)
    
    # Write some data
    dut.wen.value = 1
    for i in range(5):
        dut.wdata.value = 0x30 + i
        await RisingEdge(dut.wclk)
    dut.wen.value = 0
    
    # Reset read domain only
    dut.rrst_n.value = 0
    await ClockCycles(dut.rclk, 2)
    dut.rrst_n.value = 1
    await ClockCycles(dut.rclk, 3)
    
    # Check that read domain recovered (empty flag should be set)
    assert dut.rempty.value == 1, "Read domain should show empty after reset"
    
    # Reset both and verify clean state
    dut.wrst_n.value = 0
    dut.rrst_n.value = 0
    await ClockCycles(dut.wclk, 2)
    dut.wrst_n.value = 1
    dut.rrst_n.value = 1
    await ClockCycles(dut.wclk, 2)
    
    assert dut.rempty.value == 1, "Should be empty after full reset"
    assert dut.wfull.value == 0, "Should not be full after full reset"


# Pytest runner (required for HUD framework)
def test_async_fifo_hidden_runner():
    import os
    from pathlib import Path
    from cocotb_tools.runner import get_runner
    
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    
    sources = [proj_path / "sources/async_fifo.sv"]
    
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="async_fifo",
        always=True,
    )
    
    runner.test(
        hdl_toplevel="async_fifo",
        test_module="test_async_fifo_hidden"
    )


if __name__ == "__main__":
    test_async_fifo_hidden_runner()

`timescale 1ns/1ps

module async_fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH = 16
)(
    // Write clock domain
    input  wire                  wclk,
    input  wire                  wrst_n,
    input  wire                  wen,
    input  wire [DATA_WIDTH-1:0] wdata,
    output reg                   wfull,
    
    // Read clock domain
    input  wire                  rclk,
    input  wire                  rrst_n,
    input  wire                  ren,
    output wire [DATA_WIDTH-1:0] rdata,
    output reg                   rempty
);

    // TODO: Implement the Asynchronous FIFO logic here
    // 
    // Required components:
    // 1. Memory array for FIFO storage
    // 2. Binary and Gray code pointers for both domains
    // 3. Binary-to-Gray conversion logic
    // 4. Two-stage synchronizers for CDC
    // 5. Full and empty detection logic
    //
    // See /workdir/docs/Specification.md for complete details

endmodule

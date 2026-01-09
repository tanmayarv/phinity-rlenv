`timescale 1ns/1ps

// Asynchronous FIFO with Gray Code Pointers for Clock Domain Crossing
module async_fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH = 16
)(
    // Write domain
    input  wire                  wclk,
    input  wire                  wrst_n,
    input  wire                  wen,
    input  wire [DATA_WIDTH-1:0] wdata,
    output reg                   wfull,
    
    // Read domain
    input  wire                  rclk,
    input  wire                  rrst_n,
    input  wire                  ren,
    output wire [DATA_WIDTH-1:0] rdata,
    output reg                   rempty
);

    localparam ADDR_WIDTH = $clog2(DEPTH);
    localparam PTR_WIDTH = ADDR_WIDTH + 1;  // Extra bit for full/empty detection
    
    // Dual-port memory
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    
    // Initialize memory to prevent X propagation
    integer i;
    initial begin
        for (i = 0; i < DEPTH; i = i + 1)
            mem[i] = {DATA_WIDTH{1'b0}};
    end
    
    // Write domain signals
    reg [PTR_WIDTH-1:0] wptr_bin, wptr_gray;
    reg [PTR_WIDTH-1:0] rptr_gray_sync1, rptr_gray_sync2;
    wire [PTR_WIDTH-1:0] wptr_bin_next, wptr_gray_next;
    
    // Read domain signals
    reg [PTR_WIDTH-1:0] rptr_bin, rptr_gray;
    reg [PTR_WIDTH-1:0] wptr_gray_sync1, wptr_gray_sync2;
    wire [PTR_WIDTH-1:0] rptr_bin_next, rptr_gray_next;
    
    // Binary to Gray conversion
    function [PTR_WIDTH-1:0] bin2gray;
        input [PTR_WIDTH-1:0] binary;
        begin
            bin2gray = binary ^ (binary >> 1);
        end
    endfunction
    
    // ============ Write Domain ============
    
    assign wptr_bin_next = wptr_bin + (wen && !wfull);
    assign wptr_gray_next = bin2gray(wptr_bin_next);
    
    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            wptr_bin <= {PTR_WIDTH{1'b0}};
            wptr_gray <= {PTR_WIDTH{1'b0}};
        end else begin
            wptr_bin <= wptr_bin_next;
            wptr_gray <= wptr_gray_next;
        end
    end
    
    always @(posedge wclk) begin
        if (wen && !wfull)
            mem[wptr_bin[ADDR_WIDTH-1:0]] <= wdata;
    end
    
    // Synchronize read pointer (Gray) to write domain
    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n)
            {rptr_gray_sync2, rptr_gray_sync1} <= {(2*PTR_WIDTH){1'b0}};
        else
            {rptr_gray_sync2, rptr_gray_sync1} <= {rptr_gray_sync1, rptr_gray};
    end
    
    // Full when write wrapped once more than read (MSB, MSB-1 differ, rest match)
    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n)
            wfull <= 1'b0;
        else
            wfull <= (wptr_gray_next == {~rptr_gray_sync2[PTR_WIDTH-1:PTR_WIDTH-2], 
                                         rptr_gray_sync2[PTR_WIDTH-3:0]});
    end
    
    // ============ Read Domain ============
    
    assign rptr_bin_next = rptr_bin + (ren && !rempty);
    assign rptr_gray_next = bin2gray(rptr_bin_next);
    
    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rptr_bin <= {PTR_WIDTH{1'b0}};
            rptr_gray <= {PTR_WIDTH{1'b0}};
        end else begin
            rptr_bin <= rptr_bin_next;
            rptr_gray <= rptr_gray_next;
        end
    end
    
    // Combinational read for zero-cycle latency
    assign rdata = mem[rptr_bin[ADDR_WIDTH-1:0]];
    
    // Synchronize write pointer (Gray) to read domain
    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n)
            {wptr_gray_sync2, wptr_gray_sync1} <= {(2*PTR_WIDTH){1'b0}};
        else
            {wptr_gray_sync2, wptr_gray_sync1} <= {wptr_gray_sync1, wptr_gray};
    end
    
    // Empty when read pointer equals synchronized write pointer
    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n)
            rempty <= 1'b1;
        else
            rempty <= (rptr_gray_next == wptr_gray_sync2);
    end

endmodule

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
    output wire [DATA_WIDTH-1:0] rdata,    // Changed to wire - combinational output
    output reg                   rempty
);

    // Calculate pointer width: log2(DEPTH) + 1 for wraparound detection
    localparam ADDR_WIDTH = $clog2(DEPTH);
    localparam PTR_WIDTH = ADDR_WIDTH + 1;
    
    // Memory array - dual port
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    
    // Initialize memory to avoid X propagation in simulation
    integer i;
    initial begin
        for (i = 0; i < DEPTH; i = i + 1) begin
            mem[i] = {DATA_WIDTH{1'b0}};
        end
    end
    
    //=======================================================
    // Write Domain Signals
    //=======================================================
    reg [PTR_WIDTH-1:0] wptr_bin;          // Binary write pointer
    reg [PTR_WIDTH-1:0] wptr_gray;         // Gray code write pointer
    reg [PTR_WIDTH-1:0] rptr_gray_sync1;   // Sync stage 1
    reg [PTR_WIDTH-1:0] rptr_gray_sync2;   // Sync stage 2
    
    // Next value wires for cleaner synthesis
    wire [PTR_WIDTH-1:0] wptr_bin_next;
    wire [PTR_WIDTH-1:0] wptr_gray_next;
    
    //=======================================================
    // Read Domain Signals
    //=======================================================
    reg [PTR_WIDTH-1:0] rptr_bin;          // Binary read pointer
    reg [PTR_WIDTH-1:0] rptr_gray;         // Gray code read pointer
    reg [PTR_WIDTH-1:0] wptr_gray_sync1;   // Sync stage 1
    reg [PTR_WIDTH-1:0] wptr_gray_sync2;   // Sync stage 2
    
    // Next value wires for cleaner synthesis
    wire [PTR_WIDTH-1:0] rptr_bin_next;
    wire [PTR_WIDTH-1:0] rptr_gray_next;
    
    //=======================================================
    // Binary to Gray Conversion Function
    //=======================================================
    function [PTR_WIDTH-1:0] bin2gray;
        input [PTR_WIDTH-1:0] binary;
        begin
            bin2gray = binary ^ (binary >> 1);
        end
    endfunction
    
    //=======================================================
    // Write Domain Logic
    //=======================================================
    
    // Calculate next write pointer values (combinational)
    assign wptr_bin_next = wptr_bin + (wen && !wfull);
    assign wptr_gray_next = bin2gray(wptr_bin_next);
    
    // Write pointer management
    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            wptr_bin <= {PTR_WIDTH{1'b0}};
            wptr_gray <= {PTR_WIDTH{1'b0}};
        end else begin
            wptr_bin <= wptr_bin_next;
            wptr_gray <= wptr_gray_next;
        end
    end
    
    // Memory write logic
    always @(posedge wclk) begin
        if (wen && !wfull) begin
            mem[wptr_bin[ADDR_WIDTH-1:0]] <= wdata;
        end
    end
    
    // Synchronize read pointer to write domain (2-stage)
    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            {rptr_gray_sync2, rptr_gray_sync1} <= {(2*PTR_WIDTH){1'b0}};
        end else begin
            {rptr_gray_sync2, rptr_gray_sync1} <= {rptr_gray_sync1, rptr_gray};
        end
    end
    
    // Full flag generation (compact form from reference)
    // Full when write pointer has wrapped once more than read pointer
    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            wfull <= 1'b0;
        end else begin
            // Compact comparison: MSB and MSB-1 differ, rest match
            wfull <= (wptr_gray_next == {~rptr_gray_sync2[PTR_WIDTH-1:PTR_WIDTH-2], 
                                         rptr_gray_sync2[PTR_WIDTH-3:0]});
        end
    end
    
    //=======================================================
    // Read Domain Logic
    //=======================================================
    
    // Calculate next read pointer values (combinational)
    assign rptr_bin_next = rptr_bin + (ren && !rempty);
    assign rptr_gray_next = bin2gray(rptr_bin_next);
    
    // Read pointer management
    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rptr_bin <= {PTR_WIDTH{1'b0}};
            rptr_gray <= {PTR_WIDTH{1'b0}};
        end else begin
            rptr_bin <= rptr_bin_next;
            rptr_gray <= rptr_gray_next;
        end
    end
    
    // Memory read logic - COMBINATIONAL for industry-standard 0-cycle latency
    // Read data is immediately available (not registered)
    assign rdata = mem[rptr_bin[ADDR_WIDTH-1:0]];
    
    // Synchronize write pointer to read domain (2-stage)
    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            {wptr_gray_sync2, wptr_gray_sync1} <= {(2*PTR_WIDTH){1'b0}};
        end else begin
            {wptr_gray_sync2, wptr_gray_sync1} <= {wptr_gray_sync1, wptr_gray};
        end
    end
    
    // Empty flag generation
    // Empty when read pointer equals synchronized write pointer (Gray comparison)
    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rempty <= 1'b1;  // Start empty
        end else begin
            rempty <= (rptr_gray_next == wptr_gray_sync2);
        end
    end

endmodule

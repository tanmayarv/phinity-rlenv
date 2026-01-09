# phinity-rlenv

hello i dont know who's gonna be reading this so im writing this as texts basically (hi sonya)

maybe i'll GPT this into soemthing nicer later

my idea is gonna be to try to get cursor to make an an async fifo parameterized with the purpose of solving cdc + implement gray code for teh pointers (spec -> RTL)

+ good task coz have to understand metastability, cdc, gray code, binary <-> grey, pointer depths and stuff from a spec
+ very realistic in p much every fpga/ asic deisgn
+ gray code specifically is an upgrade to regular pointer logic in a fifo
- quite common may be available as training data?
- i have done this before in psuedocode in interviews so maybe maybe want something logically more challenging
(will deepen this a bit later genuinely a good idea v replicable)

can edit this task to do like a rtl upgrade/ edit type thing, give a completely basic hard coded fifo and ask to make parameterizable and optimize for CDC (assume the gray code is implied as a cdc sol?) so like expand the CDC for 2^N depth w/ N+1 pointers (wraparound)

+ code edit/ upgarde (as opp to just spec to rtl), test code comprehension
+ can track agent thinking trace around reaidng hardcoded stuff and identifying parameterization
+   ^^ this is particularly good in python, replicate in hw/rtl
- less code? idk lets see

so i built a TPU v1/2 styled systolic array GEMM/ ML accelerator unit 
incredible example of module reuse, generate loops, dataflow, timing verif etc
the entire base architecture is waaay too complex (i tried lol even MAX mode ended up like timing out)
maybe a reduced version of that targeting module reuse or something
like I can provide pe.sv (pe is processing element, the compute unit that does the math, MAC/ FMA w/ saturation)
and ask model to give me the generated systolic array with correct connections inferring muxed or combined weightflow and psum dataflow
(on hold, will consider)

smaller fifo spec -> rtl with ambiguity around edge cases, full/empty logic, pointer depth etc.

debugging a broken FSM (say 4-6 states with slightly complex logic) DES/ crypto something? good part is this is an intensely LLM-able task, they know the actual encryption algos much better than humans (in code form at least)
say we get a good implementation and mess up one state transition or a couple registers
+ tests whether LLM keeps most of the working stuff and parses through and finds
+ (IMPORTANT) tests whether model doesnt overthink/ over engineer stuff - critical coz claude does this a bunch on cursor/ agent platforms

another option is a AXI-lite–style handshake submodule

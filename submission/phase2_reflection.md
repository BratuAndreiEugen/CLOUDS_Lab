# Phase 2 — Reflection: where does parallelism stop helping?

Copy this file to `submission/phase2_reflection.md`, fill in every answer slot, and commit it:

```bash
cp phase-2-tiny-gpt/reflection_template.md submission/phase2_reflection.md
```

**How to fill it in.** Each answer sits between a pair of `<!--answer:...-->` markers. Replace
the `TODO` line with your answer — **leave the markers themselves untouched**, they are how the
grader finds your answers. Anything you write outside the markers is ignored, so add extra
prose, tables or your threading plot freely.

Numbers in section 1 must **match `submission/phase2_report.json`** — copy them across, do not
retype from memory; they are checked against it.

---

## 1. Your measurements

| | Value |
|---|---|
| Naive attention, ms (`attention.naive_ms`) | <!--answer:attn_naive_ms-->529.045<!--/answer--> |
| Vectorized attention, ms (`attention.vectorized_ms`) | <!--answer:attn_vectorized_ms-->1.781<!--/answer--> |
| CPU training, ms for 100 steps (`devices.cpu_ms`) | <!--answer:cpu_ms-->486291.9<!--/answer--> |
| GPU training, ms for 100 steps (`devices.gpu_ms`) | <!--answer:gpu_ms-->17651.6<!--/answer--> |
| Final training loss (`training.final_loss`) | <!--answer:final_loss-->1.5188<!--/answer--> |

**The thread sweep.** Give your four timings from `threads` — 1, 2, 4 and 8 threads — and say
which count was fastest. (verbatim: the numbers, in order)

<!--answer:thread_sweep-->
1: 2601.283 ms, 2: 2291.494 ms, 4: 2545.235 ms, 8: 2963.615 ms
The fastest run was with 2 threads: 2291.494 ms
<!--/answer-->

---

## 2. Intra-node parallelism, three ways

**Why vectorizing wins.** Both attention implementations do the same arithmetic and produce the
same result (the unit test checks that). Explain where the naive version's time actually goes,
and what the vectorized one does differently — in terms of the machine, not the Python.
(~70 words)

<!--answer:vectorization_why-->
The `attention_naive` function uses explicit Python loops to calculate one dot product at a time. At the hardware level, the CPU spends most of its time running the Fetch → Decode → Register → Execute → Writeback pipeline on these individual instructions. The `attention_vectorized` function passes whole matrices to NumPy, which uses BLAS (Basic Linear Algebra Subprograms) compiled with SIMD (Single Instruction, Multiple Data) instructions. SIMD allows the CPU to process multiple instructions as one in a pipeline. The usage of BLAS is confirmed in the notebook section 1 and my understanding of it comes from online documentation of OpenBLAS and scipy-openblas.
<!--/answer-->

**Where the thread curve flattens, and why.** Using your sweep: more threads stopped helping —
or started hurting — at some point. Say where, and give the reason. Your Colab runtime's vCPU
count is part of the answer; so is what the threads have to coordinate on. (~80 words)

<!--answer:threading_plateau-->
Running `lscpu` on Google Collab reveals that the machine only has 1 CPU core and 2 threads per core. This reveals why it is capable of making an improvement in performance at 2 threads, but with 4 and 8 threads it gets progressively worse because of thread contention: the threads have to fight more over execution time since they cannot run simultaneously. For the 4 and 8 thread runs, the execution context is more oftenly changed from one thread to another and they also have to fight over the shared CPU caches. 
<!--/answer-->

**What made the GPU faster.** The model, the data and the step count were identical; only the
device changed. Say what about a transformer training step suits a GPU, and name one workload
that would *not* see this speed-up. (~70 words)

<!--answer:gpu_why-->
Transformer training steps are formed from large, independent matrix multiplications which map to 2D grids of CUDA threads executing in lockstep (threads in a warp (group of threads of static size - 32) that run the same instruction simultaniously at each clock cycle). This is a perfect example of an ideal Sigle Instruction, Multiple Thread (SIMT) application. 
<!--/answer-->

---

## 3. The question

**Where does parallelism stop helping, and why?** Pull the three experiments together. Your
answer should distinguish the *kinds* of limit you met — work that cannot be divided, hardware
you do not have, coordination that costs more than it saves, data that has to move — and say
which one bound each experiment. One concrete number from section 1 per claim. (~150 words)

<!--answer:parallelism_limit-->
First, all types of parallelism are limited by Amdahl's law, performance improvement being limited by the operations that cannot be parallelized (for example, the GPU still has to wait for data to be transfered from host to the device at each step). This would fall under "work that cannot be divided".
Let's say for the GPU execution, data transfer is 20% (0.2) of the runtime, the rest of 80% (0.8) is math. For 256 x 32 threads the speedup is 1/(0.2 + 0.8/(256*32)) ~ 5x. This number will fall the more the data transfer (unparallelizable part) becomes more frequent (smaller batches for example).
#### CPU Multithreading Limit
This is bound by "hardware you do not have" and "coordination that costs more than it saves". The Google Colab environment only provides a machine with 2 vCPU. Because of this, performance peaked at 2 threads (2291.494 ms). Running with 4 threads (2545.235 ms) did not show much of an improvement from 1 thread (2601.283) and it was considerably worse that 2 threads. The 8 thread run only got worse (2963.615). This is due to rising contention of threads which have to fight over the hardware.
#### GPU Limit
GPU does a lot of arithmetic in parallel, bringing the 100-step training time down from the CPU's 486291.9 ms to just 17651.6 ms. However, GPUs are ultimately limited by "data that has to move". If a workload is highly sequential (like a loop where step 2 depends on step 1), or if the data payload is tiny, the latency of moving data back and forth between the CPU and GPU memory will cost more time than the parallel math saves.
<!--/answer-->

**What you would measure next.** One experiment this phase did not run that would sharpen the
answer, and what result would change your mind. (~50 words)

<!--answer:next_experiment-->
I would test GPU training performance across varying batch sizes (e.g., 1, 16, 128). This would expose the exact point where "data that has to move" becomes the bottleneck. If a batch size of 1 runs slower on the GPU than the CPU, it proves that data transfer overhead destroys the GPU's advantage when the parallel workload is too small.
<!--/answer-->

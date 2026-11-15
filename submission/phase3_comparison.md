# Phase 3 — Comparison Writeup

Copy this file to `submission/phase3_comparison.md`, fill in every answer slot, and commit it:

```bash
cp phase-3-mapreduce-spark/comparison_template.md submission/phase3_comparison.md
```

**How to fill it in.** Each answer sits between a pair of `<!--answer:...-->` markers. Replace
the `TODO` line with your answer — **leave the markers themselves untouched**, they are how the
grader finds your answers. Anything you write outside the markers is ignored, so add extra
prose, tables or images freely.

Numbers in section 1 must **match `submission/phase3_report.json`** — copy them across, do not
retype from memory; they are checked against it.

---

## 1. Facts from your runs

Numbers only (e.g. `12`, `20.3`, `0.041`).

| | Value |
|---|---|
| Map tasks in the cloud job (`mapreduce.num_splits`) | <!--answer:num_map_tasks-->12<!--/answer--> |
| Reduce tasks in the cloud job (`mapreduce.num_reducers`) | <!--answer:num_reduce_tasks-->4<!--/answer--> |
| Cloud MapReduce wall time, seconds (`mapreduce.cloud_elapsed_s`) | <!--answer:cloud_elapsed_s-->44.9<!--/answer--> |
| Local single-process wall time, seconds (`mapreduce.local_elapsed_s`) | <!--answer:local_elapsed_s-->0.008<!--/answer--> |
| Spark wall time for the `collect`, seconds (`tfidf.spark_elapsed_s`) | <!--answer:spark_elapsed_s-->4.2<!--/answer--> |
| Number of **stages** in the Spark job (read off notebook 2b / 3a) | <!--answer:num_stages-->4<!--/answer--> |
| Task **retries** you counted in your `--chaos` run (0 if none happened) | <!--answer:chaos_retries-->6<!--/answer--> |

**Explain the timings.** The three wall times above cover the same 60 documents, but not the
same job: the single-process run and the cloud MapReduce are *the same word count*; Spark's
time is for *TF-IDF*, which is more work (two `reduceByKey`s and a `join`). Rank the three and
explain what each is spending its time on. Say which comparison is like-for-like, and what the
Spark number — a heavier job, on one machine — tells you about where the cloud job's time goes.
(~80 words)

<!--answer:timing_explanation-->
The ranking from fastest to slowest is `Local MapReduce(0.008s) < Spark in Colab (4.2s) < Cloud MapReduce(44.9s)`. In terms of the goal of the job the local and cloud MapReduce compute the same thing. In terms of strategy, the Cloud MapReduce and Spark use parallel computation, while Local MapReduce does everything sequentially. Although there is another distinction cloud MapReduce uses inter-node parallelism, while the Spark job runs on the same node across multiple CPU cores.
The Spark job spends a lot of time on local task scheduling and writing & reading local disk shuffle files (as seen in `notebook.ipynb` in cell *3a*)
<!--/answer-->

**What the counts tell you.** From your stage count: how many shuffles did the Spark job have,
and which operations in `spark_tfidf.py` caused them? From your retry count: roughly what
fraction of the 16 task attempts was retried, and is that what `--chaos 0.3` should produce?
(~50 words)

<!--answer:counts_interpretation-->
The number of shuffles in the Spark job is 3 with one being used both for the join and the `doc_freq(tf)` call.
First shuffle was caused by the `reduceByKey` in `term_freq()`. This is the one that is used twice: once for the mapping in `doc_freq()` and once for the join.
The second shuffle was caused by `reduceByKey` in `doc_freq()`.
The third shuffle was caused by the join in `build_tfidf_rdd()`.

The retry count is 6, making the total attempts 16 + 6 = 22. The ration of errors to succesful runs is `6/22 = 0.27` which is close to `0.3`.
<!--/answer-->

---

## 2. Spark: transformations, actions, lineage

**Transformations vs actions.** Go through `spark_tfidf.py` and the notebook's Spark cells.
Name each RDD operation and say whether it is a transformation or an action. What happened
when you ran `build_tfidf_rdd` — and what happened when you ran `collect`? (~60 words)

<!--answer:transformations_vs_actions-->
All `flatMap`, `reduceByKey`, `map` operations in `term_freq()`, `doc_freq()` and `build_tfidf_rdd()`, as well as the `join` from ``build_tfidf_rdd()` are transformations which are lazily executed. That means they will be executed only when they are needed, which is when `collect()` is called in the notebook. `collect()` is an action. 
Running `build_tfidf_rdd()` only formed the DAG execution graph, then when `collect()` was called the actual job was executed on workers.
<!--/answer-->

**Lineage and recovery.** Using the lineage you printed in 2b and the timeline in 3a: if the
worker holding one output partition of the *first* `reduceByKey` died, what would Spark have
to recompute, and what could it reuse? Name the stage or shuffle boundary where the recovery
starts. (~50 words)

<!--answer:lineage_recovery-->
The output of the first `reduceByKey` (the one in `term_freq()`) is used both by stage 1 (for the `map` in `doc_freq()`) and stage 2 (for the `join` in `build_tfidf_rdd()`). In both cases if the worker holding the partition crashes, it's task has to be restarted on another worker. Any partitions processed by other workers can still be used, any partitions mapped by the crashed worker will have to be recalculated in order to not skew the results.
<!--/answer-->

---

## 3. Your cloud MapReduce, mapped onto Hadoop

Name the GCP service or file that played each role (one line each):

- **JobTracker** (schedules tasks, waits for the map phase, retries failures):
  <!--answer:role_jobtracker-->Cloud Workflows<!--/answer-->
- **Workers** (run your map and reduce code):
  <!--answer:role_workers-->Cloud Run Functions<!--/answer-->
- **HDFS** (holds inputs, shuffle files, outputs):
  <!--answer:role_hdfs-->Google Cloud Storage Bucket<!--/answer-->
- **Partitioner** (decides which reducer owns a key):
  <!--answer:role_partitioner-->Cloud Run Functions (via `partition()`)<!--/answer-->

**The barrier.** There is no explicit "wait for all mappers" step in `workflow.yaml`. Where,
exactly, is the barrier between the map and reduce phases — which construct provides it?
(~30 words)

<!--answer:barrier_location-->
The barrier between the map phase and the reduce phase is provided natively by the `workflow.yaml` format which does not execute any branches below the current one until it has finished.
<!--/answer-->

**Idempotence.** The workflow retries a task that failed. Why is that safe with the worker as
written, and what would go wrong if `run_map` *appended* its pairs to the shuffle file instead
of overwriting it? (~60 words)

<!--answer:idempotence-->
The worker is stateless: it just reads it's part of the input, does it's mapping and writes it's output to a uniquely named file. If `run_map` appended its pairs to the shuffle files, then in the scenario in which a worker has crashed, the worker taking over his task from the beginning appends the same entries the crashed worker has managed to write to the file again resulting in skewed results (doubled counters for the duplicate words).
<!--/answer-->

**The chaos run.** What did you see in the execution log and in Logs Explorer when you ran
with `--chaos 0.3`? Did the job still succeed, and was the final answer still identical to the
local reference? (~50 words)

<!--answer:chaos_observations-->
The job still succeded and the final answer was still identical to the local reference when running with `--chaos 0.3`. This is because at every failure, the task is retried up to 5 times. This guaranteed that each task was finalized even if there were failures. Also the mentions from the previous question allowed to output to stay consistent even in case of failures.
<!--/answer-->

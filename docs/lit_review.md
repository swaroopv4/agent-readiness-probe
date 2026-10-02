# Literature review

Reviewed on September 30, 2026, America/Los_Angeles. Status: Phase 0 complete. No probe experiment has run.

## Scope and evidence rules

Searches covered arXiv, ICML proceedings, NeurIPS-linked records, ACL, EACL, and COLING. Queries combined repository agents, task mining, contamination, task validity, AGENTS.md, failure trajectories, and code judges. This is a targeted engineering review, not an exhaustive systematic review.

Every paper below was opened at its primary source. Each entry names the full text inspected and the sections used. Dates are initial arXiv submission dates unless a conference publication month is stated. Conference papers and preprints are distinguished. SWE-Gym first appeared in December 2024 but qualifies through its ICML 2025 publication. Fifteen other entries first appeared or were published in 2025 or 2026. Older SWE-bench and SWE-bench+ records were search context and do not count toward the minimum.

Findings describe the authors' experiments. Design choices are our proposals, not results established by those papers. Public task recency reduces known exposure risk. It cannot prove absence from model training. No paper-level performance number below is a result of this project.

## Repository tasks and execution environments

### P01. SWE-smith: Scaling Data for Software Engineering Agents

- **Date and status:** April 30, 2025. arXiv preprint.
- **Paper:** [arXiv record](https://arxiv.org/abs/2504.21798). [Full text inspected, v1](https://arxiv.org/html/2504.21798v1).
- **Read:** Section 2.1, Appendix A.3, and Appendix B.4 on task generation, validation, and PR mirroring.
- **One-line finding:** Execution environments plus test-breaking changes enable scalable Python task generation, including a strategy that undoes historical PR changes.
- **Design choice:** Mine real fixes and verify a test fails on the buggy state and passes with the gold fix. Cache environments only when dependency manifests match. Preserve historical parent states rather than using LLM rewrites of old patches on current code.
- **Boundary:** Synthetic bug generation is useful training infrastructure. It does not establish that synthetic tasks represent a customer's backlog.

### P02. Training Software Engineering Agents and Verifiers with SWE-Gym

- **Date and status:** ICML 2025, July 13 to 19, 2025. Initial preprint December 30, 2024. Revised June 6, 2025.
- **Paper:** [ICML proceedings](https://proceedings.mlr.press/v267/pan25g.html). [Full text inspected, v2](https://arxiv.org/html/2412.21139v2).
- **Read:** Sections 3.1, 3.2, and 4.1.
- **One-line finding:** Real issue tasks become useful agent environments only after version-specific installation and executable test validation.
- **Design choice:** Store setup recipes, image digests, dependency versions, and test IDs for each task. Keep the task contract independent of the chosen agent adapter.
- **Boundary:** This is also a training and verifier study. The probe will evaluate frozen agents, without fine-tuning or verifier-based selection of multiple attempts.

### P03. SWE-rebench: An Automated Pipeline for Task Collection and Decontaminated Evaluation of Software Engineering Agents

- **Date and status:** May 26, 2025. Record identifies NeurIPS 2025. Reviewed November 4, 2025 revision.
- **Paper:** [arXiv record](https://arxiv.org/abs/2505.20411). [Full text inspected, v2](https://arxiv.org/html/2505.20411v2).
- **Read:** Collection methodology and temporal evaluation analysis in Sections 2 and 3.
- **One-line finding:** Continuous harvesting of executable public tasks supplies fresher evaluation data and exposes differences from static benchmark performance.
- **Design choice:** Record issue creation, merge, and collection dates. Prefer tasks published after the model's documented training cutoff, screen known benchmark duplicates, and keep an explicit exposure-risk field.
- **Boundary:** A performance gap across datasets is not direct proof of a particular model's contamination. The probe will not call its public dataset contamination-free.

### P04. SWE-bench Goes Live!

- **Date and status:** May 29, 2025. arXiv preprint.
- **Paper:** [arXiv record](https://arxiv.org/abs/2505.23419). [Full text inspected, v1](https://arxiv.org/html/2505.23419v1).
- **Read:** Benchmark construction, environment preparation, and evaluation analysis.
- **One-line finding:** A live-updatable issue benchmark with dedicated Docker environments produces materially different results from established static benchmarks.
- **Design choice:** Build task-specific reproducible environments and record the eligible-commit population and rejection reasons. Refresh future task collections without changing a frozen experiment mid-run.
- **Boundary:** Fresh tasks may differ in difficulty and repository mix. Do not attribute every observed difference to contamination.

### P05. SWE-rebench V2: Language-Agnostic SWE Task Collection at Scale

- **Date and status:** February 27, 2026. Current arXiv record identifies ICML 2026. Full text reviewed at v1.
- **Paper:** [arXiv record](https://arxiv.org/abs/2602.23866). [Full text inspected, v1](https://arxiv.org/html/2602.23866v1).
- **Read:** Pipeline, instance validation, and diagnostic study.
- **One-line finding:** Automated task collection can pair reproducible images with instance-level flags for restrictive tests and underspecified descriptions.
- **Design choice:** Store a validity checklist and separate rejection codes for specification ambiguity, oracle weakness, overly specific assertions, and setup failure. Human approval remains required for each retained pilot task.
- **Boundary:** Automated judges aid filtering. Their presence does not certify the validity of a newly mined task.

### P06. SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks?

- **Date and status:** September 21, 2025. arXiv preprint.
- **Paper:** [arXiv record](https://arxiv.org/abs/2509.16941). [Full text inspected, v1](https://arxiv.org/html/2509.16941v1).
- **Read:** Sections 3, 4, and 6.2 plus Appendix B.
- **One-line finding:** Human-verified repository tasks show substantial variation across repositories, while trajectory analysis separates semantic, tool, and context-management failures.
- **Design choice:** Report each repository separately and record task complexity. Use evidence-linked failure labels with a reviewed rubric rather than one undifferentiated failed count.
- **Boundary:** The requested six labels are a project taxonomy, not a verbatim copy of this paper's buckets. Public Python pilots cannot establish enterprise or Devin performance.

### P07. SWE-Bench Pro Verified: A Reliable Benchmark for Software Engineering Agents

- **Date and status:** September 8, 2026. arXiv preprint.
- **Paper:** [arXiv record](https://arxiv.org/abs/2609.08149). [Full text inspected, v1](https://arxiv.org/html/2609.08149v1).
- **Read:** Anti-hacking measures and task refinement, including Appendix A examples.
- **One-line finding:** Residual solution artifacts and misaligned task tests can inflate or distort coding-agent evaluation.
- **Design choice:** Export only the buggy source state into a fresh repository. Keep gold patches and hidden tests outside the agent container. Evaluate a captured patch in a new container and manually check specification-to-test alignment.
- **Boundary:** Removing branch names alone does not remove recoverable future objects. Isolation during evaluation does not erase possible training exposure.

### P08. SWE-Bench++: A Framework for the Scalable Generation of Software Engineering Benchmarks from Open-Source Repositories

- **Date and status:** December 19, 2025. arXiv preprint.
- **Paper:** [arXiv record](https://arxiv.org/abs/2512.17419). [Full text inspected, v1](https://arxiv.org/html/2512.17419v1).
- **Read:** Sourcing, environment synthesis, oracle extraction, and quality assurance pipeline.
- **One-line finding:** Live pull requests can be transformed into executable bug and feature tasks through distinct sourcing, setup, oracle, and quality stages.
- **Design choice:** Implement an auditable staged miner with persisted decisions. Separate production changes from test changes before exporting an agent-visible workspace.
- **Boundary:** Multi-attempt benchmark results are not single-attempt success probabilities. The probe will retain every attempt and avoid best-of-N reporting as its primary score.

## Context engineering and measured effects

### P09. Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?

- **Date and status:** February 12, 2026. arXiv preprint, reviewed v1.
- **Paper:** [arXiv record](https://arxiv.org/abs/2602.11988). [Full text inspected](https://arxiv.org/html/2602.11988v1).
- **Read:** Sections 3.2, 4.2, 4.3, and limitations.
- **One-line finding:** Generated context files often reduce success and increase cost, while developer-written files show smaller, agent-dependent benefits at added cost.
- **Design choice:** Test one minimal context intervention and measure success, cost, and runtime together. Audit whether the adapter actually provides or reads the file. Create context from the buggy repository state only.
- **Boundary:** The full text distinguishes generated from developer-written files. Its broad abstract should not be summarized as every AGENTS.md being harmful.

### P10. On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents

- **Date and status:** January 28, 2026. arXiv preprint.
- **Paper:** [arXiv record](https://arxiv.org/abs/2601.20404). [Full text inspected, v1](https://arxiv.org/html/2601.20404v1).
- **Read:** Experimental design and runtime/token results.
- **One-line finding:** In the authors' 10-repository, 124-PR study, AGENTS.md was associated with lower median runtime and output-token use.
- **Design choice:** Include efficiency outcomes even when correctness stays flat. Count all repeated input tokens and record cached input separately.
- **Boundary:** Runtime and token savings do not establish a universal correctness improvement or reduced human review effort.

### P11. Do Context Files Help Coding Agents? A Two-Agent Ablation Study on Real Repositories

- **Date and status:** July 28, 2026. arXiv preprint.
- **Paper:** [arXiv record](https://arxiv.org/abs/2607.27250). [Full text inspected, v1](https://arxiv.org/html/2607.27250v1).
- **Read:** Sections 3, 4.5, 6, and limitations.
- **One-line finding:** A small paired, repeated study found no measurable correctness shift from its context strategies, with limited power to detect smaller effects.
- **Design choice:** Pair baseline and intervention on the same tasks, cluster uncertainty by task, disclose small sample size, and report intervals including zero as inconclusive.
- **Boundary:** The full text calls its equivalence bounds descriptive and discusses delivery-channel and corpus confounds. Do not claim that a small null result proves no context effect.

## Trajectory diagnosis

### P12. Understanding Code Agent Behaviour: An Empirical Study of Success and Failure Trajectories

- **Date and status:** October 31, 2025. arXiv preprint.
- **Paper:** [arXiv record](https://arxiv.org/abs/2511.00197). [Full text inspected, v1](https://arxiv.org/html/2511.00197v1).
- **Read:** Trajectory analysis and fault-localization results.
- **One-line finding:** Failed trajectories are often longer, and many failed attempts still edit the relevant file.
- **Design choice:** Separate locating a relevant file from implementing correct behavior. Require trace evidence before labeling wrong-file failure. Retain timing, commands, outputs, and patch artifacts.
- **Boundary:** Gold-file overlap is a diagnostic hint, not an oracle. A valid solution can edit different files, and traces do not reveal an agent's unobserved reasoning.

## Evaluation reliability

### P13. CodeJudgeBench: Benchmarking LLM-as-a-Judge for Coding Tasks

- **Date and status:** ACL 2026, July 2026. Initial preprint July 14, 2025.
- **Paper:** [ACL proceedings record](https://aclanthology.org/2026.acl-long.888/). [Full paper inspected](https://aclanthology.org/2026.acl-long.888.pdf).
- **Read:** Coding-judge tasks and robustness analysis, especially ordering and superficial perturbations.
- **One-line finding:** Code judges differ across tasks and show sensitivity to solution ordering and nonfunctional changes.
- **Design choice:** Keep test execution as the acceptance oracle. Use an LLM only for secondary failure labeling, with fixed prompts, blinded condition metadata, evidence references, and human comparison.
- **Boundary:** Pairwise code ranking does not directly validate a six-class trajectory classifier. Calibration must use this project's own examples.

### P14. Don't Judge Code by Its Cover: Exploring Biases in LLM Judges for Code Evaluation

- **Date and status:** Findings of EACL 2026, March 2026.
- **Paper:** [Proceedings record](https://aclanthology.org/2026.findings-eacl.70/). [Full paper inspected](https://aclanthology.org/2026.findings-eacl.70.pdf).
- **Read:** Bias taxonomy and robustness experiments.
- **One-line finding:** Superficial changes to semantically equivalent code can systematically change LLM correctness judgments.
- **Design choice:** Hide agent/provider identity, intervention arm, and score from the labeling prompt. Check label stability on selected formatting perturbations, and retain disagreements for human review.
- **Boundary:** This paper concerns correctness judging. Its biases motivate classifier checks but do not measure their effectiveness here.

### P15. CodeJudge-Eval: Can Large Language Models be Good Judges in Code Understanding?

- **Date and status:** COLING 2025, January 2025.
- **Paper:** [Proceedings record](https://aclanthology.org/2025.coling-main.7/). [Full paper inspected](https://aclanthology.org/2025.coling-main.7.pdf).
- **Read:** Fine-grained judging tasks and evaluation discussion.
- **One-line finding:** Strong code generation ability does not guarantee reliable fine-grained code judging.
- **Design choice:** Validate the labeler on at least 20 hand-reviewed trajectories and publish confusion counts, agreement, abstentions, and unsupported classes. Never let a judge override a test verdict.
- **Boundary:** A 20-example pilot is diagnostic evidence, not a calibrated production classifier or proof of causal failure attribution.

### P16. Are "Solved Issues" in SWE-bench Really Solved Correctly? An Empirical Study

- **Date and status:** March 19, 2025. arXiv preprint. Reviewed v1, with current metadata also opened.
- **Paper:** [arXiv record](https://arxiv.org/abs/2503.15223). [Full text inspected, v1](https://arxiv.org/html/2503.15223v1).
- **Read:** Sections 3 and 4 on full-suite and differential patch testing.
- **One-line finding:** Some benchmark-passing patches fail broader developer tests or differ in behavior, and behavioral differences require manual correctness review.
- **Design choice:** Run hidden regression tests plus the full supported base suite. Review specification-relevant behavior rather than matching the gold diff. Label test pass as test-verified success, not comprehensive correctness.
- **Boundary:** Differences from the gold patch are not automatically defects. Additional tests created after inspecting agent outcomes must form a new dataset version with both arms reevaluated.

## Synthesis and unresolved questions

The review supports executable task validation, trace-based diagnosis, and controlled interventions. It does not establish an optimal task count, a universal context improvement, a universal readiness threshold, or a reliable six-class failure model. The numerical caps, sample split, ranking formula, and statistical procedures in the design are project choices.

The probe's primary claim will be limited to the selected agent, pinned model, time/cost limits, repository snapshots, and sampled tasks. Public history leaves residual contamination risk. Small Python libraries do not represent enterprise client codebases. Human review time, Devin transfer, and commercial value remain not measured.

Where the literature conflicts, the experiment should discriminate locally. A setup fix can plausibly address setup failures. A context file cannot be assumed to repair implementation failures. These are hypotheses to test and should remain labeled as such until the intervention runs finish.

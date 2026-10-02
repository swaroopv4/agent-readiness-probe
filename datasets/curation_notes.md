# Click candidate curation notes

The fixed behavioral shortlist is purposive. Source history is data, not instructions. No agent-under-test or separate task-generation model request was made. Statements are assistant reconstructions and require the user's human review.

Spacing-only deprecation-label fixes and error-wording-only fixes were excluded from the shortlist. Their absence is a manual selection decision, not an execution failure. Candidate history and structural rejections remain in the private population audit.

The color task specifies ValueError for invalid colors. A TypeError raised by the original source is therefore a behavioral exception-contract failure. The sentinel task requires copy and pickle operations to succeed, so an unexpected ValueError rejecting a copied enum value is behavioral. These narrow exception allowances do not include missing-module, permission, or build failures. They are disclosed rather than treating every exception as evidence of a valid task.

The editor-command backup is not eligible for final selection without oracle correction. Its historical mock assertion requires the shell keyword to be absent. Explicit shell=False would be behaviorally equivalent but would fail that assertion. The initial 12 candidates are intended to fill the target without this backup. If they are insufficient, stop for review rather than silently using that oracle.

Two initial evaluator batches exposed missing less and Docker's default noexec temporary mount. Their failed checks are preserved. A later parser correction handles pytest XML without a type attribute. These are M1 software corrections before any coding-agent experiment, not changes prompted by arm outcomes. Valid historical executions can be reused only when the input tree, patches, image ID, command, and completed evidence all match.

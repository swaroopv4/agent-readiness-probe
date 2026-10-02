# M2 status

October 1, 2026. M2 is incomplete. Live work stopped after Docker task operations timed out, as required by the user. No development smoke completed and no confirmation task was launched. Incremental paid API spend is $0. Token usage and dollar cost are not measured.

## Preserved launches

| Launch | Result | Agent task-tool calls |
|---|---|---|
| m2-smoke-001, click-002 | CLI app-server initialization denied before inference | 0 |
| m2-smoke-002, click-002 | OpenAI WebSocket certificate validation failed with UnknownIssuer | 0 |
| m2-smoke-003, click-002 | Docker readiness exec timed out after 10 seconds and forced removal timed out after 30 seconds. CLI never launched | 0 |

The first two CLI invocations are infrastructure aborts. Preserve them in the operational ceiling of 48 scored attempts plus two infrastructure aborts. They supply no task success score. The third launch stopped during container setup and did not invoke Codex. No evaluator execution was performed in M2.

The post-stop read-only check returned Docker engine 28.5.1 with Linux containers and no remaining arp task container. The engine answered that check, but task execution and cleanup had timed out. No Docker restart or further live attempt was made after the stop.

## Implemented partial adapter

`arp/adapters.py` provides the prepare, run, cancel, and collect interface for Codex exec and an unsupported Devin stub. It requires saved ChatGPT authentication, strips provider keys and injected endpoints, requests the built-in OpenAI provider, disables web search and host execution tools, and retains JSONL events and returned usage. Dollar cost is always not measured.

A host-owned TLS CONNECT proxy permits only api.openai.com, chatgpt.com, and auth.openai.com on port 443. Native Windows elevated sandbox networking blocks direct connections and permits the two loopback ports used for the proxy and task-tool broker. The agent's task tools run in a non-root Docker container with network none, dropped capabilities, a read-only root, two CPU cores, 3 GiB memory, and bounded writable tmpfs. The container mounts only the isolated historical parent snapshot and a read-only tool worker. It has no credential store, Docker socket, evaluator artifacts, or original Git history.

The trusted CLI reads the original saved authentication. Authentication was not copied, displayed, or mounted into the task container. Its runtime state and logs are redirected into the transport directory. The Windows transport profile permits CLI writes to the existing installation identifier and arg0 helper directory, while the credential store remains read-only. These are trusted CLI operations. The model has no host execution environment.

The matching 0.153.1 source establishes that CODEX_EXEC_SERVER_URL=none omits local execution environments. Shell, apply_patch, and image tools are gated on an available execution environment. MCP exposes only read, write, and shell scoped to one offline task container. This internal environment flag requires version pinning and revalidation for a new CLI release. The [matching environment-provider source](https://github.com/openai/codex/blob/rust-v0.153.1/codex-rs/exec-server/src/environment_provider.rs) and [tool gating source](https://github.com/openai/codex/blob/rust-v0.153.1/codex-rs/core/src/tools/spec_plan.rs) support this configuration.

The configured model is GPT-5.5 with medium reasoning, which is listed in the CLI's bundled catalog and supports ordinary tools without host code execution. Requested settings are recorded. The aborted JSONL logs do not independently report a served-model identity. No model or provider fallback was made.

## Checked boundaries and limits

The [tracked summary](../results/m2_summary.json) records the observed probes and host-only evidence paths. ChatGPT's metadata endpoint returned HTTP 401 without authentication through the allowed tunnel. A non-OpenAI domain received proxy HTTP 403. Direct-IP access received Windows socket permission denial. Inside the task container, external network access was unreachable, identity was 1000:1000, history contained one fresh commit with no remotes, and credentials, hidden evidence, and the Docker socket were absent.

Read/write tools reject paths outside /workspace. A shell timeout killed a running sleep command. Cancellation terminated a running native sandbox process. Core tests cover destination validation, environment injection, usage-limit classification, MCP authentication and scope, immutable task files, production patch capture, and the zero-dollar adapter policy.

The runner fixes a five-attempt development plan, 900 seconds of agent wall time, 120 seconds per shell command, and 300 seconds for offline evaluation. A watchdog cancels the active CLI if Docker availability fails. Completed poor outcomes are retained. Rate-limit and quota errors stop the batch without provider switching. Source capture validates production paths and preserves immutable public tests and task files. Evaluation uses the frozen historical buggy snapshot with its trusted oracle in a fresh network-none container. No gold patch is read or applied by M2.

## Certificate correction and remaining work

The second invocation could not validate the WebSocket issuer inside the restricted Windows account. The CLI's supported CODEX_CA_CERTIFICATE path now points to a PEM bundle of 55 public server-auth CA certificates from the existing Windows trust store. No private keys or login material are included. TLS and hostname verification stay enabled. The [matching custom-CA source](https://github.com/openai/codex/blob/rust-v0.153.1/codex-rs/http-client/src/custom_ca.rs) applies this supported setting to both HTTP and WebSocket transports. A read-only CLI catalog request succeeds with this configuration. Its live WebSocket path remains unverified because the next task container setup timed out.

The remaining M2 work is to verify the corrected live transport, complete five real development attempts, evaluate captured submissions offline, audit the run evidence, and commit the completed milestone. The fixed order is click-002 repeat 0, click-003 repeat 0, click-009 repeat 0, click-010 repeat 0, and click-002 repeat 1. The two aborted CLI launches must stay in the operational ledger. Additional infrastructure aborts would require revisiting the current ceiling before more launches.

M1-v7 remains committed with all 12 tasks accepted by Swaroop. Its tests, gold artifacts, and frozen split are unchanged. Statements were aligned to hidden assertions before agent work and are more precise than typical tickets. The sample is small, confirmation intervals will be wide, and no current agent-performance claim is supported. M3 and optional M6 have not started.

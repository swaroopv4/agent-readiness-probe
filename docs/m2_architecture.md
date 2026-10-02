# M2 Linux architecture

October 1, 2026, America/Los_Angeles. The project is now C:\arp. This architecture supersedes the Windows sandbox, loopback tunnel, and host MCP task broker. M1-v7 remains the accepted dataset at commit f000b0b.

## Agent and authentication

The agent image extends the validated M1 evaluator image. Before inference the runner verifies that the agent's filesystem layers begin with the frozen evaluator's layers. Node, the pinned Codex CLI 0.153.1 (including its matching bundled Linux Code Mode host), Git, and ripgrep are added during environment preparation. Only the docker directory is sent as build context. The resulting immutable image ID and installed package inventory are recorded for each batch; apt package versions are recorded rather than assumed reproducible across later builds.

The host copies the accepted buggy task workspace and TASK.md into a fresh input directory, excluding every .git directory and rejecting links. The agent gets that input read-only and works in a bounded private /workspace tmpfs. No hidden test delta, gold patch, private artifact directory, experiment manifest, original Git history, host repository, or Docker socket is mounted.

The user's existing Codex auth.json is mounted read-only at /auth/auth.json, with a runtime symlink at /codex/auth.json. CODEX_HOME is a private tmpfs. The container runs as 1000:1000 with a read-only root, all capabilities dropped, no privilege escalation, two CPU cores, 3 GiB memory, a PID limit, and bounded writable tmpfs. It is removed after every attempt, including failed attempts. The runner logs mount paths and login status, never credential bytes.

**Accepted limitation: credentials are visible inside the ephemeral agent container.** Read-only prevents modifying the host file; it does not hide its contents from agent code. An agent can read the saved login and use it against allowed OpenAI endpoints. This is the limitation the user explicitly accepted. No authentication file is copied into the project, image, Git, or evidence store. API-key authentication and provider fallback are rejected.

Codex runs with a clean configuration, forced ChatGPT authentication, the built-in OpenAI provider, web search disabled, no external MCP servers, and browser, computer-use, plugin, memory, and delegation features disabled. Its matching bundled Code Mode host remains enabled for Linux execution. Codex's inner sandbox is bypassed because Docker supplies the isolation boundary; there are no native Windows task tools.

## Network

The agent is connected to one Docker internal network on 192.0.2.0/24. External DNS forwarding is disabled by pointing its upstream DNS at loopback. The proxy address is passed as an IP, so resolving a proxy hostname is unnecessary. The proxy is also connected to a separate ordinary Docker egress bridge. No ports are published, forwarding is disabled in the proxy namespace, and the proxy listens only on its internal interface.

The small Python proxy accepts CONNECT only, for exact lowercase api.openai.com, chatgpt.com, and auth.openai.com hostnames on port 443. It rejects literal IPs, other ports, suffix lookalikes, and all other domains before DNS resolution. Every resolved upstream address must be public. It does not inspect TLS or log authorization headers. Native TLS certificate and hostname verification remain enabled.

A fresh preflight checks the inspected mounts, identity, capabilities, network membership, and provider environment, then proves:

- github.com and pypi.org are rejected with proxy CONNECT 403.
- A literal IP is rejected through the proxy; direct connections to 1.1.1.1 and 8.8.8.8 are unreachable.
- External DNS cannot resolve github.com.
- The Codex metadata endpoint is reachable with verified TLS; its unauthenticated response is 401.
- Saved login reports ChatGPT authentication and the credential mount is read-only.
- A live Codex request can use Linux execution tools to write and read a probe file, with successful command events and the expected final reply.

Only after every check passes may the five task attempts start. There is no Windows firewall rule, public tunnel, host tool server, or alternate agent exit path.

## Model, evaluation, and accounting

The clean CLI selected gpt-6-astra with low reasoning through the user's saved login. The rollout identifies the effective client model; its fetched catalog establishes default reasoning when the rollout omits that field. Both settings are then explicit CLI overrides for all five development smokes. Rollout metadata and returned usage are preserved. A separately verified backend served-model identity is not exposed and is not claimed. The [official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) documents model reasoning and web_search=disabled.

The agent container is removed before evaluation. The host collects source files with a trusted Python collector, validates immutable task files, and generates a production-only patch against the frozen parent snapshot. The evaluator remains the validated image, a fresh non-root, read-only, network-none container. Frozen hidden tests are present only in its input, and the submitted production patch is applied there. The M2 task runner does not read or apply gold patches; the separate M1 integrity audit verifies their stored hashes. Evaluator test behavior and dependencies are unchanged; host cleanup is now bounded.

The fixed development order is click-002 repeat 0, click-003 repeat 0, click-009 repeat 0, click-010 repeat 0, and click-002 repeat 1. Poor task outcomes are retained. Infrastructure failures remain separately recorded, including the earlier two Windows CLI aborts, the setup failures, and the disabled-tool-runtime launches. Live connectivity/tool probes consume subscription capacity and are counted separately from task attempts. Additional later experiment accounting must include this diagnostic overhead.

Incremental paid API spend is capped at $0. No API key, purchased capacity, paid judge, provider switch, or cloud machine is used. Returned usage counters are recorded; dollar cost stays not measured. The agent has a 900-second wall cap and the evaluator has a 300-second cap. The prompt asks for 120-second task commands; native CLI command timeout behavior is not claimed as an independently enforced 120-second security boundary. Docker control and cleanup commands have bounded waits. Two Docker timeouts stop further live operations; usage-limit errors stop immediately. No provider fallback or silent retry of a completed task is allowed.

M2 stops for the user's review. Confirmation tasks, M3, optional M6, and outreach remain outside this run.

## Reproduction

From C:\arp with Python 3.11+, the saved ChatGPT auth file, and a working Docker Linux engine:

```powershell
docker image inspect arp-m1-evaluator:v1
docker build -f docker/Dockerfile.agent -t arp-m2-agent:linux-v1 docker
docker build -f docker/Dockerfile.proxy -t arp-m2-proxy:linux-v1 docker
python -m arp.m2 --output artifacts/private/m2-linux-fresh-001
```

The existing evaluator tag must identify sha256:506974e3505483d01d749cfc2cffc6bae2e3d375f2f5ff69d241bc353b630cb7. Use a new output directory each time. The runner verifies ancestry and pins the built image IDs. Preflight fails closed if the reserved internal subnet conflicts with another Docker network. Reproduction uses fresh subscription capacity; it is not authorized as an automatic repeat after the review checkpoint.


Primary coordinator: Agent Archon

Agent Archon is the central mission orchestrator. It interprets user intent, maintains mission context, delegates bounded tasks, coordinates specialist agents, and presents consolidated findings.

Archon does not independently authorize consequential actions, override deterministic policy controls, or treat its own conclusions as verified evidence.

Specialist agents

- Agent Aleph — World Intelligence: Maintains the digital-world model, entity relationships, dependency information, and information-state labels.
- Agent Mneme — Intelligence and Memory: Retrieves relevant mission history, research records, and evidence while preserving provenance and uncertainty.
- Agent Melete — Research Strategy: Generates hypotheses, compares explanations, and proposes research experiments.
- Agent Protos — Simulation Engineering: Executes deterministic, scoped simulations and records their inputs and outputs.
- Agent Kratos — Policy Enforcement: Enforces predefined action restrictions, execution limits, and policy decisions through deterministic controls.
- Agent Exousia — Authorization Gateway: Checks approval records and action permissions before an operation is permitted to proceed.
- Agent Origo — Independent Verification: Checks outcomes against explicit assertions and evidence independently of the component that produced those outcomes.

Coordination contract

Every agent interaction must identify the mission, requested operation, permitted scope, expected output schema, and relevant evidence references. Results must include status and relevant uncertainty or failure information.

Agent-generated proposals are untrusted until validated. Consequential actions require independent policy evaluation and any approval mandated by the action's risk class. Verification must not rely solely on the executing agent's report.

Initial implementation boundary

The first milestone implements the mission coordinator interface and only the specialist capabilities required for the simulated authentication-failure investigation. Names may initially represent modules rather than separate autonomous LLMs.

Introduce separate model-backed agents only when they provide measurable benefits in capability, isolation, reliability, or evaluation. Each role must have explicit permissions, testable responsibilities, and documented failure behavior.

All agent roles are proposed architectural components until implemented and tested.

~~~~
flowchart TD
    U["You — Research Director"]
    A["Agent Archon — Chief Orchestrator"]

    subgraph S["Specialist Agents"]
        AL["Aleph — Digital World"]
        MN["Mneme — Memory & Evidence"]
        ME["Melete — Research Planning"]
        PR["Protos — Simulation"]
    end

    subgraph G["Authorization & Safety"]
        K["Kratos — Policy Enforcement"]
        EX["Exousia — Authorization Gateway"]
    end

    O["Origo — Independent Verification"]
    W["Updated Digital World"]
    
    U --> A
    A --> AL
    A --> MN
    A --> ME
    A --> PR

    AL --> K
    MN --> K
    ME --> K
    PR --> K

    K --> EX
    EX --> O
    O --> W
    W --> A

    style A fill:#243b55,color:#ffffff,stroke:#6ea8fe
    style O fill:#164e46,color:#ffffff,stroke:#52d6b5
    style EX fill:#5b4320,color:#ffffff,stroke:#e8bd65
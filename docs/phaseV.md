┌───────────────┐
│ Orchestrator  │   (Accept intent)
└───────┬───────┘
        │  intent event
        ▼
     Pub/Sub        ←────── delivery only
        │
        ▼
┌───────────────┐
│ Pipeline      │   (Decide next step)
│ Runner        │
└───────┬───────┘
        │  work instruction
        ▼
     Pub/Sub        ←────── delivery only
        │
        ▼
┌───────────────┐
│ Worker        │   (Do side-effects)
└───────┬───────┘
        │  fact: “work completed”
        ▼
     Pub/Sub        ←────── delivery only
        │
        ▼
┌───────────────┐
│ Pipeline      │   (Update state)
│ Runner        │
└───────────────┘


┌──────────────────────────┐
│        USER / CLIENT     │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  REQUEST INTAKE LAYER    │
│  (Control Plane)         │
│                          │
│  • Accepts user intent   │
│  • Validates input       │
│  • Assigns IDs           │
│  • Persists intent       │
│  • Responds immediately  │
│                          │
│  ❌ No long work          │
│  ❌ No retries           │
│  ❌ No side effects      │
└────────────┬─────────────┘
             │  "Start Job"
             ▼
┌──────────────────────────┐
│  JOB DECISION MAKER      │
│  (Execution Brain)       │
│                          │
│  • Knows job state       │
│  • Knows next step       │
│  • Enforces order        │
│  • Handles retries       │
│  • Detects completeness  │
│  • Survives restarts     │
│                          │
│  ❌ Does not fetch data  │
│  ❌ Does not serve users │
└────────────┬─────────────┘
             │  "Do this work"
             ▼
┌──────────────────────────┐
│  SIDE-EFFECT WORKERS     │
│  (Execution Units)       │
│                          │
│  • Fetch URLs            │
│  • Call external APIs    │
│  • Write evidence        │
│  • Perform compute       │
│                          │
│  ❌ No global knowledge  │
│  ❌ No job decisions     │
└────────────┬─────────────┘
             │  "Work done"
             ▼
┌──────────────────────────┐
│  DURABLE RECORDS         │
│                          │
│  • Job state             │
│  • Evidence              │
│  • Artifacts             │
│  • Audit logs            │
│                          │
│  (Single source of truth)│
└──────────────────────────┘

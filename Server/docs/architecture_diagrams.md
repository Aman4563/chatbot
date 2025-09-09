# Backend Architecture Diagrams

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph "Frontend"
        UI[React Frontend]
    end
    
    subgraph "FastAPI Backend"
        API[FastAPI Main App]
        CM[Conversation Manager]
        PM[Performance Monitor]
        CP[Connection Pool]
        RC[Response Cache]
    end
    
    subgraph "Agent System"
        AR[Agent Registry]
        OCA[Optimized Chat Agent]
        FA[File Agent]
        SA[Search Agent]
        IA[Image Agent]
    end
    
    subgraph "Tool System"
        LLMT[LLM Tools]
        FT[File Tools]
        WT[Web Tools]
        IT[Image Tools]
    end
    
    subgraph "Provider System"
        OR[Optimized Provider Registry]
        OP[OpenAI Provider]
        AP[Anthropic Provider]
        GP[Google Provider]
        MP[Mistral Provider]
    end
    
    subgraph "External Services"
        OAI[OpenAI API]
        ANT[Anthropic API]
        GOOG[Google API]
        MIST[Mistral API]
        WEB[Web Search APIs]
        IMG[Image Generation APIs]
    end
    
    UI --> API
    API --> AR
    API --> CM
    API --> PM
    
    AR --> OCA
    AR --> FA
    AR --> SA
    AR --> IA
    
    OCA --> LLMT
    OCA --> FT
    OCA --> WT
    OCA --> IT
    
    FA --> FT
    SA --> WT
    IA --> IT
    
    LLMT --> OR
    OR --> OP
    OR --> AP
    OR --> GP
    OR --> MP
    
    OP --> OAI
    AP --> ANT
    GP --> GOOG
    MP --> MIST
    
    WT --> WEB
    IT --> IMG
    
    PM --> CP
    PM --> RC
```

## 2. LangGraph Workflow for Optimized Chat Agent

```mermaid
graph TD
    START([User Request]) --> AI[Analyze Input]
    AI --> DAC[Determine Agent Collaboration]
    
    DAC --> |Collaboration Needed| COORD[Coordinate with Agents]
    DAC --> |Direct Processing| RTT[Route to Tools]
    
    RTT --> |Files| PFP[Process Files Parallel]
    RTT --> |Search| WSP[Web Search Parallel]
    RTT --> |Image| GIP[Generate Image Parallel]
    RTT --> |LLM| ELO[Execute LLM Optimized]
    RTT --> |Multiple| EPT[Execute Parallel Tools]
    
    COORD --> SRO[Synthesize Response Optimized]
    PFP --> ELO
    WSP --> ELO
    GIP --> ELO
    EPT --> SRO
    ELO --> SRO
    
    SRO --> FR[Finalize Response]
    FR --> END([Response to User])
    
    subgraph "Parallel Execution"
        PFP
        WSP
        GIP
        EPT
    end
    
    subgraph "Tool Results"
        TR[Tool Results]
        TE[Tool Errors]
    end
    
    PFP --> TR
    WSP --> TR
    GIP --> TR
    EPT --> TR
    
    PFP --> TE
    WSP --> TE
    GIP --> TE
    EPT --> TE
```

## 3. Tool Execution Flow

```mermaid
graph LR
    subgraph "Input Processing"
        UI[User Input] --> IA[Input Analysis]
        IA --> TD[Tool Detection]
        TD --> TR[Tool Routing]
    end
    
    subgraph "Parallel Tool Execution"
        TR --> |File Processing| DP[Document Processor]
        TR --> |Image Analysis| IA2[Image Analyzer]
        TR --> |Web Search| WS[Web Search Tool]
        TR --> |Search Analysis| SRA[Search Result Analyzer]
        TR --> |Image Generation| IG[Image Generation Tool]
        TR --> |LLM Generation| LLM[LLM Provider Tool]
    end
    
    subgraph "Result Processing"
        DP --> RC[Result Collection]
        IA2 --> RC
        WS --> RC
        SRA --> RC
        IG --> RC
        LLM --> RC
        
        RC --> RS[Response Synthesis]
        RS --> FR[Final Response]
    end
    
    subgraph "Error Handling"
        DP --> EH[Error Handler]
        IA2 --> EH
        WS --> EH
        SRA --> EH
        IG --> EH
        LLM --> EH
        
        EH --> FR
    end
```

## 4. Provider System Architecture

```mermaid
graph TB
    subgraph "Provider Registry"
        OPR[Optimized Provider Registry]
        WP[Warmup Process]
        CP2[Connection Pooling]
        PM2[Performance Monitoring]
    end
    
    subgraph "Provider Implementations"
        OAI_P[OpenAI Provider]
        ANT_P[Anthropic Provider]
        GOOG_P[Google Provider]
        MIST_P[Mistral Provider]
    end
    
    subgraph "Provider Features"
        CACH[Caching]
        RETRY[Retry Logic]
        FALLBACK[Fallback]
        METRICS[Metrics]
    end
    
    subgraph "External APIs"
        OAI_API[OpenAI API]
        ANT_API[Anthropic API]
        GOOG_API[Google API]
        MIST_API[Mistral API]
    end
    
    OPR --> OAI_P
    OPR --> ANT_P
    OPR --> GOOG_P
    OPR --> MIST_P
    
    OAI_P --> CACH
    ANT_P --> CACH
    GOOG_P --> CACH
    MIST_P --> CACH
    
    OAI_P --> RETRY
    ANT_P --> RETRY
    GOOG_P --> RETRY
    MIST_P --> RETRY
    
    OAI_P --> FALLBACK
    ANT_P --> FALLBACK
    GOOG_P --> FALLBACK
    MIST_P --> FALLBACK
    
    OAI_P --> METRICS
    ANT_P --> METRICS
    GOOG_P --> METRICS
    MIST_P --> METRICS
    
    OAI_P --> OAI_API
    ANT_P --> ANT_API
    GOOG_P --> GOOG_API
    MIST_P --> MIST_API
    
    WP --> OPR
    CP2 --> OPR
    PM2 --> OPR
```

## 5. Conversation Management Flow

```mermaid
graph TD
    subgraph "Conversation Manager"
        CM[Conversation Manager]
        CC[Conversation Cache]
        CI[Conversation Index]
        SC[Session Conversations]
    end
    
    subgraph "Storage Layer"
        FS[File System Storage]
        JSON[JSON Files]
    end
    
    subgraph "Context Management"
        CH[Conversation History]
        CC2[Conversation Context]
        TC[Token Counting]
        CT[Context Truncation]
    end
    
    CM --> CC
    CM --> CI
    CM --> SC
    
    CM --> FS
    FS --> JSON
    
    CM --> CH
    CH --> CC2
    CC2 --> TC
    TC --> CT
    
    subgraph "Operations"
        CREATE[Create Conversation]
        ADD[Add Message]
        GET[Get History]
        UPDATE[Update Title]
        DELETE[Delete Conversation]
    end
    
    CREATE --> CM
    ADD --> CM
    GET --> CM
    UPDATE --> CM
    DELETE --> CM
```

## 6. Performance Optimization System

```mermaid
graph TB
    subgraph "Performance Monitoring"
        PT[Performance Tracker]
        PM[Performance Metrics]
        OS[Operation Stats]
    end
    
    subgraph "Caching System"
        RC[Response Cache]
        CK[Cache Keys]
        TTL[TTL Management]
        LRU[LRU Eviction]
    end
    
    subgraph "Connection Management"
        CP[Connection Pool]
        HTTP[HTTP Sessions]
        KA[Keep-Alive]
        LIMITS[Connection Limits]
    end
    
    subgraph "Parallel Execution"
        PE[Parallel Executor]
        SEM[Semaphore Control]
        BATCH[Batch Processing]
        GATHER[Async Gather]
    end
    
    subgraph "Optimization Features"
        RETRY[Retry with Backoff]
        CACHE_DECORATOR[Cached Response Decorator]
        PERF_DECORATOR[Performance Monitor Decorator]
    end
    
    PT --> PM
    PM --> OS
    
    RC --> CK
    RC --> TTL
    RC --> LRU
    
    CP --> HTTP
    CP --> KA
    CP --> LIMITS
    
    PE --> SEM
    PE --> BATCH
    PE --> GATHER
    
    RETRY --> PE
    CACHE_DECORATOR --> RC
    PERF_DECORATOR --> PT
```

## 7. Error Handling and Fallback System

```mermaid
graph TD
    subgraph "Error Detection"
        TE[Tool Errors]
        PE[Provider Errors]
        VE[Validation Errors]
        NE[Network Errors]
    end
    
    subgraph "Error Handling"
        EH[Error Handler]
        ER[Error Recovery]
        FB[Fallback System]
        LOG[Error Logging]
    end
    
    subgraph "Fallback Responses"
        FR[Fallback Response Generator]
        RB[Rule-Based Responses]
        GR[Generic Responses]
        ER2[Error Responses]
    end
    
    subgraph "Recovery Mechanisms"
        RETRY2[Retry Logic]
        CIRCUIT[Circuit Breaker]
        DEGRADE[Graceful Degradation]
        ALERT[Alert System]
    end
    
    TE --> EH
    PE --> EH
    VE --> EH
    NE --> EH
    
    EH --> ER
    EH --> FB
    EH --> LOG
    
    FB --> FR
    FR --> RB
    FR --> GR
    FR --> ER2
    
    ER --> RETRY2
    ER --> CIRCUIT
    ER --> DEGRADE
    ER --> ALERT
```

## 8. Data Flow Architecture

```mermaid
graph LR
    subgraph "Input Layer"
        REQ[HTTP Request]
        FILE[File Upload]
        MSG[Message]
    end
    
    subgraph "Processing Layer"
        STATE[State Conversion]
        AGENT[Agent Processing]
        TOOLS[Tool Execution]
    end
    
    subgraph "State Management"
        CS[Chat State]
        FS[File State]
        SS[Search State]
        IS[Image State]
    end
    
    subgraph "Output Layer"
        RESP[HTTP Response]
        STREAM[Streaming Response]
        ERROR[Error Response]
    end
    
    REQ --> STATE
    FILE --> STATE
    MSG --> STATE
    
    STATE --> CS
    STATE --> FS
    STATE --> SS
    STATE --> IS
    
    CS --> AGENT
    FS --> AGENT
    SS --> AGENT
    IS --> AGENT
    
    AGENT --> TOOLS
    TOOLS --> AGENT
    
    AGENT --> RESP
    AGENT --> STREAM
    AGENT --> ERROR
```

## 9. Agent Communication System

```mermaid
graph TB
    subgraph "Communication Layer"
        ACL[Agent Communication Layer]
        AM[Agent Messages]
        AR[Agent Responses]
        PQ[Priority Queue]
    end
    
    subgraph "Message Types"
        REQ_MSG[Request Messages]
        RESP_MSG[Response Messages]
        NOTIF_MSG[Notification Messages]
        HEARTBEAT[Heartbeat Messages]
    end
    
    subgraph "Output Passing"
        OPM[Output Passing Manager]
        AOD[Agent Output Data]
        OM[Output Metadata]
        DT[Data Transformation]
    end
    
    subgraph "Agent Coordination"
        COORD[Coordination Logic]
        WORKFLOW[Workflow Management]
        DEP[Dependency Resolution]
        SYNC[Synchronization]
    end
    
    ACL --> AM
    ACL --> AR
    ACL --> PQ
    
    AM --> REQ_MSG
    AM --> RESP_MSG
    AM --> NOTIF_MSG
    AM --> HEARTBEAT
    
    OPM --> AOD
    AOD --> OM
    AOD --> DT
    
    COORD --> WORKFLOW
    WORKFLOW --> DEP
    DEP --> SYNC
    
    ACL --> OPM
    OPM --> COORD
```

## 10. Security and Validation Flow

```mermaid
graph TD
    subgraph "Input Validation"
        IV[Input Validator]
        FV[File Validator]
        SV[String Validator]
        TV[Type Validator]
    end
    
    subgraph "Security Checks"
        SC[Security Scanner]
        FS[File Scanner]
        CS[Content Scanner]
        VS[Virus Scanner]
    end
    
    subgraph "Rate Limiting"
        RL[Rate Limiter]
        IP[IP Tracking]
        SESSION[Session Tracking]
        THROTTLE[Throttling]
    end
    
    subgraph "Access Control"
        AC[Access Control]
        AUTH[Authentication]
        AUTHZ[Authorization]
        PERM[Permissions]
    end
    
    IV --> FV
    IV --> SV
    IV --> TV
    
    FV --> SC
    SC --> FS
    FS --> CS
    CS --> VS
    
    RL --> IP
    RL --> SESSION
    RL --> THROTTLE
    
    AC --> AUTH
    AC --> AUTHZ
    AUTHZ --> PERM
    
    subgraph "Current Gaps"
        GAP1[Limited File Validation]
        GAP2[No Rate Limiting]
        GAP3[Basic Security Checks]
        GAP4[No Access Control]
    end
    
    GAP1 -.-> FV
    GAP2 -.-> RL
    GAP3 -.-> SC
    GAP4 -.-> AC
```

These diagrams show the complete architecture of your backend system, including the current implementation and areas that need improvement. The system is well-architected but has several gaps in implementation, particularly in security, monitoring, and actual tool integrations.

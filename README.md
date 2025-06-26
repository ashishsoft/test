```mermaid
graph LR
    subgraph "Data Extraction (Source CST implied)"
        A[External Source System] --> A1(Data Files: Dates/Times in CST or Unspecified Format)
        A1 --> B[Ab Initio: Read File Component]
    end

    subgraph "Data Transformation & Staging (Server Timezone: UTC)"
        B --> C{Initial Validation & Cleansing}
        C -- Failed Validation --> C1[Error Handling & Reject Files]
        C -- Passed Validation --> D[Data Integration / Join Multiple Sources]

        D --> E_TZ[CRITICAL: Timezone Conversion]
        E_TZ --> F_TZ{Convert ALL Date/Time Fields to UTC}
        F_TZ -- Logic: datetime_add(cst_datetime, 6 hours) --> G_TZ[Standardized Data - All Dates/Times in UTC]

        G_TZ --> H[Data Enrichment & Derivations]
        H --> I[Apply Business Rules & Lookups]
        I --> J[Data Type Conversion & Formatting]
        J --> K[Ab Initio: Sort / Aggregate / Deduplicate]
        K --> L(Staging Area / Intermediate Tables: Dates/Times in UTC)
    end

    subgraph "Data Loading (Database Timezone: Unchanged)"
        L --> M[Ab Initio: Database Load Component]
        M --> N[Target Database: Data Warehouse / Data Mart - Load UTC directly]
        N -- Successfully Loaded --> N1[Load Audit & Logging - Audit Times in UTC]
    end

    subgraph "Data Reporting & Consumption (Interpreting UTC for Business Needs)"
        N --> P[Reporting Tools: Tableau, Power BI, QlikView, etc.]
        P -- Reporting Layer handles display conversion UTC to CST/Local --> Q[Ad-hoc Queries & Analysis]
        N --> R[Downstream Applications / APIs]
        P & Q & R --> S[Business Users / Decision Makers]
    end

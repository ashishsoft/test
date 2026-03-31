Core Data Input Requirements
​The pipeline must support several distinct loan-related data files from external sellers and third parties:
​Seller Loan Data: The primary data file, often provided in the ASF (Industry Standard) format, containing approximately 180–190 data points.
​Supplemental Loan Data: Additional data for the same loan set intended to enhance the initial records.
​HMDA Data: Home Mortgage Disclosure Act data sourced from both the seller and third-party reviewers (TPR).
​Third Party Review (TPR) Data: Exception data generated from external due diligence processes.
​ETL Pipeline & Architectural Logic
​The integration follows a specific flow between HLADS (Home Lending Automated Data System) and downstream applications like LPO:
​Ingestion: Data files are uploaded via the Axway SFTP platform into the HLADS "Sanitized Zone" for initial processing.
​Transformation & Mapping: * Sellers may vary column headers, naming conventions (e.g., "Industry Paid Through Date" vs. "Scheduled Interest Paid Through Date"), and data point order.
​The system must map diverse seller formats to a Super Set of ~250 attributes within the HLADS Curated Zone.
​Downstream distribution must utilize the MISMO JSON format.
​Data Movement: Kafka is the designated distribution channel. HLADS will act as a producer, sending messages to specific Kafka Topics that downstream applications like LPO will subscribe to.
​Syncing & Updates: A bidirectional sync is required. Updates made in the domain application (LPO) must flow back to the HLADS Curated Zone using the same Kafka/JSON standards to maintain data integrity.
​Critical Constraints & Challenges
​Dynamic Flexibility: The pipeline must be "nimble" and capable of adapting to seller-specific variations within a two-week turnaround time.
​Sensitive Data Protection: Because files contain Personally Identifiable Information (PII) and sensitive financial data, manual editing by technology teams is strictly prohibited; all adaptations should be handled systematically or by authorized business users.
​Validation: Multi-step verification is needed to ensure that supplemental files contain the same loan IDs as the primary files before merging.
​The overall significance of this design is to create an API-first, scalable architecture that supports not just bulk purchases, but also future servicing acquisitions and home equity integrations.
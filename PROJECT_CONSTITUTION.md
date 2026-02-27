# Project Principles for GnuCash (X-Accountant)

This document outlines the additional principles guiding the development of GnuCash, ensuring a consistent vision and high standards across all contributions.

## Constitution Additions

These additions are to be considered in conjunction with the Core Principles found at `.specify/memory/constitution.md`.

### VII. Financial Data Accuracy (The Foundation of Trust)

The core purpose of this application is to manage financial records. Therefore, unwavering accuracy in all calculations, balances, and transaction processing is non-negotiable. Mechanisms like double-entry accounting and reconciliation are fundamental safeguards against errors.

- **Rules**: All financial computations must be rigorously validated. Data entry must undergo stringent validation to prevent corruption. Reconciliation processes must accurately reflect external statements.
- **Rationale**: User trust in financial software hinges entirely on its correctness. Errors undermine its utility and purpose.

### VIII. Data Longevity & Interoperability (Preserving Financial History)

Financial data has enduring value and must be accessible across software versions and potentially other financial systems. The evolution of the native file format must prioritize backward compatibility, ensuring that historical data remains readable and usable.

- **Rules**: New file format versions must include robust migration paths for older data. External data import (e.g., QIF) must maintain the integrity and meaning of the imported records.
- **Rationale**: Users expect their financial history to be preserved and portable. Forced data migration or loss of historical context is unacceptable.

### IX. Cross-Platform Consistency (Universal Accessibility)

The application aims to provide a consistent and reliable experience across diverse operating environments. Technical considerations for system differences (e.g., hardware architecture, GUI toolkits) must be addressed to ensure functional parity and data integrity regardless of the platform.

- **Rules**: Implementations must account for architectural differences (e.g., endianness). User interface components should be chosen or designed to render consistently across supported platforms.
- **Rationale**: Broad accessibility ensures a wider user base and supports the GNU philosophy of free software availability.

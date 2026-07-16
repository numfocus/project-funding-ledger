# 1 Introduction

## 1.1 Purpose

This document defines the overall development strategy for the NumFOCUS
Project Funding Ledger (PFL). It describes the implementation
philosophy, development sequencing, and major milestones that will guide
construction of the application.

The roadmap is intended to provide a high-level execution plan for
delivering Version 1 of the PFL while minimizing technical risk through
incremental implementation and validation.

## 1.2 Relationship to Other Project Documentation

The Project Funding Ledger documentation is organized into four
complementary documents that collectively define the business
requirements, implementation strategy, technical architecture, and
software development approach for the application. The following table
describes the documents.

The following table summarizes the purpose of each document.

> Document Definition

| **Document** | **Purpose** |
|----|----|
| NumFOCUS PFL - 1 Functional Specification | Defines the business requirements, functional capabilities, user workflows, and reporting requirements. |
| NumFOCUS PFL - 2 Development Roadmap and Implementation Strategy | Defines the overall implementation strategy, development phases, milestones, and project sequencing. (This document.) |
| NumFOCUS PFL – 3 Architecture Design | Defines the system architecture, database design, security model, data model, integrations, and technical design decisions. |
| NumFOCUS PFL - 4 Development Plan | Defines the detailed implementation tasks, coding standards, repository structure, development environment, testing procedures, deployment process, and other developer guidance. |

Together, these documents provide a complete specification for the
Project Funding Ledger, from business requirements through technical
implementation.

## 1.3 Development Philosophy

The Project Funding Ledger (PFL) shall be developed incrementally
through a series of well-defined milestones. Each milestone should
produce a stable, reviewable increment that builds upon previously
completed functionality. Each milestone establishes a functional
foundation for subsequent milestones and should be considered complete
before development proceeds to the next major phase.

Development should prioritize:

- Establishing a reliable database foundation before user interface
  development.

- Implementing security before exposing application functionality.

- Validating backend business workflows before developing frontend
  screens.

- Maintaining complete auditability throughout development.

- Delivering working software at the conclusion of each milestone.

## 1.4 Implementation Principles

The following are guiding principles of the design and development
effort:

- Build the foundation first.

- Prefer configuration over custom code.

- Preserve data integrity.

- Maintain complete auditability.

- Keep business rules centralized.

- Deliver incremental value.

- Favor simplicity over premature optimization.

# 2 Development Milestones

The Project Funding Ledger (PFL) shall be implemented through a series
of sequential development milestones. Each milestone represents a
significant increment of application functionality and establishes the
technical foundation required for subsequent development. Milestones are
intended to reduce implementation risk, support periodic technical
review, and ensure that Version 1 evolves through stable, validated
increments rather than as a single large development effort.

## 2.1 Milestone 1: Project Repository and Development Environment

Establish the GitHub repository, development standards, local
development environment, Supabase project, initial Next.js application
shell, environment variable structure, and basic deployment approach.

## 2.2 Milestone 2: Database Foundation

Create the initial PostgreSQL schema for the core business entities,
including Project, Funding Source, User Profile, Project Permission,
Import Batch, Financial Transaction, Mapping Rule, Mapping Exception,
Supporting Document, Governing Agreement, Reporting Obligation, Project
Governance, and Audit Log.

This milestone should include primary keys, foreign keys, required
fields, enums, timestamps, indexes, and initial database migration
scripts.

## 2.3 Milestone 3: Security and Row-Level Access Control

Implement Supabase authentication and Row Level Security policies.
Security shall be based primarily on Project Permissions. Users are
granted access to one or more Projects. Access to the associated core
business entities, including Funding Source, Financial Transaction,
Governing Agreement, Reporting Obligation, Project Governance, and
Supporting Document, is inherited automatically through the Project
relationship.

## 2.4 Milestone 4: Core Backend Workflows

Develop backend workflows for creating, updating, and maintaining the
core business entities, including Project, Funding Source, Governing
Agreement, Reporting Obligation, Supporting Document, and Project
Permission. These workflows should be tested directly against the
database before significant frontend development begins.

## 2.5 Milestone 5: Import Batch and Financial Transaction Import Framework

Implement the QuickBooks Online (QBO) import framework, including
standardized import file processing, file upload, import batch creation,
source file hashing, validation, duplicate detection, transformation of
imported QBO data into normalized Import Batch and Financial Transaction
records, financial transaction import, error handling, and immutable
imported Financial Transaction records.

The import framework shall include the data translation layer
responsible for converting standardized QBO import files into the
Project Funding Ledger's internal data model. This process shall
validate incoming data, normalize imported values, populate Import Batch
and Financial Transaction business entities, preserve traceability to
the source QBO data, and identify records requiring manual review before
import completion.

## 2.6 Milestone 6: Mapping Engine

Implement the Financial Transaction Mapping Engine to assign imported
Financial Transactions to Funding Sources using the standardized
QuickBooks Online (QBO) Class value. The QBO Class is expected to follow
the "Project \| Funding Source" naming convention and should provide the
primary mechanism for identifying the appropriate Funding Source during
import. Additional imported attributes, including QBO Account and
Transaction Type (Income or Expense), may be used to support validation,
specialized mapping scenarios, or legacy data. Financial Transactions
that cannot be confidently assigned shall be routed to the Mapping
Exception queue for manual review.

## 2.7 Milestone 7: Mapping Exception Resolution

Implement workflows for reviewing, assigning, resolving, and auditing
the Mapping Exception business entity. Resolution should update only
permitted assignment fields and should not modify immutable QBO
financial transaction fields.

## 2.8 Milestone 8: Supporting Document Repository

Implement document upload, storage, metadata management, versioning,
access control, and relationships between the Supporting Document core
business entity and the associated Project, Funding Source, Governing
Agreement, Reporting Obligation, and Project Governance core business
entities. Financial Transaction-level accounting support documents
remain outside the PFL.

## 2.9 Milestone 9: Dashboards and Inquiry Screens

Develop user-facing dashboards, inquiry screens, and administrative
interfaces for the core business entities, including Project, Funding
Source, Project Governance, Governing Agreement, Reporting Obligation,
Supporting Document, Import Batch, Financial Transaction, Mapping Rule,
Mapping Exception, User Profile, Project Permission, Funding Adjustment,
and Audit Log.

## 2.10 Milestone 10: Export Capabilities

Implement CSV export capabilities for the core business entities
Financial Transaction and Funding Adjustment.

## 2.11 Milestone 11: Audit Logging and Administrative Review

Implement comprehensive audit logging and administrative review
capabilities for the core business entities, including Project, Funding
Source, Project Governance, Governing Agreement, Reporting Obligation,
Supporting Document, Import Batch, Financial Transaction, Mapping Rule,
Mapping Exception, User Profile, Project Permission, and Funding
Adjustment. Audit Log entries shall capture significant business events,
metadata changes, permission changes, import activities, lifecycle
events, and administrative actions to provide complete traceability
throughout the PFL.

## 2.12 Milestone 12: Testing, Review, and Production Readiness

Complete unit testing, integration testing, role-based access testing,
import testing, mapping testing, export testing, and user acceptance
testing. Prepare the production deployment checklist, backup procedures,
and post-launch support process.

## 2.13 Milestone Completion

Each development milestone should conclude with a technical review to
verify that the milestone objectives have been satisfied and that the
completed functionality provides a stable foundation for subsequent
development. Unless otherwise approved, unresolved defects or incomplete
deliverables should be addressed before proceeding to the next
milestone.

# 3 Version 1 Objectives

The objective of Version 1 of the NumFOCUS Project Funding Ledger (PFL)
is to deliver a secure, production-ready application that provides
NumFOCUS with a centralized repository for managing Project funding
information outside the accounting system. Version 1 establishes the
architectural and operational foundation for future enhancements while
delivering the core capabilities necessary to manage Projects, Funding
Sources, supporting governance information, and imported QuickBooks
Online (QBO) Financial Transactions.

The application is intended to complement, rather than replace, existing
operational systems. QuickBooks Online remains the authoritative
accounting system of record, while the Project Funding Ledger becomes
the authoritative operational repository for project funding metadata,
imported Financial Transactions, governance records, supporting
documentation, and related administrative information.

Version 1 shall establish a scalable, maintainable platform capable of
supporting future enhancements without requiring fundamental
architectural redesign.

## 3.1 Expected Version 1 Deliverables

Upon successful completion of the Version 1 development effort, the
Project Funding Ledger is expected to provide the following
capabilities:

- Secure authentication and Project-based access control.

- Project and Funding Source management.

- Import of Financial Transactions from standardized QuickBooks Online
  data extracts.

- Import Batch management with complete import traceability and audit
  history.

- Automated Financial Transaction assignment through the Mapping Rule
  engine.

- Mapping Exception review and resolution workflows.

- Supporting Document repository with metadata management, version
  control, and relationships to associated business entities.

- Project Governance, Governing Agreement, and Reporting Obligation
  management.

- Administrative dashboards and inquiry screens for all core business
  entities.

- Comprehensive Audit Log and administrative review capabilities.

- CSV export functionality for supported business entities.

- A fully tested, documented, and production-ready application suitable
  for operational use by NumFOCUS staff.

## 3.2 Future Development

Version 1 establishes the technical and functional foundation for the
continued evolution of the Project Funding Ledger. Future releases may
introduce additional capabilities, including expanded integrations with
external systems, workflow automation, enhanced reporting and analytics,
automated data synchronization, and other operational improvements.

Future enhancements should build upon the architectural principles
established during Version 1 while preserving the application's core
design goals of data integrity, Project-based security, complete
auditability, and clear separation between accounting systems of record
and project funding management.

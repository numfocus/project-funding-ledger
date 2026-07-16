# 1 Introduction 

## 1.1 Executive Summary 

The Project Funding Ledger (PFL) is a project funding visibility and
governance application that provides NumFOCUS staff and authorized
Fiscally Sponsored Project stakeholders with a centralized view of
project funding, financial activity, funding authority, agreements,
reporting obligations, supporting documents, and related project
information.

Today, project funding information is \`distributed across multiple
operational systems, spreadsheets, documents, and institutional
knowledge, making it difficult for project stakeholders to understand
available funding, funding restrictions, reporting commitments, and the
agreements that govern project resources. The PFL consolidates this
information into a single application that improves transparency,
supports informed decision-making, and strengthens project governance.

The PFL imports selected financial activity from QuickBooks Online (QBO)
and combines that information with project-specific operational metadata
maintained within the application. Together, these records provide a
comprehensive view of project funding without duplicating the accounting
responsibilities of existing financial systems.

The PFL is not an accounting system and does not replace QuickBooks
Online. QBO remains the authoritative system of record for accounting
transactions, financial reporting, accounts payable, accounts
receivable, payment processing, and other accounting functions. The PFL
supplements these operational systems by organizing project funding
information in a manner that is meaningful and accessible to project
stakeholders.

The application supports NumFOCUS's broader objectives of improving
financial transparency, strengthening project governance, reducing
reliance on manual reporting processes, and providing project leaders
with self-service access to the information needed to manage their
projects effectively.

## 1.2 PFL in the Financial Systems Architecture

The Project Funding Ledger is one of three core financial management
systems used by NumFOCUS. Each system serves a distinct business purpose
and complements, rather than replaces, the others.

The Expense Entry System captures and approves spending requests,
including employee reimbursements, credit card expenses, and vendor
invoices. Approved expenses are recorded in the Accounting System, which
serves as the authoritative system of record for all economic activity,
including the general ledger, financial statements, assets, liabilities,
revenues, and expenses.

The Project Funding Ledger imports selected accounting activity together
with Project governance, funding, agreement, reporting, and supporting
document information to provide a point-in-time operational view of
available Project funding. The PFL is not an accounting system and does
not replace the organization's financial or operational systems of
record.

<img src="../images/three-core-financial-systems.png"
     alt="Three Core Financial Systems"
     style="width:9in;height:5.06in" />

**1.3 Purpose**

This Functional Specification defines the business capabilities,
functional requirements, and business rules for the PFL.

The document describes the business problems the application addresses,
the users it serves, and the functional capabilities required to support
project funding management and visibility. It defines what the system
must do from a business perspective without prescribing the technical
implementation.

The intended audience includes business stakeholders, project sponsors,
product owners, business analysts, architects, software developers,
quality assurance personnel, and others involved in the planning,
design, development, testing, and support of the PFL.

## 1.4 Relationship to Other Project Documentation

The Project Funding Ledger (PFL) documentation is organized into complementary documents, each serving a distinct purpose.

This **Functional Specification** defines the business capabilities, user requirements, business rules, and functional behavior of the PFL. It describes **what** the application must do to meet the needs of NumFOCUS staff, fiscally sponsored projects, and other stakeholders.

The **Architecture Design** translates those business requirements into the system's technical architecture, including the business entity model, database design, security model, integration strategy, and other technical design decisions. It describes **how** the system is designed to satisfy the functional requirements.

The **Development Plan** defines how the application will be implemented, including the development environment, repository organization, coding standards, testing approach, deployment process, and other guidance for contributors.

The **Development Roadmap & Implementation Strategy** defines the overall implementation approach, project phases, milestones, priorities, and sequencing used to guide the evolution of the Project Funding Ledger from initial development through production deployment.

Together, these documents provide a complete description of the Project Funding Ledger while maintaining a clear separation between business requirements, technical architecture, implementation planning, and development execution.

The following table summarizes the purpose of each document.

> Document Definition

| Document                                                                                 | Purpose                                                                                                                                                                           |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **[Functional Specification](../functional-specification/functional-specification.md)**  | Defines the business requirements, functional capabilities, user workflows, and reporting requirements.                                                                           |
| **[Development Roadmap and Implementation Strategy](../roadmap/development-roadmap.md)** | Defines the overall implementation strategy, development phases, milestones, and project sequencing. *(This document.)*                                                           |
| **[Architecture Design](../architecture/architecture-design.md)**                        | Defines the system architecture, database design, security model, data model, integrations, and technical design decisions.                                                       |
| **[Development Plan](../development/development-plan.md)**                               | Defines the detailed implementation tasks, coding standards, repository structure, development environment, testing procedures, deployment process, and other developer guidance. |

## 
## 1.5 Business Objectives

The primary business objectives of the PFL are to:

- Provide a centralized source of project funding information for
  NumFOCUS staff and authorized project stakeholders.

- Improve transparency into project funding, financial activity, and
  available funding authority.

- Provide authorized users with self-service access to project funding
  information without requiring access to QuickBooks Online.

- Consolidate project governance records, agreements, reporting
  obligations, and supporting documents into a single application.

- Improve consistency, traceability, and accountability of project
  funding information.

- Reduce the manual effort required to answer project funding questions
  and prepare operational reports.

- Support the retirement of Open Collective as the primary project
  funding visibility platform.

- Provide a scalable foundation for future enhancements to project
  funding management and reporting.

## 1.6 Business Scope

The PFL supports the operational management and visibility of project
funding throughout its lifecycle.

The application provides capabilities for:

- Maintaining Project information.

- Maintaining Funding Source information.

- Importing and viewing financial activity.

- Managing Project Governance records.

- Managing Agreement records.

- Managing Reporting Obligation records.

- Managing Supporting Document records.

- Reviewing project funding activity and funding availability.

- Searching, filtering, and exporting project funding information.

- Maintaining an auditable history of significant operational activity.

The PFL supplements existing operational systems by organizing project
funding information for operational visibility and governance. It is not
intended to replace accounting, payment processing, expense management,
document management, or other operational systems that remain the
authoritative source for those business functions.

## 1.7 Guiding Principles

The PFL is guided by the following business principles:

- QuickBooks Online remains the authoritative financial system of
  record.

- The PFL provides operational visibility into project funding rather
  than performing accounting functions.

- Information should be entered once whenever practical and reused
  throughout the application.

- Authorized users should be able to answer routine project funding
  questions without requiring assistance from Finance.

- Project funding information should remain traceable to its
  authoritative source.

- The application should support future organizational growth while
  minimizing disruption to established business processes.

# 2. Functional Requirements

## 2.1 Overview

The Project Funding Ledger provides business capabilities that support
the management, visibility, governance, and reporting of project funding
throughout its lifecycle. The functional requirements described in this
section define the business capabilities the application must provide to
support NumFOCUS staff and authorized Fiscally Sponsored Project
stakeholders.

The requirements are organized by major functional area and describe
what the system must do from a business perspective. Technical
implementation details, application architecture, database design, and
development standards are documented separately within the Design
Specification and Development Standards.

## 2.2 Project Management

The system shall provide functionality for maintaining and managing
Project information throughout the Project lifecycle. Users shall be
able to create, maintain, search, view, and archive Project records,
together with associated governance information, funding sources, and
supporting documentation.

Primary capabilities include:

- Create and maintain Project information.

- View Project details and current status.

- Associate Funding Sources with a Project.

- Associate Project Governance records.

- Associate Supporting Documents.

- Search and filter Projects.

- View Project funding summary information.

## 2.3 Funding Source Management

The system shall provide functionality for maintaining Funding Sources
and the operational information associated with each source of project
funding.

Primary capabilities include:

- Create and maintain Funding Source information.

- Record funding authority and related operational metadata.

- Associate Funding Sources with Projects.

- Associate Governing Agreements.

- Associate Reporting Obligations.

- Associate Supporting Documents.

- Monitor funding availability.

- Close or archive Funding Sources.

## 2.4 Financial Activity

The system shall provide visibility into financial activity associated
with Projects and Funding Sources by importing accounting activity from
the financial system of record.

Primary capabilities include:

- Import financial activity.

- View financial activity.

- Search and filter financial activity.

- Associate financial activity with Projects and Funding Sources.

- Export financial activity.

- Preserve traceability to source accounting records.

## 2.5 Funding Adjustment Management

The system shall provide functionality for recording operational funding
adjustments that affect the availability or presentation of Project
funding without modifying the underlying accounting records.

Primary capabilities include:

- Record Funding Adjustments.

- Associate Funding Adjustments with Funding Sources.

- Maintain adjustment history.

- Include Funding Adjustments in operational funding views.

- Preserve an audit history of adjustments.

## 

## 

## 2.6 Project Governance Management

The system shall provide functionality for maintaining Project
Governance information that defines the relationship between NumFOCUS
and each Project.

Primary capabilities include:

- Create and maintain Project Governance records.

- Associate governance records with Projects.

- Associate Supporting Documents.

- View governance history.

- Search Project Governance information.

## 2.7 Agreement Management

The system shall provide functionality for maintaining Governing
Agreements that establish funding authority, contractual obligations, or
other relationships affecting Project funding.

Primary capabilities include:

- Create and maintain Agreement records.

- Associate Agreements with Projects and Funding Sources.

- Track Agreement status and effective periods.

- Associate Supporting Documents.

- Search and review Agreements.

## 2.8 Reporting Obligation Management

The system shall provide functionality for maintaining Reporting
Obligations associated with Projects, Funding Sources, and Governing
Agreements.

Primary capabilities include:

- Create and maintain Reporting Obligations.

- Record reporting schedules and due dates.

- Track reporting status.

- Associate Reporting Obligations with Funding Sources and Agreements.

- View reporting calendars and schedules.

## 2.9 Supporting Document Management

The system shall provide centralized management of Supporting Documents
associated with Projects, Funding Sources, Governing Agreements, Project
Governance records, and Reporting Obligations.

Primary capabilities include:

- Upload Supporting Documents.

- Maintain document metadata.

- Associate Supporting Documents with business records.

- Maintain document versions.

- Search and retrieve Supporting Documents.

- Download Supporting Documents.

## 2.10 User Access and Security

The system shall provide user authentication, authorization, and
permission management appropriate to each user's assigned
responsibilities.

Primary capabilities include:

- Maintain User Profiles.

- Assign Project Permissions.

- Authenticate users.

- Authorize access to Project information.

- Restrict access to authorized information.

- Maintain user session security.

## 2.11 Search, Inquiry, and Reporting

The system shall provide inquiry, search, dashboard, and reporting
capabilities that enable users to locate and analyze Project funding
information.

Primary capabilities include:

- Search across Project funding information.

- Filter business information.

- Display Project dashboards.

- Display Funding Source dashboards.

- Export selected information.

- Support operational reporting.

## 2.12 Administration

The system shall provide administrative capabilities necessary to
support ongoing operation of the Project Funding Ledger.

Primary capabilities include:

- Maintain Supporting Reference Data.

- Configure application settings.

- Manage Mapping Rules.

- Review and resolve Mapping Exceptions.

- Monitor Import Batches.

- Manage application configuration.

## 

## 2.13 Audit and Traceability

The system shall maintain a complete history of significant operational
activity to support accountability, transparency, and historical review.

Primary capabilities include:

- Record Audit Log entries.

- Maintain historical record changes.

- Preserve traceability to originating records.

- Review system activity.

- Support operational and compliance audits.

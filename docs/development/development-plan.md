# 1 Introduction 

## 1.1 Purpose

**Project Funding Ledger (PFL) Development Plan** defines
the software engineering practices for developing, testing, deploying,
and maintaining the PFL application. It describes the development
environment, repository organization, coding standards, testing
strategy, deployment process, release management, development workflow,
and other engineering practices that support the project throughout its
lifecycle.

This document serves as the authoritative software engineering guide for
the PFL. It establishes the standards, conventions, and engineering
practices that promote consistency, maintainability, code quality, and
effective collaboration among project contributors.

## 1.2 Relationship to Other Project Documentation

The PFL documentation is organized into four complementary documents
that collectively define the business requirements, implementation
strategy, technical architecture, and software development approach for
the application. 

Together, these documents provide a complete description of the PFL
while maintaining a clear separation between business requirements,
system design, and software implementation.

The following table summarizes the purpose of each document.

> Document Definition

| Document                                                                                 | Purpose                                                                                                                                                                           |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **[Functional Specification](../functional-specification/functional-specification.md)**  | Defines the business requirements, functional capabilities, user workflows, and reporting requirements.                                                                           |
| **[Development Roadmap and Implementation Strategy](../roadmap/development-roadmap.md)** | Defines the overall implementation strategy, development phases, milestones, and project sequencing. *(This document.)*                                                           |
| **[Architecture Design](../architecture/architecture-design.md)**                        | Defines the system architecture, database design, security model, data model, integrations, and technical design decisions.                                                       |
| **[Development Plan](../development/development-plan.md)**                               | Defines the detailed implementation tasks, coding standards, repository structure, development environment, testing procedures, deployment process, and other developer guidance. |

## 

## 1.3 Scope

This document defines the software engineering practices used to
develop, test, deploy, and maintain Version 1 of the Project Funding
Ledger. It describes the development environment, repository
organization, coding conventions, testing strategy, deployment process,
source control practices, release management, documentation standards,
and other engineering practices that support the project's long-term
sustainability.

This document defines how the Project Funding Ledger is developed and
maintained. It does not define business requirements, implementation
priorities, application architecture, database design, security
architecture, or functional behavior, which are documented separately in
the Functional Specification, Development Roadmap and Implementation
Strategy, and Architecture Design documents.

# 2. Development Philosophy

The PFL is developed using modern software engineering practices that
emphasize simplicity, maintainability, transparency, and long-term
sustainability. The objective is to create a reliable, well-documented
application that can be understood, maintained, and extended by future
contributors while minimizing operational complexity and technical debt.

Development decisions should prioritize clarity, correctness,
maintainability, and security over unnecessary technical sophistication.
The application is intended to evolve incrementally through well-defined
enhancements while preserving the integrity of its core architecture,
business rules, and data model.

The project values established engineering practices, thoughtful
architectural design, comprehensive testing, and constructive peer
review. Contributors are encouraged to use the tools and development
workflows that best support these goals, provided that all contributions
meet the project's standards for quality, security, documentation, and
maintainability.

The following principles guide all software development activities for
the Project Funding Ledger.

## 2.1 Engineering Principles

The Project Funding Ledger is developed according to the following
engineering principles:

1.  Business requirements drive technical design. Technology choices
    should support the application's business objectives rather than
    dictate them.

2.  Simplicity is preferred over complexity. Straightforward,
    understandable solutions are favored whenever they adequately
    satisfy the requirements.

3.  Configuration is preferred where it improves flexibility without
    introducing unnecessary complexity. Business rules should be
    configurable whenever practical to reduce future maintenance.

4.  Maintainability takes precedence over optimization. Code should be
    written for long-term readability and supportability before
    unnecessary performance optimizations are pursued.

5.  The database is the authoritative source for application data and
    business relationships. Business entities and their relationships
    should be maintained through the relational data model rather than
    duplicated within application logic.

6.  Imported accounting data remains immutable. Application
    functionality must never modify accounting information imported from
    QuickBooks Online.

7.  Security is designed into the application rather than added
    afterward. Authentication, authorization, and auditability are
    fundamental architectural requirements.

8.  Every significant business action should be traceable.
    Administrative changes, data imports, mapping decisions, and other
    material activities should be auditable.

9.  Technical debt should be minimized through continuous improvement.
    Code should be periodically reviewed, refactored, and simplified
    where appropriate without compromising application stability.

10. Documentation is part of the deliverable. Software is not considered
    complete until the corresponding technical documentation has been
    updated.

## 2.2 Open Source Development Philosophy

The Project Funding Ledger is to be developed as an open source software
project.

Development practices should encourage transparency, collaboration,
maintainability, and community participation while supporting
contributions from future developers. Application architecture, coding
standards, and documentation should be sufficiently clear that an
experienced developer can understand and extend the application without
requiring institutional knowledge.

All significant architectural and functional decisions should be
documented within the project's technical documentation to preserve
design intent as the application evolves.

## 2.3 Open Source Licensing

The Project Funding Ledger is licensed under the **BSD 3-Clause License**.

All source code, documentation, and other project artifacts contributed to the repository are governed by the terms of the BSD 3-Clause License unless otherwise noted.

All third-party libraries, frameworks, and other software dependencies incorporated into the application must be compatible with the BSD 3-Clause License or otherwise approved by the project maintainers.

Contributors should make reasonable efforts to understand the licensing terms of external software components included in their contributions. Project maintainers are responsible for reviewing and approving dependencies to ensure continued compliance with the project's licensing requirements.

The inclusion of third-party software should be limited to dependencies that provide clear value to the project. Preference should be given to mature, well-maintained, widely adopted open source projects with active communities, permissive licensing, and long-term maintenance prospects.

## 2.4 AI-Assisted Development

The Project Funding Ledger welcomes contributions developed using a
variety of software engineering approaches. Contributors may choose to
use artificial intelligence (AI) tools as development aids where they
improve productivity, software quality, or developer experience.
Examples include generating boilerplate code, developing test cases,
drafting documentation, exploring implementation alternatives, or
assisting with code review.

The use of AI-assisted development is entirely optional. Contributors
are equally welcome to develop software using traditional software
engineering practices without AI assistance.

Regardless of how code is produced, all contributions are expected to
meet the same standards for correctness, maintainability, security,
performance, documentation, and licensing compliance. AI-generated
content should be treated as a development aid rather than an
authoritative source and should be reviewed, validated, and tested by
the contributor before submission.

Responsibility for the quality and suitability of each contribution
always remains with the human contributor submitting the change. The use
of AI tools does not replace sound engineering judgment, thoughtful
architectural design, comprehensive testing, or peer review.

# 3. Development Environment

## 3.1 Required Software

Development of the Project Funding Ledger requires the following
software components:

| Document | Purpose |
|----|----|
| Visual Studio Code (or comparable IDE) | Primary development environment |
| Git | Source control |
| GitHub | Source code repository and collaboration |
| Python (3.12 or newer) | Python runtime |
| uv | Package management |
| Supabase CLI | Local Supabase development and database management |
| PostgreSQL | Local database platform (when applicable) |
| Modern Web Browser | Application testing and debugging |

Contributors may use additional development tools, editors, extensions,
debugging utilities, AI-assisted development tools, or other software
engineering tools that support their individual workflows. Regardless of
the tools used, all contributions are expected to conform to the
project's coding standards, testing requirements, and contribution
guidelines.

## 3.2 Local Development Environment

Developers should maintain a local development environment that
reasonably reflects the production architecture whenever practical. The
project provides a standard local development environment to simplify
onboarding, testing, and collaboration.

The local development environment should support:

- Local execution of the Flask & Jinja2 application

- Local Supabase services

- Local PostgreSQL database

- Authentication testing

- Row-Level Security testing

- Database migrations

- File storage testing

- API testing

Application configuration should be externalized through environment
variables to allow consistent deployment across development, test, and
production environments.

## 3.3 Environment Variables

Environment-specific configuration shall be maintained outside the
application source code.

Typical environment variables include:

- Supabase URL

- Supabase API keys

- Database connection information

- Authentication configuration

- Storage configuration

- Application environment (Development, Test, Production)

Sensitive credentials shall never be committed to source control.

Environment variable templates may be provided for developer onboarding.

## 3.4 Local Database

Local development should utilize the Supabase local development
environment, including PostgreSQL, whenever practical.

Database schema changes shall be implemented through version-controlled
migration scripts rather than manual database modifications.

Developers should periodically rebuild local environments from migration
scripts to verify that the complete database can be recreated from
source control.

### 3.4.1 Database Migrations

Database schema changes shall be implemented exclusively through
version-controlled migration scripts. Manual schema modifications to
shared development, test, or production databases should be avoided.
Each migration should be repeatable, reversible where practical, and
capable of recreating the database schema from an empty database.

## 3.5 Development Data

The project should provide representative sample data for development
and testing that exercises the application's primary business processes.

Development data should include examples of:

- Projects

- Funding Sources

- Financial Transactions

- Supporting Documents

- Governing Agreements

- Reporting Obligations

- Project Governance

- User Profiles

- Project Permissions

- Mapping Rules

- Mapping Exceptions

- Funding Adjustments

Production financial information, confidential documents, credentials,
or personally identifiable information should not be included in
development datasets unless specifically authorized and appropriately
protected.

# 4 Source Code Management

## 4.1 Source Code Repository

The Project Funding Ledger source code shall be maintained within a
distributed version control repository. GitHub serves as the project's
initial authoritative source code repository.

Application source code, database migration scripts, technical
documentation, configuration templates, and other development artifacts
shall be maintained under version control to preserve a complete history
of the application's evolution.

## 4.2 Repository Organization

The source repository should be organized to clearly separate
application components, database objects, documentation, and supporting
development resources.

The repository should include dedicated locations for:

- Application source code

- Database migration scripts

- Technical documentation

- Development utilities and scripts

- Static application assets

- Configuration templates

The repository organization should remain simple, consistent, and
intuitive to facilitate long-term maintenance and future contributions.

## 4.3 Version Control Practices

Development should occur through small, incremental changes that can be
easily understood, tested, and maintained.

Developers should:

- Commit changes frequently.

- Use clear, descriptive commit messages.

- Maintain a stable and functional main branch.

- Document significant architectural, database, or business rule changes
  as part of the corresponding documentation updates.

Version control history should provide a clear record of how the
application has evolved over time.

## 4.4 Database Migration Management

All database schema changes shall be implemented through
version-controlled migration scripts.

Database objects should never be modified manually within production
environments. Schema changes shall be reproducible by executing the
migration history from an empty database.

Migration scripts should include schema changes, lookup data
initialization where appropriate, and any required data transformation
logic necessary to support application upgrades.

Developers should periodically rebuild local development databases from
the migration history to verify that the complete database schema can be
recreated from source control.

# 5 Coding Standards

## 5.1 General Coding Standards

roject Funding Ledger code should be clear, readable, and maintainable.

Code should favor straightforward implementation over clever or overly
abstract patterns. It should be written so that a future maintainer can
easily understand the purpose, data flow, and business rules being
implemented.

Regardless of how code is produced, all contributions are expected to
meet the same standards for correctness, readability, maintainability,
security, and testing.

General standards:

- Prefer simple, explicit logic.

- Avoid unnecessary abstraction.

- Keep functions focused on a single purpose.

- Avoid duplicating business rules across multiple layers.

- Validate inputs before processing.

- Keep security and authorization checks close to the data being
  accessed.

- Update documentation when implementation decisions materially affect
  system behavior.

## 5.2 Application Code Standards

Application code should use clear and well-defined data structures,
interfaces, and contracts for business entities, API responses, form
inputs, and database interactions.

General standards:

- Use the language’s type system or validation mechanisms to make data
  expectations clear.

- Avoid implicit or unsafe type conversion.

- Handle nullable and optional values intentionally.

- Organize shared data structures and common logic in predictable,
  reusable locations.

- Treat compiler, linter, and static-analysis warnings as issues to
  resolve rather than routinely ignore.

- Document temporary exceptions to normal type-safety or validation
  practices.

## 5.3 User Interface Standards

User interface components should be simple, focused, maintainable, and
easy to test.

The choice of frontend framework, component model, state-management
approach, form library, validation framework, and related middleware may
evolve based on the needs of the application and the experience of
project contributors.

General standards:

- Separate presentation concerns from data access and business logic
  where practical.

- Keep interface components focused and purpose-specific.

- Avoid embedding complex business rules directly in the presentation
  layer.

- Introduce shared components only when meaningful reuse exists.

- Maintain consistent form validation and interaction patterns.

- Avoid unnecessary global state.

- Use accessible labels, controls, navigation, and interaction patterns.

## 5.4 SQL Standards

Database development shall conform to the architecture and data model
defined in the PFL Architecture Design document.

Database schema changes shall be implemented through version-controlled
migration scripts. Changes to the logical data model should be reflected
in the Architecture Design before implementation.

SQL should prioritize clarity, correctness, and maintainability.

## 5.5 Naming Conventions

Application code, database objects, APIs, and documentation should use
the terminology and business entity names defined in the PFL Functional
Specification and Architecture Design.

Naming should be consistent across the application, database, API, and
documentation.

Business entity names should align with the terminology used in the
Functional

## 5.6 Error Handling

Errors should be handled intentionally and presented clearly.

Application errors should not expose sensitive system details to end
users. User-facing messages should explain what happened and, when
possible, what action the user can take.

Error handling standards:

- Validate user input before database operations.

- Handle failed imports gracefully.

- Provide clear messages for Mapping Exception and validation failures.

- Log technical details needed for troubleshooting.

- Avoid swallowing errors silently.

- Do not expose credentials, stack traces, or internal database details
  to users.

## 5.7 Logging Standards

Logging should support troubleshooting, traceability, performance
analysis, and operational awareness without capturing unnecessary
sensitive information.

Application logs should record meaningful technical events.
Business-significant actions should be recorded through the Audit Log
where required by the Architecture Design.

Logging standards:

- Log import processing outcomes.

- Log unexpected application errors.

- Log security-relevant failures.

- Log long-running or failed database operations where practical.

- Capture basic timing information for imports, file processing, API
  calls, and other material workflows.

- Include request, import batch, job, or correlation identifiers where
  appropriate to support traceability across related events.

- Do not log passwords, API keys, access tokens, or sensitive
  credentials.

- Avoid logging confidential financial detail unless necessary for
  troubleshooting.

- Use the Audit Log for material business actions, permission changes,
  mapping changes, document lifecycle events, and Funding Source
  assignment changes.

Performance logging should be lightweight and should not materially
affect application performance.

## 5.8 Documentation Standards

Technical documentation shall be maintained as part of the software
development process. Documentation should evolve with the application to
ensure that architectural decisions, business rules, and implementation
guidance remain accurate and current.

Documentation standards:

- Update documentation when implementing significant functional,
  architectural, or database changes.

- Keep comments concise and focused on explaining why rather than what
  the code does.

- Document public APIs, database functions, and non-obvious business
  logic.

- Remove or update obsolete documentation when behavior changes.

- Ensure examples and code snippets remain consistent with the current
  implementation.

Software changes are not considered complete until the corresponding
documentation has been reviewed and updated where appropriate.

# 6 Database Development

## 6.1 Schema Migration Process

All database schema changes shall be implemented through
version-controlled migration scripts.

Migration scripts should be incremental, repeatable, and capable of
creating or updating the database schema without manual intervention.
Changes to the logical data model should be reflected in the
Architecture Design before implementation.

Direct modification of production database objects outside the migration
process should be avoided.

## 6.2 Seed Data

Development environments may include seed data to support application
development and testing.

Seed data should represent realistic business scenarios while avoiding
confidential or production information. Seed data should be reproducible
and maintained under version control where practical.

## 6.3 Reference Data

Reference data used by the application should be maintained through
controlled database scripts or administrative functions rather than
direct database updates.

Changes to reference data that affect application behavior should be
documented and version controlled.

## 6.4 Database Version Control

Database schema definitions, migration scripts, seed data, and
supporting database objects shall be maintained under version control
together with the application source code.

Each application release should correspond to a known database schema
version that can be recreated from the migration history.

## 6.5 Row-Level Security Development

Row-Level Security (RLS) policies shall be implemented consistently with
the authorization model defined in the Architecture Design.

Security policies should be developed, tested, and validated as part of
normal application development. Changes affecting authorization behavior
should be verified using representative user roles before deployment.

The logical security model and authorization rules are defined in the
Architecture Design and should not be duplicated within this document.

# 7 Testing Strategy

## 7.1 Testing Philosophy

The Project Funding Ledger shall be developed using a test-first mindset
in which automated testing is considered an integral part of software
development rather than a separate activity.

The automated testing framework is considered a core component of the
application architecture and shall be maintained with the same
discipline as the application source code. The testing harness shall
evolve with the application to provide increasing confidence in the
correctness, stability, and maintainability of the system.

No software development task is considered complete until the
corresponding automated tests have been implemented, executed
successfully, and committed with the associated source code.

The objective of the testing strategy is to ensure that application
functionality remains reliable as the system evolves and that future
enhancements do not unintentionally alter existing behavior.

The automated testing framework should provide confidence that:

- New functionality operates as intended.

- Existing functionality continues to operate correctly.

- Business rules are enforced consistently.

- Database changes do not introduce unintended behavior.

- Security policies continue to function correctly.

- Financial Transaction imports remain reliable across supported
  scenarios.

- Refactoring can be performed safely without introducing regressions.

Testing principles include:

- Automated testing is part of software development, not a separate
  activity.

- Automated tests shall be maintained under version control.

- Every reported defect should result in one or more automated
  regression tests where practical.

- Automated tests should execute repeatedly without manual intervention.

- Testing should support continuous improvement of the application
  throughout its lifecycle.

## 7.2 Unit Testing

Unit tests verify the behavior of individual software components and
business rules in isolation.

Every significant business rule should be supported by one or more
automated unit tests. Unit tests should execute quickly, produce
repeatable results, and avoid dependencies on external services whenever
practical.

Unit testing should focus on:

- Business rule validation

- Data validation

- Financial calculations

- Funding Source assignment logic

- Mapping Rule evaluation

- Utility functions

- Error handling

## 7.3 Integration Testing

Integration testing verifies that application components operate
correctly when interacting with one another.

Integration tests should validate interactions among the application,
database, authentication services, storage services, and external
interfaces.

Integration testing should include:

- Database operations

- Authentication and authorization

- Row-Level Security

- REST API endpoints

- Supporting Document storage

- Audit Log generation

- End-to-end application workflows

## 7.4 Data Import Testing

The Financial Transaction import process represents one of the
application's most critical business functions and shall receive
comprehensive automated testing.

Import testing should verify:

- Successful imports

- Invalid import files

- Duplicate detection

- Required field validation

- Mapping Rule execution

- Mapping Exception creation

- Import Batch creation

- Audit Log generation

- Import rollback behavior when errors occur

Representative import datasets should be maintained to support
repeatable testing of both normal and exceptional processing scenarios.

## 7.5 User Acceptance Testing

User Acceptance Testing validates that the application satisfies the
business requirements defined in the Functional Specification.

Testing should confirm that users can successfully perform expected
business workflows and that the application behaves consistently with
documented functional requirements.

User Acceptance Testing should include representative scenarios
covering:

- Project management

- Funding Source management

- Financial Transaction inquiry

- Supporting Document management

- Reporting Obligation tracking

- Import administration

- Security and authorization

- Dashboard and reporting functionality

## 7.6 Regression Testing

Regression testing ensures that previously implemented functionality
continues to operate correctly as the application evolves.

Automated regression tests should be executed following significant
application changes and before production releases.

Every corrected defect should, where practical, result in one or more
automated regression tests to prevent recurrence.

The regression test suite represents the cumulative knowledge of the
application. Every implemented feature, corrected defect, and clarified
business rule should strengthen the test suite, ensuring that the
application's reliability increases over time.

## 7.7 Test Data Management

Development and testing shall utilize representative datasets that
exercise the application's primary business processes and edge cases.

Test datasets should include scenarios covering:

- Multiple Projects

- Multiple Funding Sources

- Imported Financial Transactions

- Valid and invalid import files

- Mapping Rules and Mapping Exceptions

- Funding Adjustments

- User roles and Project Permissions

- Supporting Documents

- Historical accounting scenarios

- Error conditions and recovery scenarios

Test data should be reproducible, maintained under version control where
practical, and shall not contain confidential production information
unless specifically authorized and appropriately protected.

# 8 Build and Deployment

## 8.1 Build Process

The Project Funding Ledger shall support a repeatable build process that
produces consistent application artifacts from the version-controlled
source code.

Build failures should be resolved before software is deployed to shared
testing or production environments.

## 8.2 Development Deployment

Development deployments provide an environment for ongoing
implementation, debugging, and testing.

Development environments may evolve as the application matures and
should support rapid iteration while remaining consistent with the
application's architectural design.

## 8.3 Test Deployment

A test environment should be used to validate significant application
changes before production deployment.

Testing should include verification that new functionality operates
correctly and that existing functionality continues to perform as
expected.

## 8.4 Production Deployment

Production deployments should be performed using a repeatable deployment
process that minimizes operational risk.

Application releases should be based on tested source code and
associated database migrations.

## 8.5 Release Management

Application releases should be incremental and should include
corresponding updates to source code, database migrations, automated
tests, and documentation where appropriate.

Each release should represent a stable and deployable version of the
application.

## 8.6 Rollback Procedures

Deployment planning should consider the ability to recover from
unsuccessful releases.

Where practical, application releases should support restoration of the
previous stable version or other appropriate recovery procedures.

# 9 Security Development

## 9.1 Secure Development

Security should be considered throughout the software development
lifecycle rather than added after implementation.

Application features should be designed and implemented in a manner
consistent with the security architecture defined in the PFL
Architecture Design document.

## 9.2 Secrets Management

Sensitive information, including passwords, API keys, access tokens,
encryption keys, and connection credentials, shall not be stored within
application source code or committed to version control.

Environment-specific configuration should be maintained outside the
application source code.

## 9.3 Authentication and Authorization

Authentication and authorization shall be implemented in accordance with
the security architecture defined in the PFL Architecture Design
document.

Changes affecting authentication, authorization, or Row-Level Security
should be verified through appropriate testing prior to deployment.

## 9.4 Secure Coding Practices

Software should be developed using generally accepted secure coding
practices appropriate for the application.

Development should include appropriate input validation, error handling,
access control, and protection of sensitive information.

Potential security issues identified during development should be
addressed before production deployment.

## 9.5 Dependency Management

Third-party libraries and frameworks should be actively maintained and
obtained from trusted sources.

Dependencies should be periodically reviewed and updated to address
security vulnerabilities, compatibility issues, and long-term
maintainability.

# 10 Maintenance and Continuous Improvement

## 10.1 Maintaining the Development Plan

This Development Plan should be reviewed periodically and updated as the
project's development practices evolve.

Changes to development practices should be documented here without
duplicating business requirements, implementation strategy, or
architectural decisions maintained in the other PFL documentation.

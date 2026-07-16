# Project Funding Ledger

The **Project Funding Ledger (PFL)** is an open source funding visibility and governance platform designed for fiscally sponsored organizations.

The PFL provides project leaders, fiscal sponsors, and authorized stakeholders with a clear understanding of project funding, governing agreements, spending authority, financial activity, reporting obligations, and supporting documentation.

The PFL is **not an accounting system**. It complements existing accounting systems by organizing project funding information in a way that is meaningful and accessible to project communities.

## Why the Project Funding Ledger?

Open source projects often struggle to answer seemingly simple questions:

- How much funding does our project actually have?
- What agreements govern our funding?
- What can we spend today?
- What expenses have already been processed?
- What reporting obligations do we have?
- Where are the supporting documents?

Traditional accounting systems are designed to support accurate financial reporting, accounting controls, and regulatory compliance. They are not designed to provide project-centered funding visibility.

The Project Funding Ledger bridges that gap.

## Project Goals

The PFL is being designed to provide:

- Project funding visibility
- Point-in-time spending authority
- Agreement and contract visibility
- Reporting obligation management
- Supporting document organization
- Secure, project-based access
- Transparent financial activity
- Complete audit history

## System Overview

![Three Core Financial Systems](docs/images/three-core-financial-systems.png)

## Project Status

The Project Funding Ledger is currently in the architecture and design phase.

The project is being developed in the open, and community participation is encouraged from the beginning.

## Planned Architecture

The Project Funding Ledger is being designed around a PostgreSQL database hosted on Supabase.

The frontend technology stack has intentionally not been selected. Implementation technologies for the user interface and application layer will be evaluated during development based on project requirements, contributor expertise, maintainability, accessibility, security, and long-term sustainability.

| Component | Current Direction |
|---|---|
| Database | PostgreSQL |
| Backend platform | Supabase |
| Authentication | Supabase Auth |
| Object storage | Supabase Storage |
| User interface | To be determined |

## Documentation

Project documentation is maintained in the [`docs/`](docs/) directory.

Current documentation areas include:

- Functional Specification
- Architecture Design
- Development Roadmap and Implementation Strategy
- Development Plan
- Architecture Decision Records

## Contributing

Community participation is welcome, including contributions involving:

- Software development
- Product and workflow design
- User experience and accessibility
- Database architecture
- Security and privacy
- Testing
- Documentation
- Fiscal sponsorship operations

Detailed contribution guidelines will be added as the project develops.

## License

Project Funding Ledger is licensed under the BSD 3-Clause License.

See the LICENSE file for details.

## About NumFOCUS

The Project Funding Ledger is initially being developed to improve funding visibility and governance for open source projects operating under NumFOCUS fiscal sponsorship.

The longer-term vision is to create a reusable platform that can benefit fiscally sponsored communities more broadly.

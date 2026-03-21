# sdd-cash-manager Solution Architecture

This document outlines the solution architecture for the sdd-cash-manager system, using the C4 model for visualization. The system is designed as a self-contained application with a clear separation of concerns across different layers and components.

## Level 1: System Context

This diagram shows the sdd-cash-manager system as a whole and its interaction with external users.

```plantuml
@startuml
!includeurl https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

title sdd-cash-manager System Context

' Level 1: System Context
System_Boundary(system_context_boundary, "sdd-cash-manager System Context") {
    Person(user, "User", "Interacts with the system to manage finances.")
    System(cash_management_system, "Cash Management System", "Manages financial accounts and transactions.")
    Rel(user, cash_management_system, "Uses", "HTTPS")
}
@enduml
```

## Level 2: Container Diagram

This diagram zooms into the `Cash Management System` to show its main deployment containers: the API Application and the Database.

```plantuml
@startuml
!includeurl https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

title sdd-cash-manager Container Diagram

' Level 2: Containers within the System
System_Boundary(system_boundary, "sdd-cash-manager Solution") {
    ContainerDb(database_container, "Database", "PostgreSQL/SQLite", "Stores financial account and transaction data.")

    System_Boundary(api_container_boundary, "API Container") {
        Container(api_app, "API Application", "Python/FastAPI", "Provides a RESTful API for the cash management system.")
    }

    ' Level 2 Relationships
    Rel(api_app, database_container, "Reads from and writes to", "SQL")
}
@enduml
```

## Level 3: Component Diagram (API Application)

This diagram details the components within the `API Application` container.

```plantuml
@startuml
!includeurl https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title sdd-cash-manager Component Diagram (API Application)

' Level 3: Components within the API Container
Boundary(api_component_boundary, "API Components") {
    Component(api_routers, "API Routers", "Python", "Handles incoming HTTP requests, routing, and basic validation.")
    Component(service_layer, "Service Layer", "Python", "Core business logic: account management, transaction processing.")
    Component(data_access_layer, "Data Access Layer", "Python/SQLAlchemy", "Manages database interactions, ORM models, and session management.")
    Component(shared_components, "Shared Components", "Python", "Configuration, authentication (JWT), utilities.")
}

' Level 3 Relationships
Rel(api_routers, service_layer, "Uses", "Dependency Injection")
Rel(service_layer, data_access_layer, "Uses", "Dependency Injection")
Rel(service_layer, shared_components, "Uses", "Dependency Injection")
Rel(api_routers, shared_components, "Uses", "Dependency Injection")
@enduml
```

## Architectural Overview

The sdd-cash-manager is designed with a layered architecture:

1. **User (Person):** Interacts with the system through an HTTPS interface.
2. **API Application (Container):** A Python/FastAPI application serving as the primary interface for client interactions. It handles request routing, business logic orchestration, and data persistence.
   - **API Routers (Component):** The entry points for requests, responsible for request parsing, validation, and delegating tasks to the service layer.
   - **Service Layer (Component):** Houses the core business logic, including account management and transaction processing, ensuring financial integrity.
   - **Data Access Layer (Component):** Manages all interactions with the database using SQLAlchemy, including defining models and handling sessions.
   - **Shared Components (Component):** Contains cross-cutting concerns such as configuration loading, authentication mechanisms (e.g., JWT), and utility functions.
3. **Database (Container):** A persistent data store, using PostgreSQL in production and defaulting to SQLite for development. It stores all financial data.

This architecture promotes modularity, testability, and maintainability.

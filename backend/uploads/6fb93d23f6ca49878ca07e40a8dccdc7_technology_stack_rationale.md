# Technology Stack Rationale

## Backend Framework: FastAPI
FastAPI was selected due to its high performance and built-in support for asynchronous
programming. It also provides automatic OpenAPI documentation, which improved
developer onboarding.

## Database: PostgreSQL
PostgreSQL was chosen for its strong consistency guarantees and support for complex queries.
It also aligns with the company’s existing infrastructure.

## Why Not MongoDB?
MongoDB was evaluated but rejected because:
- Most data had relational characteristics.
- Strong transactional consistency was required.
- Existing team expertise was stronger in SQL.

## Caching Strategy
Redis is used as a shared cache across services to reduce database load.

## Security Considerations
- All APIs are protected using JWT authentication.
- Role-based access control is enforced at the service level.

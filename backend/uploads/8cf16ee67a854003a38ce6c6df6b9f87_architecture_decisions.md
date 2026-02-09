# Architecture Decision Records (ADR)

## Decision: Use Redis instead of RabbitMQ for caching and task coordination

### Context
During the development of Project X, the backend team needed a fast and reliable
mechanism for caching frequently accessed data and coordinating lightweight background tasks.

The primary options evaluated were Redis and RabbitMQ.

### Decision
Redis was selected as the primary in-memory data store.

### Rationale
- Redis provides sub-millisecond latency, which is critical for API response times.
- The system required fast key-value access rather than complex message routing.
- Redis supports simple pub/sub features that were sufficient for our use case.
- Operational overhead for Redis was lower compared to RabbitMQ.

### Trade-offs
- Redis does not guarantee message durability like RabbitMQ.
- This was accepted because the tasks were idempotent and non-critical.

### Outcome
System performance improved by approximately 35%, and operational complexity was reduced.

### Author
Senior Backend Engineer

### Date
2023-08-14

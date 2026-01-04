# Project Best Practices

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:
- Line length: 100 characters (not 79)
- Use type hints for all function signatures
- Document all public functions with docstrings

### Example

```python
def calculate_discount(
    original_price: float,
    discount_percent: float,
    apply_tax: bool = True,
) -> float:
    """
    Calculate the final price after applying discount.
    
    Args:
        original_price: The original price before discount.
        discount_percent: Discount percentage (0-100).
        apply_tax: Whether to apply tax after discount.
        
    Returns:
        The final price after discount (and tax if applicable).
        
    Raises:
        ValueError: If discount_percent is not between 0 and 100.
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")
    
    discounted = original_price * (1 - discount_percent / 100)
    
    if apply_tax:
        TAX_RATE = 0.08  # 8% tax
        discounted *= (1 + TAX_RATE)
    
    return round(discounted, 2)
```

## Git Workflow

### Branch Naming Convention
- `feature/` - New features (e.g., `feature/user-authentication`)
- `bugfix/` - Bug fixes (e.g., `bugfix/login-error`)
- `hotfix/` - Urgent production fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:
```
feat(auth): add OAuth2 support for Google login

- Implement OAuth2 flow for Google
- Add user profile sync from Google
- Update login page with Google button

Closes #123
```

## Testing Requirements

### Unit Tests
- Minimum 80% code coverage
- All new features must have tests
- Mock external dependencies

### Integration Tests
- Test API endpoints end-to-end
- Use test database (not production!)
- Clean up test data after each run

## Security Best Practices

### Never Do
- Store passwords in plain text
- Commit secrets to Git
- Use HTTP for sensitive data
- Trust user input without validation

### Always Do
- Use parameterized queries (prevent SQL injection)
- Validate and sanitize all inputs
- Use HTTPS everywhere
- Implement rate limiting
- Log security events

## Performance Guidelines

### Database Queries
- Always use indexes for frequently queried columns
- Avoid N+1 queries (use eager loading)
- Paginate large result sets
- Monitor slow queries

### API Design
- Use pagination for list endpoints
- Implement caching headers
- Compress responses (gzip)
- Use async operations for I/O

## Monitoring & Logging

### What to Log
- All API requests (method, path, status, duration)
- Authentication events (login, logout, failed attempts)
- Errors and exceptions (with stack traces)
- Business-critical events

### What NOT to Log
- Passwords or secrets
- Full credit card numbers
- Personal health information
- Full session tokens

## Incident Response

### Severity Levels
1. **P1 (Critical)**: Service down, data loss
2. **P2 (Major)**: Significant feature broken
3. **P3 (Minor)**: Small issue, workaround available
4. **P4 (Low)**: Cosmetic or minor inconvenience

### Response Process
1. Acknowledge the incident
2. Assess severity and impact
3. Communicate to stakeholders
4. Implement fix or workaround
5. Post-mortem and prevention

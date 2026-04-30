You are a senior backend engineer.

Task: create a minimal, production-minded FastAPI backend for patient registration.

STRICT REQUIREMENTS:
- Keep code SIMPLE and readable (no overengineering)
- Prefer fewer abstractions over complex patterns
- Every function and class must have a clear purpose
- Add short comments explaining WHY, not WHAT
- Use async FastAPI + SQLAlchemy 2.0
- PostgreSQL
- Include basic audit logging (simple version, no need for full hash chain yet)

Features:
- Create patient endpoint
- Patient model: id, full_name, birth_date, created_at

Architecture:
- Keep it simple: router + service + repository (no deep layers)
- Use dependency injection

Output:
1. File structure
2. Code (split into files, not one file)
3. Short explanation for EACH file:
   - why it exists
   - what problem it solves

IMPORTANT:
- Avoid overengineering
- Avoid unnecessary patterns
- Code must be easy to explain line-by-line in an interview
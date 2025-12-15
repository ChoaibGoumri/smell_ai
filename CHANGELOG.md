# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Fixed - 2025-12-15

#### Docker Import Path Issues
**Problem:**
All microservices (`static_analysis_service`, `report_service`, `ai_analysis_service`, `gateway`) were failing to start in Docker containers with `ModuleNotFoundError: No module named 'webapp'`.

**Root Cause:**
Services used absolute Python imports (e.g., `from webapp.services.staticanalysis.app.routers...`) that worked in local development but failed in Docker. When Docker builds each service with its specific context (e.g., `./webapp/services/staticanalysis`), only that directory is copied into the container, making the full `webapp.services.*` path unavailable.

**Solution:**
- Updated all import statements to use relative imports from the service root (e.g., `from app.routers...`)
- Modified service URL configuration in gateway from localhost to Docker service names
- Commented out local development imports and activated Docker-compatible imports

**Files Modified:**

Static Analysis Service:
- `webapp/services/staticanalysis/app/main.py`
- `webapp/services/staticanalysis/app/routers/detect_smell.py`
- `webapp/services/staticanalysis/app/utils/static_analysis.py`

Report Service:
- `webapp/services/report/app/main.py`
- `webapp/services/report/app/routers/report.py`

AI Analysis Service:
- `webapp/services/aiservice/app/main.py`
- `webapp/services/aiservice/app/routers/detect_smell.py`
- `webapp/services/aiservice/app/utils/model.py`

Gateway:
- `webapp/gateway/main.py` (Updated service URLs from `http://localhost:800X` to `http://service_name:800X`)

**Impact:**
- ✅ All services now start successfully in Docker
- ✅ Gateway can communicate with backend services via Docker network
- ✅ Frontend webapp runs on port 3000
- ⚠️ Local development requires switching import comments back

**Services Running:**
- Gateway: `http://localhost:8000`
- AI Analysis Service: `http://localhost:8001`
- Static Analysis Service: `http://localhost:8002`
- Report Service: `http://localhost:8003`
- Frontend WebApp: `http://localhost:3000`

---

## Future Improvements

- [ ] Implement environment-based import configuration
- [ ] Add automated script to switch between local/Docker modes
- [ ] Use Python's `sys.path` manipulation to avoid manual import switching
- [ ] Consider using relative imports consistently across all environments

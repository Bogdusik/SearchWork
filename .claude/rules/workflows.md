# Common Workflows

### Adding a new job source
1. Create `backend/services/<name>_service.py` — implement `search_jobs(query, location)` returning list of job dicts
2. Import and call it in `backend/routers/jobs.py` alongside existing services
3. Add source name to job card display in `frontend/components/search/job-card.tsx`

### Adding a new backend route
1. Create or extend a router in `backend/routers/`
2. Register it in `backend/main.py` with `app.include_router(...)`
3. Add the corresponding client method in `frontend/lib/` or fetch call in the page

### Adding a new page
1. Create `frontend/app/<page>/page.tsx`
2. Use frosted glass card layout — see `frontend/app/applications/page.tsx` as reference
3. Add nav link in `frontend/components/layout/`

### Testing UI changes
Always start both frontend and backend before testing. Check browser console for API errors.

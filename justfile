# Single entry point for humans and agents.
# Backend expects a venv at backend/venv (see README "Running locally").
set shell := ["bash", "-cu"]

default:
    @just --list

dev-web:
    cd frontend && npm run dev

dev-api:
    cd backend && venv/bin/uvicorn main:app --reload

lint:
    cd frontend && npm run lint

typecheck:
    cd frontend && npx tsc --noEmit

# Backend unit tests with the same dummy env as CI (see evals/manifest.json).
test:
    node scripts/run-evals.mjs --profile test

e2e:
    cd frontend && npm run test:mobile -- --reporter=line

build:
    cd frontend && npm run build

# Deterministic gate. Profiles live in evals/manifest.json.
evals profile="fast":
    node scripts/run-evals.mjs --profile {{profile}}

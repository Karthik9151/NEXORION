# Stage 2 Security and Test Matrix

## Automated coverage

| Control | Test evidence in backend/tests/ |
|---|---|
| Local registration creates user and owner workspace | test_register_sets_server_side_session_and_workspace |
| Authenticated mission draft persistence | test_authenticated_user_can_create_list_and_read_draft_mission |
| Cross-workspace isolation | test_workspace_boundary_hides_another_users_mission |
| CSRF required for mutating mission requests | test_csrf_is_required_for_mutation |
| Non-synthetic source class rejected | test_live_or_observed_scope_is_rejected_and_errors_have_request_id |
| Client cannot supply a terminal state | test_client_cannot_choose_mission_state |
| Logout revokes the server-side session | test_logout_revokes_session |
| Liveness and database readiness are separated | test_health_and_readiness_are_separate |

## Manual/release checks still required

- CI passes on the actual pull request; review installed dependency versions and security advisories.
- Apply the Alembic migration against a real PostgreSQL instance and exercise migration rollback/restore procedures.
- Test multiple workers and concurrent account/session/mission requests against PostgreSQL.
- Validate rate limits, lockout/abuse behavior, registration verification, password reset, session rotation, MFA/SSO needs, and administrator onboarding.
- Validate browser origin/CSRF behavior with the selected frontend origin.
- Configure production secrets outside source control, disable debug mode/docs, enforce TLS at the serving edge, and review proxy/header trust.
- Run dependency scanning, secret scanning, threat modeling, backup/restore, retention/deletion, and operational incident procedures.

No claim of production security certification is made. The delivered tests are a first safety net, not a substitute for the remaining release gates.

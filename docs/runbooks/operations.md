# Production operations runbook

- Updates: use Update Engine validation, staging, migration, activation, and recorded result. Never patch extension files or Core directly.
- Backup: create a scoped Backup Set and require verification before treating it as a recovery point.
- Restore: validate provider and platform compatibility, restore through Recovery, then run readiness and smoke checks.
- Database: use Database and Migration contracts. Manual SQL is not migration history.
- Storage: use Storage scopes and Backup/Recovery. Never delete provider objects behind Media or another owner.
- Queue/Scheduler: inspect their health through approved contracts. Manual retry or trigger requires an explicitly defined permission.
- Plugin/Theme failure: disable through the owning Engine when safe; preserve diagnostics and never repair by changing Core.
- Incident: contain, preserve safe diagnostic identifiers, recover through owning contracts, validate readiness, and add a regression test.
- Credentials: rotate through secure Configuration/provider procedures and never place values in Logs, tickets, or this runbook.
- Startup: backend and frontend are separate supervised processes. Startup does not install or migrate; run `favorite-cms status` during release verification.
- Operator CLI: treat any nonzero `favorite-cms` exit code as failure. Correct the underlying configuration or authorization and retry; never capture passwords or secrets in command arguments or logs.
- Health: liveness indicates the process can respond; readiness indicates required dependencies are usable. Do not treat liveness as readiness.
- PostgreSQL recovery: use an approved PostgreSQL-native backup/restore process. Favorite CMS does not claim provider-validated PostgreSQL restore.
- Mounted Storage: protect and back up the configured durable mount using operator-approved controls. Application removal must not silently remove retained Database or Storage data.
- Recovery validation: verify the Backup Set checksum, platform/database compatibility, restored Storage scopes, extension state, and readiness. The built-in snapshot path is validated with SQLite and isolated mounted Storage; PostgreSQL-native backup/restore remains provider-owned and was not live-tested by the project.

Thresholds, retention, escalation contacts, vendors, and staffing policies are intentionally environment-owned.

## Authorized diagnostics

Public `/health/live` and `/health/ready` responses intentionally contain only overall status and the corresponding boolean. Operators granted `admin.diagnostics.view` can use **Admin → Diagnostics** for a redacted status view composed by Health from owning contracts. Status values mean:

- `healthy`: the owner confirmed availability;
- `degraded`: an optional dependency is impaired;
- `unavailable`: a required boundary failed or is not ready;
- `not configured` or `unknown`: no owner-confirmed provider/value is available.

The private view reports platform version, Database and mounted-Storage provider type, configuration presence (never values), explicit migration and installation state, Theme, Queue/Scheduler, Notification, Update, Recovery, Content SEO, and supported Media mode. It never reports URLs, secrets, credentials, paths, SQL, topology, payloads, or stack traces. Request and error identifiers are safe correlation values; expected API errors retain stable categories such as `authentication_required`, `permission_denied`, `validation_error`, `resource_unavailable`, `conflict`, and `service_unavailable`.

Migration and installation remain explicit CLI actions; diagnostics do not run either operation. Update remains an explicit local-package workflow with no polling or remote repository. Recovery visibility describes only the existing verified boundary: SQLite snapshots plus selected mounted Storage scopes and extension state. PostgreSQL-native recovery and external Storage recovery remain operator/provider responsibilities.

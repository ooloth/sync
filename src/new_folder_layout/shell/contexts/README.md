This folder is where we **compose the runtime** for each environment.

The core (`core/`) depends only on **ports** (interfaces) like `UserRepo` and `EventPublisher`.
The shell (`shell/`) provides concrete **adapters** (Postgres/Kafka/GCS/etc.) that implement those ports.

`contexts/` is the one place where we:

- choose which adapters to use in each environment (prod/dev/test)
- instantiate them in the right order (config → clients → adapters)
- return an `AppContext` object that holds the assembled dependencies

Entry points (HTTP routes, event consumers, CLI commands) should:

- create a context at startup (or per test)
- call core use-cases using `ctx.<dependency>` values
- avoid importing adapters directly

Rule of thumb:

- If it imports SDKs/frameworks/DB drivers, it belongs in the shell.
- If it contains business rules or workflows, it belongs in `core/`.

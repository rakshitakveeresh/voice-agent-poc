# PostgreSQL (TODO)

Draft component for a private Azure Database for PostgreSQL Flexible Server.
The architecture uses PostgreSQL for customer/order records, pgvector knowledge
data, and n8n chat memory; n8n itself remains externally managed.

Choose the server version, SKU, private networking mode, database/schema
provisioning, backups, retention, and secret-delivery approach before
implementation.

# Private Application Gateway (TODO)

Draft component for an Application Gateway with a private frontend IP only and
WAF shown in the architecture. It should forward browser traffic from clients
connected to the private network to the Voice Agent POC Container App and use a
defined TLS certificate and health probe.

Decide the private DNS name, certificate issuance/rotation, WAF policy, and how
users connect to the VNet (for example, through an existing VPN or
ExpressRoute). Do not create a public IP or internet-facing listener. No gateway
resources are implemented yet.

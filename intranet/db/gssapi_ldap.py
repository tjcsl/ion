# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import gssapi
import ldap3
from ldap3.protocol.sasl.sasl import send_sasl_negotiation, abort_sasl_negotiation

NO_SECURITY_LAYER = 1
INTEGRITY_PROTECTION = 2
CONFIDENTIALITY_PROTECTION = 4

ldap3.SASL_AVAILABLE_MECHANISMS.append('GSSAPI')


class GSSAPIConnection(ldap3.Connection):
    def do_sasl_bind(self, controls):
        with self.lock:
            result = None
            if not self.sasl_in_progress:
                self.sasl_in_progress = True
                if self.sasl_mechanism == 'GSSAPI':
                    result = sasl_gssapi(self, controls)
                else:
                    raise ldap3.LDAPSASLMechanismNotSupportedError('requested SASL mechanism not supported')
                self.sasl_in_progress = False
            return result


def sasl_gssapi(connection, controls):
    target_name = gssapi.Name('ldap@' + connection.server.host, gssapi.NameType.hostbased_service)
    ctx = gssapi.SecurityContext(name=target_name, mech=gssapi.MechType.kerberos)
    in_token = None
    try:
        while True:
            out_token = ctx.step(in_token)
            if out_token is None:
                out_token = ''
            result = send_sasl_negotiation(connection, controls, out_token)
            in_token = result['saslCreds']
            try:
                ctx.complete  # This raises an exception if we haven't completed connecting.
                break
            except gssapi.exceptions.MissingContextError:
                pass

        unwrapped_token = ctx.unwrap(in_token)
        if len(unwrapped_token.message) != 4:
            raise ValueError("Incorrect response from server.")

        server_security_layers = unwrapped_token.message[0]
        if not isinstance(server_security_layers, int):
            server_security_layers = ord(server_security_layers)
        if server_security_layers in (0, NO_SECURITY_LAYER):
            if unwrapped_token.message[1:] != '\x00\x00\x00':
                raise ValueError("Server max buffer size must be 0 if no security layer.")
        if not (server_security_layers & NO_SECURITY_LAYER):
            raise ValueError("Server requires a security layer, but we don't support any.")

        client_security_layers = bytearray([NO_SECURITY_LAYER, 0, 0, 0])
        out_token = ctx.wrap(bytes(client_security_layers), False)
        return send_sasl_negotiation(connection, controls, out_token.message)
    except (gssapi.exceptions.GSSError, ValueError):
        abort_sasl_negotiation(connection, controls)
        raise

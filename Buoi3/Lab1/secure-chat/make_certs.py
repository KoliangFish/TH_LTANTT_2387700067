"""Generate a local teaching CA and distinct client identities, no OpenSSL CLI needed."""
import argparse
import base64
import ipaddress
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

ROOT = Path(__file__).resolve().parent


def generate(root=ROOT, force=False):
    root = Path(root)
    if (root / 'certs/ca/ca.key').exists() and not force:
        raise ValueError('Certificates already exist; use --force only to reset the lab')
    now = datetime.now(timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Buoi3 Lab CA')])

    def save(folder, name, key, cert):
        path = root / 'certs' / folder
        path.mkdir(parents=True, exist_ok=True)
        (path / f'{name}.key').write_bytes(key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()))
        (path / f'{name}.crt').write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(days=3650))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), False)
          .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), False)
          .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), True)
          .sign(ca_key, hashes.SHA256()))
    save('ca', 'ca', ca_key, ca)
    for name in ('server', 'alice', 'bob', 'charlie'):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
        builder = (x509.CertificateBuilder().subject_name(subject).issuer_name(ca_name)
                   .public_key(key.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(days=365))
                   .add_extension(x509.BasicConstraints(ca=False, path_length=None), True)
                   .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
                   .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), False)
                   .add_extension(x509.KeyUsage(True, False, True, False, False, False, False, False, False), True)
                   .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH if name == 'server'
                                                       else ExtendedKeyUsageOID.CLIENT_AUTH]), False))
        if name == 'server':
            builder = builder.add_extension(x509.SubjectAlternativeName([
                x509.DNSName('localhost'), x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), False)
        save('server' if name == 'server' else 'client', name, key, builder.sign(ca_key, hashes.SHA256()))
    keys = {room: base64.b64encode(os.urandom(32)).decode() for room in ('general', 'study')}
    (root / 'room_keys.json').write_text(json.dumps(keys, indent=2), encoding='utf-8')
    print('Created CA, server SAN localhost/127.0.0.1, client alice/bob/charlie')
    print('Created room_keys.json for general and study (client-only secret)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        generate(force=args.force)
    except ValueError as exc:
        parser.exit(1, f'{exc}\n')

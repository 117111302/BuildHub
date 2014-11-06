from paramiko import RSAKey, DSSKey


default_values = {
    "dsa": {'bits': 1024},
    "rsa": {'bits': 2048},
}


key_dispatch_table = {
    'dsa': DSSKey,
    'rsa': RSAKey,
}


def generate(filename, ktype='rsa', phrase=''):
    """generating private key
    """
    pub_key = ''
    bits = default_values[ktype]['bits']

    # generating private key
    prv = key_dispatch_table[ktype].generate(bits=bits)
    prv.write_private_key_file(filename, password=phrase)

    # generating public key
    pub = key_dispatch_table[ktype](filename=filename, password=phrase)
    pub_key = "%s %s" % (pub.get_name(), pub.get_base64())
    with open("%s.pub" % filename, 'w') as f:
        f.write(pub_key)

    return pub_key

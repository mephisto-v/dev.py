# --- File: doubleratchet/crypto/__init__.py ---
'''
File: __init__.py
Date: 05/20/2020
Author: Robert Neff
'''

from __future__ import absolute_import
import sys
import os

from abc import ABC, abstractmethod



from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives import padding
from cryptography.exceptions import InvalidSignature

class SerializableIface(ABC):
  """Serializable Interface"""

  @abstractmethod
  def serialize(self):
    """Returns serialized dict of class state."""
    pass

  @classmethod
  @abstractmethod
  def deserialize(cls, serialized_obj):
    """Class instance from serialized class state."""
    pass    



class KDFChainIface(SerializableIface):
  """KDF Chain Interface."""

  @property
  @abstractmethod
  def ck(self):
    """Returns chain key."""
    pass

  @ck.setter
  @abstractmethod
  def ck(self, val):
    """Sets chain key to val."""
    pass

class RootChainIface(KDFChainIface):
  """Root KDF Chain Interface (extends KDFChain Interface)."""

  @abstractmethod
  def ratchet(self, dh_out):
    """Ratchets the KDF chain, updating the chain key."""
    pass



class SymmetricChainIface(KDFChainIface):
  """Symmetric KDF Chain Interface (extends KDFChain Interface)."""

  @abstractmethod
  def ratchet(self):
    """Ratchets the KDF chain, updating the chain key."""
    pass

  @property
  @abstractmethod
  def msg_no(self):
    """Returns the current chain message number (chain length)."""
    pass

  @msg_no.setter
  @abstractmethod
  def msg_no(self, val):
    """Sets the current message number to val."""
    pass


class AEADIFace(ABC):
  """Authenticated Encryption with Associated Data Interface"""

  @staticmethod
  @abstractmethod
  def encrypt(key, pt, associated_data = None):
    """Encrypts plaintext, with associated data authentication, using
      provided key with an AEAD scheme.
    """
    pass

  @staticmethod
  @abstractmethod
  def decrypt(key, ct, associated_data = None):
    """Decrypts ciphertext and authenticates associated data using
      provided key with an AEAD scheme.
    """
    pass

# Note: suggested to use Curve25519 or Curve448
class DHKeyPairIface(SerializableIface):
  """Diffie-Hellman Keypair"""

  @classmethod
  @abstractmethod
  def generate_dh(cls):
    """Generates a new Diffie-Hellman keypair (containing private and 
    public keys)."""
    pass

  @abstractmethod
  def dh_out(self, dh_pk):
    """Returns Diffie-Hellman output from private key and provided peer
    public key."""
    pass

  @property
  @abstractmethod
  def private_key(self):
    """Returns Diffie-Hellman private key."""
    pass

  @property
  @abstractmethod
  def public_key(self):
    """Returns Diffie-Hellman public key."""  
    pass


class DHPublicKeyIface(SerializableIface):
  """Diffie-Hellman Public Key"""

  @abstractmethod
  def pk_bytes(self):
    """Returns Diffie-Hellman public key in byte form."""
    pass

  @abstractmethod
  def is_equal_to(self, dh_pk):
    """Checks if public key is equal to the provided one."""
    pass

  @classmethod
  @abstractmethod
  def from_bytes(cls, pk_bytes):
    """Returns Diffie-Hellman public key instance from byte form
    public key."""
    pass

  @property
  @abstractmethod
  def public_key(self):
    """Returns Diffie-Hellman public key."""
    pass


class AuthenticationFailed(Exception):
  """Decrypting ciphertext with authenticated data failed."""
  pass

# AES256-CBC with HMACSHA256 authentication
class AES256CBCHMAC(AEADIFace):
  """An implementation of the AEAD Interface."""

  KEY_LEN = 32 # 256-bit key
  IV_LEN = 16
  HKDF_LEN = 2 * KEY_LEN + IV_LEN
  TAG_LEN = 32

  @staticmethod
  def encrypt(key, pt, associated_data = None):
    if not isinstance(key, bytes):
      raise TypeError("key must be of type: bytes")
    if not len(key) == AES256GCM.KEY_LEN:
      raise ValueError("key must be 32 bytes")
    if not isinstance(pt, bytes):
      raise TypeError("pt must be of type: bytes")
    if associated_data and not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")

    aes_key, hmac_key, iv = AES256CBCHMAC._gen_keys(key)

    padder = padding.PKCS7(AES256CBCHMAC.IV_LEN * 8).padder()
    padded_pt = padder.update(pt) + padder.finalize()

    aes_cbc = AES256CBCHMAC._aes_cipher(aes_key, iv).encryptor()
    ct = aes_cbc.update(padded_pt) + aes_cbc.finalize()

    tag = hmac(hmac_key, associated_data + ct, SHA256(), default_backend())
    return ct + tag

  @staticmethod
  def decrypt(key, ct, associated_data = None):
    if not isinstance(key, bytes):
      raise TypeError("key must be of type: bytes")
    if not len(key) == AES256GCM.KEY_LEN:
      raise ValueError("key must be 32 bytes")
    if not isinstance(ct, bytes):
      raise TypeError("ct must be of type: bytes")
    if associated_data and not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")

    aes_key, hmac_key, iv = AES256CBCHMAC._gen_keys(key)

    try:
      hmac_verify(hmac_key,
        associated_data + ct[:-SHA256().digest_size],
        SHA256(),
        default_backend(),
        ct[-SHA256().digest_size:] # tag
      )
    except InvalidSignature:
      raise AuthenticationFailed("Invalid ciphertext")

    aes_cbc = AES256CBCHMAC._aes_cipher(aes_key, iv).decryptor()
    pt_padded = aes_cbc.update(ct[:-SHA256().digest_size]) + aes_cbc.finalize()
    
    unpadder = padding.PKCS7(AES256CBCHMAC.IV_LEN * 8).unpadder()
    pt = unpadder.update(pt_padded) + unpadder.finalize()

    return pt

  # Generates AEAD keys using HKDF
  @staticmethod
  def _gen_keys(key):
    hkdf_out = hkdf(
      key, 
      AES256CBCHMAC.HKDF_LEN,
      bytes(SHA256().digest_size),
      b"cbchmac_keys", 
      SHA256(), 
      default_backend()
    )
    
    return hkdf_out[:AES256CBCHMAC.KEY_LEN], \
      hkdf_out[AES256CBCHMAC.KEY_LEN:2*AES256CBCHMAC.KEY_LEN], \
      hkdf_out[-AES256CBCHMAC.IV_LEN:]

  # Returns AES-CBC cipher
  @staticmethod
  def _aes_cipher(aes_key, iv):
    return Cipher(
      algorithms.AES(aes_key),
      modes.CBC(iv),
      backend = default_backend()
    )

# AES256-GCM
class AES256GCM(AEADIFace):
  """An implementation of the AEAD Interface."""
  KEY_LEN = 32 # 256-bit key
  IV_LEN = 16

  @staticmethod
  def encrypt(key, pt, associated_data = None):
    if not isinstance(key, bytes):
      raise TypeError("key must be of type: bytes")
    if not len(key) == AES256GCM.KEY_LEN:
      raise ValueError("key must be 32 bytes")
    if not isinstance(pt, bytes):
      raise TypeError("pt must be of type: bytes")
    if associated_data and not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")    

    aesgcm = AESGCM(key)
    iv = os.urandom(AES256GCM.IV_LEN)
    ct = aesgcm.encrypt(iv, pt, associated_data)

    return ct + iv

  @staticmethod
  def decrypt(key, ct, associated_data = None):
    if not isinstance(key, bytes):
      raise TypeError("key must be of type: bytes")
    if not len(key) == AES256GCM.KEY_LEN:
      raise ValueError("key must be 32 bytes")
    if not isinstance(ct, bytes):
      raise TypeError("ct must be of type: bytes")
    if associated_data and not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")

    try:
      aesgcm = AESGCM(key)
      pt = aesgcm.decrypt(
        ct[-AES256GCM.IV_LEN:], 
        ct[:-AES256GCM.IV_LEN], 
        associated_data
      )
    except InvalidSignature:
      raise AuthenticationFailed("Invalid ciphertext")

    return pt
    


from cryptography.hazmat.primitives import serialization

# DH using Curve448
from cryptography.hazmat.primitives.asymmetric.x448 import X448PrivateKey, X448PublicKey

class DHKeyPair(DHKeyPairIface):
  """An implementation of the DHKeyPair Interface."""
  def __init__(self, dh_pair = None):
    if dh_pair:
      if not isinstance(dh_pair, X448PrivateKey):
        raise TypeError("dh_pair must be of type: X448PrivateKey")
      self._private_key = dh_pair
    else:
      self._private_key = X448PrivateKey.generate()
    self._public_key = self._private_key.public_key()

  @classmethod
  def generate_dh(cls):
    return cls(X448PrivateKey.generate())

  def dh_out(self, dh_pk):
    if not isinstance(dh_pk, DHPublicKey):
      raise TypeError("dh_pk must be of type: DHPublicKey")
  
    return self._private_key.exchange(dh_pk.public_key)

  def serialize(self):
    return {
      "private_key" : self._sk_bytes().hex(),
      "public_key" : pk_bytes(self._public_key).hex()
    }

  @classmethod
  def deserialize(cls, serialized_dh):
    if not isinstance(serialized_dh, dict):
      raise TypeError("serialized_dh must be of type: dict")

    private_key = X448PrivateKey.from_private_bytes(
      bytes.fromhex(serialized_dh["private_key"])
    )
    return cls(private_key)

  @property
  def private_key(self):
    self._private_key

  @property
  def public_key(self):
    return DHPublicKey(self._public_key)

  # Returns private key in bytes form
  def _sk_bytes(self):
    return self._private_key.private_bytes(
      encoding=serialization.Encoding.Raw,
      format=serialization.PrivateFormat.Raw,
      encryption_algorithm=serialization.NoEncryption()
    )


class DHPublicKey(DHPublicKeyIface):
  """An implementation of the DHPublicKey Interface."""
  KEY_LEN = 56

  def __init__(self, public_key):
    if not isinstance(public_key, X448PublicKey):
      raise TypeError("public_key must be of type: X448PublicKey")
    self._public_key = public_key

  def pk_bytes(self):
    return pk_bytes(self._public_key)

  def is_equal_to(self, dh_pk):
    if not isinstance(dh_pk, DHPublicKey):
      raise TypeError("dh_pk must be of type: DHPublicKey")

    return self.pk_bytes() == dh_pk.pk_bytes()

  @classmethod
  def from_bytes(cls, pk_bytes):
    if not isinstance(pk_bytes, bytes):
      raise TypeError("pk_bytes must be of type: bytes")
    if not len(pk_bytes) == DHPublicKey.KEY_LEN:
      raise ValueError("pk_bytes must be 56 bytes")

    return cls(X448PublicKey.from_public_bytes(pk_bytes))

  @property
  def public_key(self):
    return self._public_key

  def serialize(self):
    return {
      "public_key": pk_bytes(self._public_key).hex()
    }
  
  @classmethod
  def deserialize(cls, serialized_pk):
    if not isinstance(serialized_pk, dict):
      raise TypeError("serialized_pk must be of type: dict")

    public_key = X448PublicKey.from_public_bytes(
      bytes.fromhex(serialized_pk["public_key"])
    )
    return cls(public_key)


# Returns public key in bytes form
def pk_bytes(pk):
  return pk.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
  )

from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend



class SymmetricChain(SymmetricChainIface):
  """An implementation of the Symmetric Chain Interface."""
  def __init__(self, ck = None, msg_no = None):
    if ck:
      if not isinstance(ck, bytes):
        raise TypeError("ck must be of type: bytes")
      self._ck = ck
    else:
      self._ck = None

    if msg_no:
      if not isinstance(msg_no, int):
        raise TypeError("msg_no must be of type: int")
      if msg_no < 0:
        raise ValueError("msg_no  must be positive")
      self._msg_no = msg_no
    else:
      self._msg_no = 0

  def ratchet(self):
    if self._ck == None:
      raise ValueError("ck is not initialized")

    mk = hmac(self._ck, b"mk_ratchet", SHA256(), default_backend())
    self._ck = hmac(self._ck, b"ck_ratchet", SHA256(), default_backend())
    
    return mk

  def serialize(self):
    return {
      "ck" : self._ck,
      "msg_no" : self._msg_no
    }

  @classmethod
  def deserialize(cls, serialized_chain):
    if not isinstance(serialized_chain, dict):
      raise TypeError("serialized_chain must be of type: dict")

    return cls(serialized_chain["ck"], serialized_chain["msg_no"])
  
  @property
  def ck(self):
    return self._ck

  @ck.setter
  def ck(self, val):
    self._ck = val

  @property
  def msg_no(self):
    return self._msg_no

  @msg_no.setter
  def msg_no(self, val):
    self._msg_no = val


class RootChain(RootChainIface):
  """An implementation of the Root Chain Interface."""
  KEY_LEN = 32
  DEFAULT_OUTPUTS = 1

  def __init__(self, ck = None):
    if ck:
      if not isinstance(ck, bytes):
        raise TypeError("ck must be of type: bytes")
      if not len(ck) == RootChain.KEY_LEN:
        raise ValueError("ck must be 32 bytes")
      self._ck = ck
    else:
      self._ck = None

  def ratchet(self, dh_out, outputs = DEFAULT_OUTPUTS):
    if not isinstance(dh_out, bytes):
      raise TypeError("dh_out must be of type: bytes")
    if not isinstance(outputs, int):
      raise TypeError("outputs must be of type: int")
    if outputs < 0:
      raise ValueError("outputs must be positive")
    if self._ck == None:
      raise ValueError("ck is not initialized")

    hkdf_out = hkdf(
      dh_out, 
      RootChain.KEY_LEN * (outputs + 1),
      self._ck,
      b"rk_ratchet", 
      SHA256(), 
      default_backend()
    )

    self._rk = hkdf_out[-RootChain.KEY_LEN:]

    keys = []
    for i in range(0, outputs):
      keys.append(hkdf_out[i * RootChain.KEY_LEN:(i + 1) * RootChain.KEY_LEN])

    return keys

  def serialize(self):
    return {
      "ck" : self._ck
    }

  @classmethod
  def deserialize(cls, serialized_chain):
    if not isinstance(serialized_chain, dict):
      raise TypeError("serialized_chain must be of type: dict")

    return cls(serialized_chain["ck"])

  @property
  def ck(self):
    return self._ck

  @ck.setter
  def ck(self, val):
    self._ck=  val

from secrets import choice
import string

from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.hmac import HMAC


# Return HKDF outputs for provided key and params
def hkdf(key, length, salt, info, hash_alg, backend):
  return HKDF(
    algorithm=hash_alg,
    length=length,
    salt=salt,
    info=info,
    backend=backend
  ).derive(key)

# Return HMAC for provided key and params
def hmac(key, data, hash_alg, backend):
  h = HMAC(
    key,
    hash_alg,
    backend=backend
  )
  h.update(data)
  return h.finalize()

# Verifies HMAC signature on provided data
# Raises exception on invalid signature
def hmac_verify(key, data, hash_alg, backend, sig = None):
  h = HMAC(
    key,
    hash_alg,
    backend=backend
  )
  h.update(data)
  return h.verify(sig)

# Return random alpha-numeric string of specified length
def rand_str(n):
  assert(isinstance(n, int))

  return ''.join(choice(
    string.ascii_uppercase + string.digits) for i in range(n))
    


from abc import ABC, abstractmethod


class AEADIFace(ABC):
  """Authenticated Encryption with Associated Data Interface"""

  @staticmethod
  @abstractmethod
  def encrypt(key, pt, associated_data = None):
    """Encrypts plaintext, with associated data authentication, using
      provided key with an AEAD scheme.
    """
    pass

  @staticmethod
  @abstractmethod
  def decrypt(key, ct, associated_data = None):
    """Decrypts ciphertext and authenticates associated data using
      provided key with an AEAD scheme.
    """
    pass


from abc import abstractmethod



# Note: suggested to use Curve25519 or Curve448
class DHKeyPairIface(SerializableIface):
  """Diffie-Hellman Keypair"""

  @classmethod
  @abstractmethod
  def generate_dh(cls):
    """Generates a new Diffie-Hellman keypair (containing private and 
    public keys)."""
    pass

  @abstractmethod
  def dh_out(self, dh_pk):
    """Returns Diffie-Hellman output from private key and provided peer
    public key."""
    pass

  @property
  @abstractmethod
  def private_key(self):
    """Returns Diffie-Hellman private key."""
    pass

  @property
  @abstractmethod
  def public_key(self):
    """Returns Diffie-Hellman public key."""  
    pass


class DHPublicKeyIface(SerializableIface):
  """Diffie-Hellman Public Key"""

  @abstractmethod
  def pk_bytes(self):
    """Returns Diffie-Hellman public key in byte form."""
    pass

  @abstractmethod
  def is_equal_to(self, dh_pk):
    """Checks if public key is equal to the provided one."""
    pass

  @classmethod
  @abstractmethod
  def from_bytes(cls, pk_bytes):
    """Returns Diffie-Hellman public key instance from byte form
    public key."""
    pass

  @property
  @abstractmethod
  def public_key(self):
    """Returns Diffie-Hellman public key."""
    pass





class SymmetricChainIface(KDFChainIface):
  """Symmetric KDF Chain Interface (extends KDFChain Interface)."""

  @abstractmethod
  def ratchet(self):
    """Ratchets the KDF chain, updating the chain key."""
    pass

  @property
  @abstractmethod
  def msg_no(self):
    """Returns the current chain message number (chain length)."""
    pass

  @msg_no.setter
  @abstractmethod
  def msg_no(self, val):
    """Sets the current message number to val."""
    pass



class MsgKeyStorageIface(SerializableIface):
  """Dictionary-like Message Key Storage Interface"""

  @abstractmethod
  def front(self):
    """Returns first (oldest) stored message key."""
    pass

  @abstractmethod
  def lookup(self, key):
    """Returns value for provided key, None if key is not present."""
    pass

  @abstractmethod
  def put(self, key, value):
    """Puts key-value pair in datastructure."""
    pass

  @abstractmethod
  def delete(self, key):
    """Deletes current key and associated value from datastructure."""
    pass

  @abstractmethod
  def count(self):
    """Returns number of message keys stored."""
    pass

  @abstractmethod
  def items(self):
    """Returns list of all (key, value) tuples."""
    pass

  @abstractmethod
  def notify_event(self):
    """Performs storage updates (ex. key deletion) due to Double Ratchet
    event (ex. successful decryption)."""
    pass


from abc import ABC, abstractmethod


class RatchetIface(ABC):
  """Double Ratchet Algorithm Communication Interface"""

  @staticmethod
  @abstractmethod
  def encrypt_message(state, pt, associated_data, aead):
    """Encrypts plaintext from provided state using Double Ratchet algorithm."""
    pass

  @staticmethod
  @abstractmethod
  def decrypt_message(state, msg, associated_data, aead, keypair):
    """Decrypts message ciphertext as provided state using Double 
    Ratchet algorithm."""
    pass

# --- File: doubleratchet/interfaces/serializable.py ---

from abc import ABC, abstractmethod


class SerializableIface(ABC):
  """Serializable Interface"""

  @abstractmethod
  def serialize(self):
    """Returns serialized dict of class state."""
    pass

  @classmethod
  @abstractmethod
  def deserialize(cls, serialized_obj):
    """Class instance from serialized class state."""
    pass


from collections import OrderedDict


class MsgKeyStorage(MsgKeyStorageIface):
  EVENT_THRESH = 5 # a key is deleted when event count reaches threshold

  def __init__(self, skipped_mks = None, event_count = 0):
    if skipped_mks:
      if not isinstance(skipped_mks, OrderedDict):
        raise TypeError("skipped_mks must be of type: OrderedDict")

      self._skipped_mks = skipped_mks
    else:
      self._skipped_mks = OrderedDict()

    if not isinstance(event_count, int):
      raise TypeError("event_count must be of type: int")
    if event_count < 0:
      raise ValueError("event_count must be positive")
    self._event_count = event_count

  def front(self):
    return next(iter(self._skipped_mks))

  def lookup(self, key):
    if key not in self._skipped_mks:
      return None
    return self._skipped_mks[key]

  def put(self, key, value):
    self._skipped_mks[key] = value

  def delete(self, key):
    del self._skipped_mks[key]

  def count(self):
    return len(self._skipped_mks)

  def items(self):
    return self._skipped_mks.items()

  def notify_event(self):
    if len(self._skipped_mks) == 0:
      self._event_count = 0
      return

    # Naive event-based key deletion
    # Every EVENT_THRESH events the first key in the dict is deleted.
    # FIXME:
    # Ideally each key should live for set amount of events in
    # dict (ex. using dict for lifetime lookups and doubly linked list
    # for fast deletion).

    self._event_count = (self._event_count + 1) % MsgKeyStorage.EVENT_THRESH
    if self._event_count == 0:
      del self._skipped_mks[self.front()]

  def serialize(self):
    return {
      "skipped_mks": dict(self._skipped_mks),
      "event_count": self._event_count
    }
  
  @classmethod
  def deserialize(cls, serialized_dict):
    if not isinstance(serialized_dict, dict):
      raise TypeError("serialized_dict must be of type: dict")

    return cls(
      OrderedDict(serialized_dict["skipped_mks"]),
      serialized_dict["event_count"]
    )



# Double Ratchet message header
class Header:
  INT_ENCODE_BYTES = 4 # number of int bytes use when encoding a header

  def __init__(self, dh_pk, prev_chain_len, msg_no):
    if not isinstance(dh_pk, DHPublicKey):
      raise TypeError("dh_pk must be of type: DHPublicKey")
    if not isinstance(prev_chain_len, int):
      raise TypeError("prev_chain_len must be of type: int")
    if  prev_chain_len < 0:
      raise ValueError("prev_chain_len must be positive")
    if not isinstance(msg_no, int):
      raise TypeError("msg_no must be of type: int")
    if msg_no < 0:
      raise ValueError("msg_no must be positive")

    self._dh_pk = dh_pk
    self._prev_chain_len = prev_chain_len
    self._msg_no = msg_no

  def __bytes__(self):
    header_bytes = self._dh_pk.pk_bytes()
    header_bytes += self._prev_chain_len.to_bytes(
      Header.INT_ENCODE_BYTES, 
      byteorder='little'
    )
    header_bytes += self._msg_no.to_bytes(
      Header.INT_ENCODE_BYTES, 
      byteorder='little'
    )

    return header_bytes

  @classmethod
  def from_bytes(cls, header_bytes):
    if not isinstance(header_bytes, bytes):
      raise TypeError("header_bytes must be of type: bytes")

    if header_bytes == None or \
      len(header_bytes) != DHPublicKey.KEY_LEN + 2 * Header.INT_ENCODE_BYTES:
      raise ValueError("Inva")

    dh_pk = DHPublicKey.from_bytes(header_bytes[:DHPublicKey.KEY_LEN])
    prev_chain_len = int.from_bytes(
      header_bytes[DHPublicKey.KEY_LEN:-Header.INT_ENCODE_BYTES], 
      byteorder='little'
    )
    msg_no = int.from_bytes(
      header_bytes[-Header.INT_ENCODE_BYTES:], 
      byteorder='little'
    )
    
    return cls(dh_pk, prev_chain_len, msg_no)

  # Getters/setters

  @property
  def dh_pk(self):
    return self._dh_pk

  @property
  def prev_chain_len(self):
    return self._prev_chain_len

  @property
  def msg_no(self):
    return self._msg_no


# Ratchet message
class Message:
  def __init__(self, header, ct):
    if not isinstance(header, Header):
      raise TypeError("header must be of type: Header")
    if not isinstance(ct, bytes):
      raise TypeError("ct must be of type: bytes")

    self._header = header
    self._ct = ct

  # Getters/setters

  @property
  def header(self):
    return self._header

  @property
  def ct(self):
    return self._ct

# Ratchet message (header encryption variant)
class MessageHE:
  def __init__(self, header_ct, ct):
    if not isinstance(header_ct, bytes):
      raise TypeError("header_ct must be of type: bytes")
    if not isinstance(ct, bytes):
      raise TypeError("ct must be of type: bytes")

    self._header_ct = header_ct
    self._ct = ct

  # Getters/setters

  @property
  def header_ct(self):
    return self._header_ct

  @property
  def ct(self):
    return self._ct
    


class MaxSkippedMksExceeded(Exception):
  """Too many message keys skipped/stored in single chain."""
  pass

# Default doubel-ratchet encrypt/decrypt
class Ratchet(RatchetIface):
  """An implementation of the Ratchet Interface."""
  MAX_SKIP = 1000
  MAX_STORE = 2000

  @staticmethod
  def encrypt_message(state, pt, associated_data, aead):
    if not isinstance(state, State):
      raise TypeError("state must be of type: state")
    if not isinstance(pt, str):
      raise TypeError("pt must be of type: string")
    if not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")
    if not issubclass(aead, AEADIFace):
      raise TypeError("aead must implement AEADIface")

    if state.delayed_send_ratchet:
      state.send.ck = state.root.ratchet(state.dh_pair.dh_out(state.dh_pk_r))[0]
      state.delayed_send_ratchet = False

    mk = state.send.ratchet()
    header = Header(state.dh_pair.public_key, 
      state.prev_send_len, state.send.msg_no)
    state.send.msg_no += 1

    ct = aead.encrypt(mk, pt.encode("utf-8"), associated_data + bytes(header))
    return Message(header, ct)

  @staticmethod
  def decrypt_message(state, msg, associated_data, aead, keypair):
    if not isinstance(state, State):
      raise TypeError("state must be of type: state")
    if not isinstance(msg, Message):
      raise TypeError("msg must be of type: Message")
    if not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")
    if not issubclass(aead, AEADIFace):
      raise TypeError("aead must implement AEADIface")
    if not issubclass(keypair, DHKeyPairIface):
      raise TypeError("keypair must implement DHKeyPairIface")

    pt = try_skipped_mks(state, msg.header, msg.ct, associated_data, aead)
    if pt != None:
      state.skipped_mks.notify_event() # successful decrypt event
      return pt

    if not state.dh_pk_r:
      dh_ratchet(state, msg.header.dh_pk, keypair)
    elif not state.dh_pk_r.is_equal_to(msg.header.dh_pk): 
      skip_over_mks(state, msg.header.prev_chain_len, 
        state.dh_pk_r.pk_bytes()) # save mks from old recv chain
      dh_ratchet(state, msg.header.dh_pk, keypair)
    
    skip_over_mks(state, msg.header.msg_no, 
      state.dh_pk_r.pk_bytes())  # save mks on new sending chain

    mk = state.receive.ratchet()
    state.receive.msg_no += 1

    pt_bytes = aead.decrypt(mk, msg.ct, associated_data + bytes(msg.header))
    state.skipped_mks.notify_event() # successful decrypt event
    
    return pt_bytes.decode("utf-8")

# Double ratchet encrypt/decrypt (header encryption variant)
class RatchetHE(RatchetIface):
  """An implementation of the AEAD Interface."""

  MAX_SKIP = 1000
  MAX_STORE = 2000

  @staticmethod
  def encrypt_message_he(state, pt, associated_data, aead):
    if not isinstance(state, State):
      raise TypeError("state must be of type: state")
    if not isinstance(pt, str):
      raise TypeError("pt must be of type: string")
    if not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")
    if not issubclass(aead, AEADIFace):
      raise TypeError("aead must implement AEADIface")

    if state.delayed_send_ratchet:
      state.send.ck, state.next_hk_s = \
        state.root.ratchet(state.dh_pair.dh_out(state.dh_pk_r), 2)
      state.delayed_send_ratchet = False

    mk = state.send.ratchet()
    header = Header(state.dh_pair.public_key, 
      state.prev_send_len, state.send.msg_no)
    hdr_ct = aead.encrypt(state.hk_s, bytes(header), b"")
    
    state.send.msg_no += 1

    ct = aead.encrypt(mk, pt.encode("utf-8"), associated_data + hdr_ct)
    return MessageHE(hdr_ct, ct)


  @staticmethod
  def decrypt_message_he(state, msg, associated_data, aead, keypair):
    if not isinstance(state, State):
      raise TypeError("state must be of type: state")
    if not isinstance(msg, Message):
      raise TypeError("msg must be of type: Message")
    if not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")
    if not issubclass(aead, AEADIFace):
      raise TypeError("aead must implement AEADIface")
    if not issubclass(keypair, DHKeyPairIface):
      raise TypeError("keypair must implement DHKeyPairIface")

    pt = try_skipped_mks_he(state, msg.header_ct, msg.ct, associated_data, aead)
    if pt != None:
      state.skipped_mks.notify_event() # successful decrypt event
      return pt

    header, should_dh_ratchet = decrypt_header(state, msg.header_ct, aead)
    if should_dh_ratchet:
      skip_over_mks(state, header.prev_chain_len,
        state.hk_r) # save mks from old recv chain
      dh_ratchet_he(state, header.dh_pk, keypair)

    skip_over_mks(state, header.msg_no, 
      state.hk_r)  # save mks on new sending chain

    mk = state.receive.ratchet()
    state.receive.msg_no += 1

    pt_bytes = aead.decrypt(mk, msg.ct, associated_data + bytes(header))
    state.skipped_mks.notify_event() # successful decrypt event
    
    return pt_bytes.decode("utf-8")


# Returns decrypted plaintext if message key was stored, else None
def try_skipped_mks(state, header, ct, associated_data, aead):
  hdr_pk_bytes = header.dh_pk.pk_bytes()
  mk = state.skipped_mks.lookup((hdr_pk_bytes, header.msg_no))
  if mk:
    state.skipped_mks.delete((hdr_pk_bytes, header.msg_no))

    pt_bytes = aead.decrypt(mk, ct, associated_data + bytes(header))
    return pt_bytes.decode("utf-8")

  return None

# Returns decrypted plaintext if header receive key was stored, else None.
def try_skipped_mks_he(state, header_ct, ct, associated_data, aead):
  for ((hk_r, msg_no), mk) in state.skipped_mks.items():
    try:
      header_bytes = aead.decrypt(hk_r, header_ct, b"")
    except:
      continue
    
    header = Header.from_bytes(header_bytes)
    if header.msg_no == msg_no:
      state.skipped_mks.delete((hk_r, msg_no))

      pt_bytes = aead.decrypt(mk, ct, associated_data + header_ct)
      return pt_bytes.decode("utf-8")

  return None

# Returns decrypted header trying current and next header receive keys.
# Also returns whether DH-ratchet step is needed, i.e. if next header
# key is used then returns should DH-ratchet
def decrypt_header(state, header_ct, aead):
  if state.hk_r != None: # may not have ratcheted yet
    try:
      header_bytes = aead.decrypt(state.hk_r, header_ct, b"")
      return Header.from_bytes(header_bytes), False
    except:
      pass
    
  try:
    header_bytes = aead.decrypt(state.next_hk_r, header_ct, b"")  
    return Header.from_bytes(header_bytes), True
  except:
    pass

  raise ValueError("Error: invalid header ciphertext.")

# Skips over and stores message keys in the current chain 
# that come before provided end_msg_no. Raises exception
# if too many messages have been skipped in the current
# receiving chain.
def skip_over_mks(state, end_msg_no, map_key):
  new_skip = end_msg_no - state.receive.msg_no
  if new_skip + state.skipped_count > Ratchet.MAX_SKIP:
    raise MaxSkippedMksExceeded("Too many messages skipped in"
      "current chain")
  if new_skip + state.skipped_mks.count() > Ratchet.MAX_STORE:
    raise MaxSkippedMksExceeded("Too many messages stored")
  elif state.receive.ck != None:
    while state.receive.msg_no < end_msg_no:
      mk = state.receive.ratchet()
      if state.skipped_mks.count() == Ratchet.MAX_SKIP: # del keys FIFO
        state.skipped_mks.delete(state.skipped_mks.front())

      state.skipped_mks.put((map_key, state.receive.msg_no), mk)
      state.receive.msg_no += 1
    state.skipped_count += new_skip

# Diffie-Hellman ratchet step
def dh_ratchet(state, dh_pk_r, keypair):
  if state.delayed_send_ratchet: 
    state.send.ck = state.root.ratchet(state.dh_pair.dh_out(dh_pk_r))[0]

  state.dh_pk_r = dh_pk_r
  state.receive.ck = state.root.ratchet(state.dh_pair.dh_out(state.dh_pk_r))[0]
  state.dh_pair = keypair.generate_dh()
  state.delayed_send_ratchet = True
  state.prev_send_len = state.send.msg_no
  state.send.msg_no = 0
  state.receive.msg_no = 0
  state.skipped_count = 0

# Diffie-Hellman ratchet step (header encryption variant)
def dh_ratchet_he(state, dh_pk_r, keypair):
  if state.delayed_send_ratchet:
    state.send.ck, state.next_hk_s = \
      state.root.ratchet(state.dh_pair.dh_out(dh_pk_r), 2)

  state.dh_pk_r = dh_pk_r
  state.hk_s = state.next_hk_s
  state.hk_r = state.next_hk_r
  state.receive.ck, state.next_hk_r = \
    state.root.ratchet(state.dh_pair.dh_out(state.dh_pk_r), 2)
  state.dh_pair = keypair.generate_dh()
  state.delayed_send_ratchet = True
  state.prev_send_len = state.send.msg_no
  state.send.msg_no = 0
  state.receive.msg_no = 0
  state.skipped_count = 0
  


# FIXME: remove dependence on pickle (needed for serializing 
# passed interface implementation classes)
import pickle



# State for a party in double-ratchet algorithm
class State(SerializableIface):
  def __init__(self, keypair, public_key, keystorage, 
      root_chain, symmetric_chain):
    self._dh_pair = None
    self._dh_pk_r = None

    self._root = None
    self._send = None 
    self._receive = None
    self._prev_send_len = 0

    self._hk_s = None
    self._hk_r = None
    self._next_hk_s = None
    self._next_hk_r = None
    
    self._delayed_send_ratchet = False

    self._skipped_mks = None
    self._skipped_count = 0

    self._keypair = keypair
    self._public_key = public_key
    self._keystorage = keystorage
    self._root_chain = root_chain
    self._symmetric_chain = symmetric_chain

  # Sets initial sender state
  def init_sender(self, sk, dh_pk_r):
    self._dh_pair = self._keypair.generate_dh()
    self._dh_pk_r = dh_pk_r

    self._root = self._root_chain()
    self._root.ck = sk
    self._send = self._symmetric_chain()
    self._receive = self._symmetric_chain()
    self._prev_send_len = 0

    self._delayed_send_ratchet = True

    self._skipped_mks = self._keystorage()
    self._skipped_count = 0

  # Sets initial sender state (header encryption variant)
  def init_sender_he(self, sk, dh_pk_r, hk_s, next_hk_r):
    self._dh_pair = self._keypair.generate_dh()
    self._dh_pk_r = dh_pk_r

    self._root = self._root_chain()
    self._root.ck = sk
    self._send = self._symmetric_chain()
    self._receive = self._symmetric_chain()
    self._prev_send_len = 0

    self._hk_s = hk_s
    self._hk_r = None
    self._next_hk_s = None
    self._next_hk_r = next_hk_r

    self._delayed_send_ratchet = True

    self._skipped_mks = self._keystorage()
    self._skipped_count = 0

  # Sets initial receiver state
  def init_receiver(self, sk, dh_pair):
    self._dh_pair = dh_pair
    self._dh_pk_r = None

    self._root = self._root_chain()
    self._root.ck = sk
    self._send = self._symmetric_chain()
    self._receive = self._symmetric_chain()
    self._prev_send_len = 0

    self._delayed_send_ratchet = False

    self._skipped_mks = self._keystorage()
    self._skipped_count = 0

  # Sets initial receiver state (header encryption variant)
  def init_receiver_he(self, sk, dh_pair, next_hk_s, next_hk_r):
    self._dh_pair = dh_pair
    self._dh_pk_r = None

    self._root = self._root_chain()
    self._root.ck = sk
    self._send = self._symmetric_chain()
    self._receive = self._symmetric_chain()
    self._prev_send_len = 0

    self._hk_s = None
    self._hk_r = None
    self._next_hk_s = next_hk_s
    self._next_hk_r = next_hk_r

    self._delayed_send_ratchet = False

    self._skipped_mks = self._keystorage()
    self._skipped_count = 0

  # Getter/setters

  @property
  def dh_pair(self):
    return self._dh_pair
  
  @dh_pair.setter
  def dh_pair(self, val):
    self._dh_pair = val
  
  @property
  def dh_pk_r(self):
    return self._dh_pk_r
  
  @dh_pk_r.setter
  def dh_pk_r(self, val):
    self._dh_pk_r = val

  @property
  def root(self):
    return self._root

  @property
  def send(self):
    return self._send
  
  @property
  def receive(self):
    return self._receive

  @property
  def prev_send_len(self):
    return self._prev_send_len
  
  @prev_send_len.setter
  def prev_send_len(self, val):
    self._prev_send_len = val

  @property
  def hk_s(self):
    return self._hk_s
  
  @hk_s.setter
  def hk_s(self, val):
    self._hk_s = val

  @property
  def hk_r(self):
    return self._hk_r
  
  @hk_r.setter
  def hk_r(self, val):
    self._hk_r = val

  @property
  def next_hk_s(self):
    return self._next_hk_s
  
  @next_hk_s.setter
  def next_hk_s(self, val):
    self._next_hk_s = val

  @property
  def next_hk_r(self):
    return self._next_hk_r
  
  @next_hk_r.setter
  def next_hk_r(self, val):
    self._next_hk_r = val

  @property
  def delayed_send_ratchet(self):
    return self._delayed_send_ratchet

  @delayed_send_ratchet.setter
  def delayed_send_ratchet(self, val):
    self._delayed_send_ratchet = val

  @property
  def skipped_mks(self):
    return self._skipped_mks

  @property
  def skipped_count(self):
    return self._skipped_count

  @skipped_count.setter
  def skipped_count(self, val):
    self._skipped_count = val

  # Serialize class
  def serialize(self):
    return {
      "dh_pair" : self._dh_pair.serialize(),
      "dh_pk_r": self._dh_pk_r.serialize(),
      "root": self._root.serialize(),
      "send": self._send.serialize(),
      "receive": self._receive.serialize(),
      "prev_send_len": self._prev_send_len,
      "hk_s": self._hk_s,
      "hk_r": self._hk_r,
      "next_hk_s": self._next_hk_s,
      "next_hk_r": self._next_hk_r,
      "delayed_send_ratchet": self._delayed_send_ratchet,
      "skipped_mks": self._skipped_mks.serialize(),
      "skipped_count": self._skipped_count,
      "keypair_class": pickle.dumps(self._keypair),
      "pk_class": pickle.dumps(self._public_key),
      "keystorage_class": pickle.dumps(self._keystorage),
      "root_chain_class": pickle.dumps(self._root_chain),
      "symmetric_chain_class": pickle.dumps(self._symmetric_chain)
    }
  
  # Deserialize class
  @classmethod
  def deserialize(cls, serialized_dict):
    if not isinstance(serialized_dict, dict):
      raise TypeError("serialized_dict must be of type: dict")

    keypair_class = pickle.loads(serialized_dict["keypair_class"])
    pk_class = pickle.loads(serialized_dict["pk_class"])
    keystorage_class = pickle.loads(serialized_dict["keystorage_class"])
    root_chain_class = pickle.loads(serialized_dict["root_chain_class"])
    symmetric_chain_class = pickle.loads(serialized_dict["symmetric_chain_class"])

    state = cls(keypair_class, pk_class, keystorage_class, root_chain_class,
      symmetric_chain_class)

    state._dh_pair = keypair_class.deserialize(serialized_dict["dh_pair"])
    state._dh_pk_r = pk_class.deserialize(serialized_dict["dh_pk_r"])
    state._root = root_chain_class.deserialize(serialized_dict["root"])
    state._send = symmetric_chain_class.deserialize(serialized_dict["send"])
    state._receive = symmetric_chain_class.deserialize(serialized_dict["receive"])
    state._prev_send_len = serialized_dict["prev_send_len"]
    state._hk_s = serialized_dict["hk_s"]
    state._hk_r = serialized_dict["hk_r"]
    state._next_hk_s = serialized_dict["next_hk_s"]
    state._next_hk_r = serialized_dict["next_hk_r"]
    state._delayed_send_ratchet = serialized_dict["delayed_send_ratchet"]
    state._skipped_mks = keystorage_class.deserialize(serialized_dict["skipped_mks"])
    state._skipped_count = serialized_dict["skipped_count"]

    return state


import pickle # for saving interface implemented params :|

class DRSession(SerializableIface):
  """Double Ratchet Session.
  
  Provides secure communication with peer session (initialized with same
  shared secrets) using Double Ratchet Algorithm.
  
  Session can be serialized/deserialized if desired.

  Reference: https://signal.org/docs/specifications/doubleratchet/
  """

  def __init__(
      self,
      state: State = None,
      aead: AEADIFace = AES256CBCHMAC, 
      keypair: DHKeyPairIface = DHKeyPair,
      public_key: DHPublicKeyIface = DHPublicKey,
      keystorage: MsgKeyStorageIface = MsgKeyStorage, 
      root_chain: RootChainIface = RootChain,
      symmetric_chain: SymmetricChainIface = SymmetricChain,
      ratchet: RatchetIface = Ratchet) -> None:
    """Sets up new session and necessary Double Ratchet components.

    Args:
      state: State to initialize session with (ex. by deserializing 
        saved session).
      aead: a class implementating AEADIface.
      keypair: an instance of an implementation for DHKeyPairIface.
      public_key: an instance of an implementation for DHPublicKeyIface.
      keystorage: an instance of an implementation for MsgKeyStorageIface.
      root_chain: an instance of an implementation for RootChainIface.
      symmetric_chain: an instance of an implementation for SymmetricChainIface.
      ratchet: an instance of an implementation for RatchetIface.

    Raises:
      TypeError: on incorrect argument type.
    """

    if state and not isinstance(state, State):
      raise TypeError("state must be of type: State")
    if not issubclass(aead, AEADIFace):
      raise TypeError("aead must implement AEADIFace")
    if not issubclass(keypair, DHKeyPairIface):
      raise TypeError("keypair must implement DHKeyPairIface")
    if not issubclass(public_key, DHPublicKeyIface):
      raise TypeError("public_key must implement DHPublicKeyIface")
    if not issubclass(keystorage, MsgKeyStorageIface):
      raise TypeError("keystorage must implement MsgKeyStorageIface")
    if not issubclass(root_chain, RootChainIface):
      raise TypeError("root_chain must implement KDFChainIface")
    if not issubclass(symmetric_chain, SymmetricChainIface):
      raise TypeError("symmetric_chain must implement SymmetricChainIface")
    if not issubclass(ratchet, RatchetIface):
      raise TypeError("ratchet must be of type: RatchetIface")

    self._aead = aead
    self._keypair = keypair
    self._ratchet = ratchet

    if state:
      self._state = state
    else:
      self._state = \
        State(keypair, public_key, keystorage, root_chain, symmetric_chain)

  def setup_sender(self, sk: bytes, dh_pk_r: DHPublicKey) -> None:
    """Sets up session as initial sender.

    Args:
      sk: shared secret key (agreed upon using protocol such as X3DH).
      dh_pk_r: received DH-ratchet public key.

    Raises:
      TypeError: on incorrect argument type.
    """

    if not isinstance(sk, bytes):
      raise TypeError("sk must be of type: bytes")
    if not isinstance(dh_pk_r, DHPublicKey):
      raise TypeError("dh_pk_r must be of type: DHPublicKey")

    self._state.init_sender(sk, dh_pk_r)

  def setup_receiver(self, sk: bytes, dh_pair: DHKeyPair) -> None:
    """Sets up session as initial receiver.

    Args:
      sk: shared secret key (agreed upon using protocol such as X3DH).
      dh_pair: generated DH-ratchet keypair.
    
    Raises:
      TypeError: on incorrect argument type.
    """

    if not isinstance(sk, bytes):
      raise TypeError("sk must be of type: bytes")
    if not isinstance(dh_pair, DHKeyPair):
      raise TypeError("dh_pair must be of type: DHKeyPair")

    self._state.init_receiver(sk, dh_pair)

  def encrypt_message(self, pt: str, associated_data: bytes) -> Message:
    """Returns an encrypted message (header and ciphertext).

    Args:
      pt: plaintext to encrypt.
      associated_data: additional data to bind to ciphertext integrity.

    Raises:
      TypeError: on incorrect argument type.
    """
    
    if not isinstance(pt, str):
      raise TypeError("pt must be of type: string")
    if not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")

    msg = self._ratchet.encrypt_message(
      self._state, pt, associated_data, self._aead)
    return msg

  def decrypt_message(self, msg: Message, associated_data: bytes) -> str:
    """Returns decrypted message plaintext.

    Args:
      msg: header and ciphertext.
      associated_data: additional data bound to ciphertext integrity.

    Raises:
      TypeError: on incorrect argument type.
      AuthenticationFailed: on decryption failure.
    """

    if not isinstance(msg, Message):
      raise TypeError("msg must be of type: Message")
    if not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")

    pt = self._ratchet.decrypt_message(
      self._state, msg, associated_data, self._aead, self._keypair)
    return pt

  def generate_dh_keys(self) -> DHKeyPair:
    """Returns a new DHKeypair."""
    return self._keypair.generate_dh()

  def serialize(self) -> dict:
    """Returns serialized dictionary of session state."""
    return {
      "state" : self._state.serialize(),
      "aead": pickle.dumps(self._aead), # need to use pickle to save class types
      "keypair": pickle.dumps(self._keypair),
      "ratchet": pickle.dumps(self._ratchet)
    }

  @classmethod
  def deserialize(cls, serialized_dict: dict):
    """Returns new instance of DRSession from provided
    serialized state.
    
    Args:
      serialized_dict: serialized session state.
      
    Raises:
      TypeError: on incorrect argument type.
      """

    if not isinstance(serialized_dict, dict):
      raise TypeError("serialized_dict must be of type: dict")

    return cls(
      state=State.deserialize(serialized_dict["state"]),
      aead=pickle.loads(serialized_dict["aead"]), # need to use pickle to save class types
      keypair=pickle.loads(serialized_dict["keypair"]),
      ratchet=pickle.loads(serialized_dict["ratchet"])
    )


class DRSessionHE(SerializableIface):
  """Double Ratchet Session using Header Encryption.
  
  Provides secure communication with peer session (initialized with same
  shared secrets) using Double Ratchet Algorithm with header encryption.
  
  Session can be serialized/deserialized if desired.

  Reference: https://signal.org/docs/specifications/doubleratchet/
  """

  def __init__(
      self,
      state: State = None,
      aead: AEADIFace = AES256GCM, 
      keypair: DHKeyPairIface = DHKeyPair,
      public_key: DHPublicKeyIface = DHPublicKey,
      keystorage: MsgKeyStorageIface = MsgKeyStorage, 
      root_chain: RootChainIface = RootChain,
      symmetric_chain: SymmetricChainIface = SymmetricChain,
      ratchet: RatchetIface = Ratchet) -> None:
    """Sets up new session and necessary Double Ratchet components.

    Args:
      state: State to initialize session with (ex. by deserializing 
        saved session).
      aead: a class implementating AEADIface.
      keypair: an instance of an implementation for DHKeyPairIface.
      public_key: an instance of an implementation for DHPublicKeyIface.
      keystorage: an instance of an implementation for MsgKeyStorageIface.
      root_chain: an instance of an implementation for RootChainIface.
      symmetric_chain: an instance of an implementation for SymmetricChainIface.
      ratchet: an instance of an implementation for RatchetIface.

    Raises:
      TypeError: on incorrect argument type.
    """

    if state and not isinstance(state, State):
      raise TypeError("state must be of type: State")
    if not issubclass(aead, AEADIFace):
      raise TypeError("aead must implement AEADIFace")
    if not issubclass(keypair, DHKeyPairIface):
      raise TypeError("keypair must implement DHKeyPairIface")
    if not issubclass(public_key, DHPublicKeyIface):
      raise TypeError("public_key must implement DHPublicKeyIface")
    if not issubclass(keystorage, MsgKeyStorageIface):
      raise TypeError("keystorage must implement MsgKeyStorageIface")
    if not issubclass(root_chain, RootChainIface):
      raise TypeError("root_chain must implement KDFChainIface")
    if not issubclass(symmetric_chain, SymmetricChainIface):
      raise TypeError("symmetric_chain must implement SymmetricChainIface")
    if not issubclass(ratchet, RatchetIface):
      raise TypeError("ratchet must be of type: RatchetIface")

    self._aead = aead
    self._keypair = keypair
    self._ratchet = ratchet

    if state:
      self._state = state
    else:
      self._state = \
        State(keypair, public_key, keystorage, root_chain, symmetric_chain)

  def setup_sender(self, sk: bytes, dh_pk_r: DHPublicKey, hk_s: bytes,
      next_hk_r: bytes) -> None:
    """Sets up session as initial sender.

    Args:
      sk: shared secret key (agreed upon using protocol such as X3DH).
      dh_pk_r: received DH-ratchet public key.
      hk_s: shared header sending key (agreed upon using protocol such as X3DH).
      next_hk_r: shared next header receiving key (agreed upon using protocol 
        such as X3DH).

    Raises:
      TypeError: on incorrect argument type.
    """

    if not isinstance(sk, bytes):
      raise TypeError("sk must be of type: bytes")
    if not isinstance(dh_pk_r, DHPublicKey):
      raise TypeError("dh_pk_r must be of type: DHPublicKey")
    if not isinstance(hk_s, bytes):
      raise TypeError("hk_s must be of type: bytes")
    if not isinstance(next_hk_r, bytes):
      raise TypeError("next_hk_r must be of type: bytes")

    self._state.init_sender_he(sk, dh_pk_r, hk_s, next_hk_r)

  def setup_receiver(self, sk: bytes, dh_pair: DHKeyPair, 
      next_hk_s: bytes, next_hk_r: bytes) -> None:
    """Sets up session as initial receiver.

    Args:
      sk: shared secret key (agreed upon using protocol such as X3DH).
      dh_pair: generated DH-ratchet keypair.
      next_hk_s: shared next header sending key (agreed upon using protocol 
        such as X3DH).
      next_hk_r: shared next header receiving key (agreed upon using protocol 
        such as X3DH).
    
    Raises:
      TypeError: on incorrect argument type.
    """

    if not isinstance(sk, bytes):
      raise TypeError("sk must be of type: bytes")
    if not isinstance(dh_pair, DHKeyPair):
      raise TypeError("dh_pair must be of type: DHKeyPair")
    if not isinstance(next_hk_s, bytes):
      raise TypeError("next_hk_s must be of type: bytes")
    if not isinstance(next_hk_r, bytes):
      raise TypeError("next_hk_r must be of type: bytes")

    self._state.init_receiver_he(sk, dh_pair, next_hk_s, next_hk_r)

  def encrypt_message(self, pt: str, associated_data: bytes) -> Message:
    """Returns an encrypted message (header and ciphertext).

    Args:
      pt: plaintext to encrypt.
      associated_data: additional data to bind to ciphertext integrity.

    Raises:
      TypeError: on incorrect argument type.
    """
    
    if not isinstance(pt, str):
      raise TypeError("pt must be of type: string")
    if not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")

    msg = self._ratchet.encrypt_message(
      self._state, pt, associated_data, self._aead)
    return msg

  def decrypt_message(self, msg: Message, associated_data: bytes) -> str:
    """Returns decrypted message plaintext.

    Args:
      msg: header and ciphertext.
      associated_data: additional data bound to ciphertext integrity.

    Raises:
      TypeError: on incorrect argument type.
      AuthenticationFailed: on decryption failure.
    """

    if not isinstance(msg, Message):
      raise TypeError("msg must be of type: Message")
    if not isinstance(associated_data, bytes):
      raise TypeError("associated_data must be of type: bytes")

    pt = self._ratchet.decrypt_message(
      self._state, msg, associated_data, self._aead, self._keypair)
    return pt

  def generate_dh_keys(self) -> DHKeyPair:
    """Returns a new DHKeypair."""
    return self._keypair.generate_dh()

  def serialize(self) -> dict:
    """Returns serialized dictionary of session state."""
    return {
      "state" : self._state.serialize(),
      "aead": pickle.dumps(self._aead),
      "keypair": pickle.dumps(self._keypair),
      "ratchet": pickle.dumps(self._ratchet)
    }

  @classmethod
  def deserialize(cls, serialized_dict: dict):
    """Returns new instance of DRSession from provided
    serialized state.
    
    Args:
      serialized_dict: serialized session state.
      
    Raises:
      TypeError: on incorrect argument type.
    """
    if not isinstance(serialized_dict, dict):
      raise TypeError("serialized_dict must be of type: dict")

    return cls(
      state=State.deserialize(serialized_dict["state"]),
      aead=pickle.loads(serialized_dict["aead"]),
      keypair=pickle.loads(serialized_dict["keypair"]),
      ratchet=pickle.loads(serialized_dict["ratchet"])
    )


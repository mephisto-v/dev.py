#ifndef AES_H
#define AES_H

#include <stdint.h>

// AES block size in bytes
#define AES_BLOCK_SIZE 16

// Expanded key size for AES-256 (60 32-bit words)
#define EXPANDED_KEY_SIZE 60

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Encrypt/decrypt data in AES-IGE 256-bit mode.
 * 
 * @param in      Pointer to input data.
 * @param length  Length of the data in bytes (must be multiple of AES_BLOCK_SIZE).
 * @param key     32-byte (256-bit) key.
 * @param iv      32-byte IV (two 16-byte blocks concatenated).
 * @param encrypt 1 for encryption, 0 for decryption.
 * 
 * @return Pointer to newly allocated output buffer (must be freed by caller).
 */
uint8_t *ige256(const uint8_t in[], uint32_t length, const uint8_t key[32], const uint8_t iv[32], uint8_t encrypt);

/**
 * Set the expanded key for AES-256 encryption.
 * 
 * @param key         32-byte (256-bit) key.
 * @param expandedKey Output buffer for expanded key (60 uint32_t words).
 */
void aes256_set_encryption_key(const uint8_t key[32], uint32_t expandedKey[EXPANDED_KEY_SIZE]);

/**
 * Set the expanded key for AES-256 decryption.
 * 
 * @param key         32-byte (256-bit) key.
 * @param expandedKey Output buffer for expanded key (60 uint32_t words).
 */
void aes256_set_decryption_key(const uint8_t key[32], uint32_t expandedKey[EXPANDED_KEY_SIZE]);

/**
 * AES-256 block encryption (ECB mode, one block).
 * 
 * @param in   16-byte input block.
 * @param out  16-byte output block.
 * @param key  Expanded key (60 uint32_t words).
 */
void aes256_encrypt(const uint8_t in[AES_BLOCK_SIZE], uint8_t out[AES_BLOCK_SIZE], const uint32_t key[EXPANDED_KEY_SIZE]);

/**
 * AES-256 block decryption (ECB mode, one block).
 * 
 * @param in   16-byte input block.
 * @param out  16-byte output block.
 * @param key  Expanded key (60 uint32_t words).
 */
void aes256_decrypt(const uint8_t in[AES_BLOCK_SIZE], uint8_t out[AES_BLOCK_SIZE], const uint32_t key[EXPANDED_KEY_SIZE]);

#ifdef __cplusplus
}
#endif

#endif // AES_H

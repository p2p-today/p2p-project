/**
* Base Converter
* ==============
*
* Arbitrary precision base conversion by Daniel Gehriger <gehriger@linkcad.com>
* Permission for use was given `here <https://archive.is/BFA8H#17%>`_.
* This has been heavily modified since copying, has been hardcoded for a specific case, then translated to C.
*/

#ifndef C2P_BASE_CONVERSION
#define C2P_BASE_CONVERSION
#include <math.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
* .. c:var:: const static char *base_58
*
*     This buffer contains all of the characters within the base_58 "alphabet"
*
* .. c:var:: const static char *ascii
*
*     This buffer contains all of the characters within the extended ascii "alphabet"
*/

const static char *base_58 = (char *)"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const static char *ascii   = (char *)"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff";

/**
* .. c:function:: static size_t find_base_58(const char search)
*
*     This is the equivalent of base_58.indexOf(search)
*
*     :param search: The character you would like to search for
*
*     :returns: The index of this character in base_58, or -1
*/

static size_t find_base_58(const char search)  {
    size_t i;
    for (i = 0; i < 58; i++) {
        if (base_58[i] == search)
            return i;
    }
    return -1;
}

/**
* .. c:function:: static unsigned long long from_base_58(const char *str, const size_t len)
*
*     This converts a short base_58 buffer to its ascii equivalent
*
*     :param str: The buffer you wish to convert
*     :param len: The length of the buffer to convert
*
*     :returns: The equivalent integral value
*/

static unsigned long long from_base_58(const char *str, const size_t len) {
    unsigned long long ret = 0;
    unsigned int i;
    for (i = 0; i < len; i++)    {
        ret *= (unsigned long long) 58;
        ret += (unsigned long long) find_base_58(str[i]);
    }
    return ret;
}

/**
* .. c:function:: static unsigned int base2dec(const char *value, const size_t len)
*
*     Converts a small ascii buffer to its equivalent integral value
*
*     :param value: The buffer you wish to convert
*     :param len:   The length of the buffer to convert
*
*     :returns: The equivalent integral value
*/

static unsigned int base2dec(const char *value, const size_t len)  {
    unsigned int result = 0;
    size_t i;
    for (i = 0; i < len; ++i) {
        result <<= 8;
        result += (unsigned char)value[i];
    }

    return result;
}

/**
* .. c:function:: static void dec2base(unsigned int value, char *result, size_t *len)
*
*     Converts an integral value to its equivalent binary buffer, then places this in result and updates len
*
*     :param value:     The value you wish to convert (as an unsigned int)
*     :param result:    The buffer result
*     :param len:       The length of the buffer result
*
*     .. note::
*
*         This uses :c:func:`memmove` to transfer data, so it's helpful if you start with a larger-than-necessary buffer
*/

static void dec2base(unsigned int value, char *result, size_t *len)  {
    size_t pos = 4;
    do  {
        result[--pos] = (unsigned char)value % 256;
        value >>= 8;
    }
    while (value);

    *len = 4 - pos;
    memmove(result, result + pos, *len);
}

/**
* .. c:function:: static char *to_base_58(unsigned long long i, size_t *len)
*
*     Converts an integral value to base_58, then updates len
*
*     :param i:     The value you want to convert
*     :param len:   The length of the generated buffer
*
*     :returns: A buffer containing the base_58 equivalent of ``i``
*
*     .. note::
*
*         The return value needs to have :c:func:`free` called on it at some point
*/

static char *to_base_58(unsigned long long i, size_t *len) {
    size_t pos = 0;
    char *str = (char*)malloc(sizeof(char) * 4);
    while (i)   {
        str[pos++] = base_58[i % 58];
        i /= 58;
        if (pos % 4 == 0)
            str = (char*)realloc(str, pos + 4);
    }
    if (!pos)
        str[0] = base_58[0];
    else    {
        const size_t lim = pos - 1;
        size_t i;
        for (i = 0; i < lim - i; i++)    {
            str[i] ^= str[lim - i];
            str[lim - i] ^= str[i];
            str[i] ^= str[lim - i];
        }
    }
    *len = pos;
    return str;
}

/**
* .. c:function:: static unsigned int divide_58(char *x, size_t *length)
*
*     Divides an ascii buffer by 58, and returns the remainder
*
*     :param x:         The binary buffer you wish to divide
*     :param length:    The length of the buffer
*
*     :returns: An unsigned int which contains the remainder of this division
*/

static unsigned int divide_58(char *x, size_t *length)  {
    const size_t const_length = *length;
    size_t pos = 0;
    char *quotient = (char*) malloc(sizeof(char) * const_length);
    size_t len = 4;
    char dec2base_str[4];
    unsigned int remainder;
    size_t i;

    for (i = 0; i < const_length; ++i) {
        const size_t j = i + 1 + (*length) - const_length;
        unsigned int value;
        if (*length < j)
            break;

        value = base2dec(x, j);

        quotient[pos] = (unsigned char)(value / 58);
        if (pos != 0 || quotient[pos] != ascii[0])  // Prevent leading zeros
            pos++;

        dec2base(value % 58, dec2base_str, &len);
        memmove(x + len, x + j, (*length) - j);
        memcpy(x, dec2base_str, len);

        *length -= j;
        *length += len;
    }

    // calculate remainder
    remainder = base2dec(x, *length);

    // store quotient in 'x'
    memcpy(x, quotient, pos);
    free(quotient);
    *length = pos;

    return remainder;
}

/**
* .. c:function:: static char *ascii_to_base_58_(const char *input, size_t length, size_t *res_len)
*
*     Converts an arbitrary ascii buffer to its base_58 equivalent. The length of this buffer is placed in res_len.
*
*     :param input:     An input buffer
*     :param length:    The length of said buffer
*     :param res_len:   A pointer to the return buffer's length
*
*     :returns: A buffer containing the base_58 equivalent of the provided buffer.
*/

static char *ascii_to_base_58_(const char *input, size_t length, size_t *res_len)    {
    char *c_input = (char*)malloc(sizeof(char) * length);
    size_t res_size;
    size_t pos;
    char *result;

    memcpy(c_input, input, length);
    res_size = ceil(length * 1.4);
    pos = res_size;
    result = (char*)malloc(sizeof(char) * res_size);

    do  {
        result[--pos] = base_58[divide_58(c_input, &length)];
    }
    while (length && !(length == 1 && c_input[0] == ascii[0]));

    free(c_input);

    *res_len = res_size - pos;
    memmove(result, result + pos, *res_len);
    return result;
}

/**
* .. c:function:: static char *ascii_to_base_58(const char *input, size_t length, size_t *res_len, size_t minDigits)
*
*     Converts an arbitrary ascii buffer into its base_58 equivalent. This is largely used for converting hex digests, or
*     other such things which cannot conveniently be converted to an integral.
*
*     :param input:     An input buffer
*     :param length:    The length of said buffer
*     :param res_len:   A pointer to the return buffer's length
*     :param minDigits: The minimum number of base_58 digits you would like to get back
*
*     :returns: A buffer containing the base_58 equivalent of the provided buffer.
*/

static char *ascii_to_base_58(const char *input, size_t length, size_t *res_len, size_t minDigits) {
    char *result = ascii_to_base_58_(input, length, res_len);
    if (length < minDigits) {
        size_t end_zeros = minDigits - *res_len;
        result = (char*)realloc(result, minDigits);
        memmove(result + end_zeros, result, *res_len);
        memset(result, base_58[0], end_zeros);
    }
    return result;
}

#ifdef __cplusplus
}

#endif
#endif

/**
* Base Converter
* ==============
*
* Arbitrary precision base conversion by Daniel Gehriger <gehriger@linkcad.com>
* Permission for use was given `here <http://archive.is/BFA8H#17%>`_.
* This has been heavily modified since copying, has been hardcoded for a specific case, then translated to C.
*/

#include <math.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#ifdef __cplusplus
#include <string>
using namespace std;

extern "C" {
#endif

const static char *base_58 = (char *)"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const static char *ascii   = (char *)"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff";

static inline size_t find_base_58(const char search)  {
    for (size_t i = 0; i < 58; i++) {
        if (base_58[i] == search)
            return i;
    }
    return -1;
}

static inline unsigned long long from_base_58(const char *str, const size_t len) {
    unsigned long long ret = 0;
    for (unsigned int i = 0; i < len; i++)    {
        ret *= (unsigned long long) 58;
        ret += (unsigned long long) find_base_58(str[i]);
    }
    return ret;
}

static inline unsigned int base2dec(const char *value, const size_t len)  {
    unsigned int result = 0;
    for (size_t i = 0; i < len; ++i) {
        result <<= 8;
        result += (unsigned char)value[i];
    }

    return result;
}

static inline void dec2base(unsigned int value, char *result, size_t *len)  {
    size_t pos = 4;
    do  {
        result[--pos] = (unsigned char)value % 256;
        value >>= 8;
    }
    while (value);

    *len = 4 - pos;
    memmove(result, result + pos, *len);
}

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
        for (size_t i = 0; i < lim - i; i++)    {
            str[i] ^= str[lim - i];
            str[lim - i] ^= str[i];
            str[i] ^= str[lim - i];
        }
    }
    *len = pos;
    return str;
}

static unsigned int divide_58(char *x, size_t *length)  {
    const size_t const_length = *length;
    size_t pos = 0;
    char *quotient = (char*) malloc(sizeof(char) * const_length);
    size_t len = 4;
    char dec2base_str[4] = {};

    for (size_t i = 0; i < const_length; ++i) {
        const size_t j = i + 1 + (*length) - const_length;
        if (*length < j)
            break;

        const unsigned int value = base2dec(x, j);

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
    const unsigned int remainder = base2dec(x, *length);

    // store quotient in 'x'
    memcpy(x, quotient, pos);
    free(quotient);
    *length = pos;

    return remainder;
}

static char *ascii_to_base_58_(const char *input, size_t length, size_t *res_len)    {
    char *c_input = (char*)malloc(sizeof(char) * length);
    memcpy(c_input, input, length);

    const size_t res_size = ceil(length * 1.4);
    size_t pos = res_size;
    char *result = (char*)malloc(sizeof(char) * res_size);

    do  {
        result[--pos] = base_58[divide_58(c_input, &length)];
    }
    while (length && !(length == 1 && c_input[0] == ascii[0]));

    free(c_input);

    *res_len = res_size - pos;
    memmove(result, result + pos, *res_len);
    return result;
}

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

static string ascii_to_base_58(string input)   {
    size_t res_size = 0;
    char *c_string = ascii_to_base_58(input.c_str(), input.length(), &res_size, 1);
    string result = string(c_string, res_size);
    free(c_string);
    return result;
}

static inline string to_base_58(unsigned long long i)   {
    size_t len = 0;
    char *temp_str = to_base_58(i, &len);
    string ret = string(temp_str, len);
    free(temp_str);
    return ret;
}

#endif

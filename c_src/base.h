/**
* Base Module
* ===========
*
* This module contains common functions and classes used throughout the rest of the library
*/
#ifndef C2P_PROTOCOL_MAJOR_VERSION
#define CP2P__STR( ARG ) #ARG
#define CP2P__STR__( ARG ) CP2P__STR(ARG)

#define C2P_PROTOCOL_MAJOR_VERSION 0
#define C2P_PROTOCOL_MINOR_VERSION 5
#define C2P_NODE_VERSION 607
#define C2P_VERSION CP2P__STR__(C2P_PROTOCOL_MAJOR_VERSION) "." CP2P__STR__(C2P_PROTOCOL_MINOR_VERSION) "." CP2P__STR__(C2P_NODE_VERSION)
/**
* .. c:macro:: C2P_PROTOCOL_MAJOR_VERSION
*
*     This macro defines the major version number. A change here indicates a major change or release, and may be breaking. In a scheme x.y.z, it would be x
*
* .. c:macro:: C2P_PROTOCOL_MINOR_VERSION
*
*     This macro defines the minor version number. It refers specifically to minor protocol revisions, and all changes here are API compatible (after 1.0), but not compatbile with other nodes. In a scheme x.y.z, it would be y
*
* .. c:macro:: C2P_NODE_VERSION
*
*     This macro defines the patch version number. It refers specifically to node policies, and all changes here are backwards compatible. In a scheme x.y.z, it would be z
*
* .. c:macro:: C2P_VERSION
*
*     This macro is a string literal. It combines all the above macros into a single string. It will generate whatever a string literal would normally be interpreted as in that context.
*
* .. c:macro:: C2P_DEBUG_FLAG
*
*     This macro indicates whether cp2p should generate debug prints. If you define this as anything it will print
*/

#ifdef CP2P_DEBUG_FLAG
    #define CP2P_DEBUG(...) printf(__VA_ARGS__);
#else
    #define CP2P_DEBUG(...)
#endif

//This macro was taken from:
//http://www.pixelbeat.org/programming/gcc/static_assert.html
//under the GNU All-Permissive License, which is included below:
//Copyright © Pádraig Brady 2008
//
//Copying and distribution of this file, with or without modification,
//are permitted in any medium without royalty provided the copyright
//notice and this notice are preserved.
#define ASSERT_CONCAT_(a, b) a##b
#define ASSERT_CONCAT(a, b) ASSERT_CONCAT_(a, b)
/* These can't be used after statements in c89. */
#ifdef __COUNTER__
  #define STATIC_ASSERT(e,m) \
    ;enum { ASSERT_CONCAT(static_assert_, __COUNTER__) = 1/(int)(!!(e)) }
#else
  /* This can't be used twice on the same line so ensure if using in headers
   * that the headers are not included twice (by wrapping in #ifndef...#endif)
   * Note it doesn't cause an issue when used on same line of separate modules
   * compiled with gcc -combine -fwhole-program.  */
  #define STATIC_ASSERT(e,m) \
    ;enum { ASSERT_CONCAT(assert_line_, __LINE__) = 1/(int)(!!(e)) }
#endif
//End macro

#include <time.h>

#ifdef _cplusplus
extern "C" {
#endif

STATIC_ASSERT(sizeof(size_t) >= 4, "Size of strings is too small to easily meet protocol specs");

#define BROADCAST_FLAG (unsigned char *) "\x00"
#define BROADCAST_LEN (size_t) 1
#define RENEGOTIATE_FLAG (unsigned char *) "\x01"
#define RENEGOTIATE_LEN (size_t) 1
#define WHISPER_FLAG (unsigned char *) "\x02"
#define WHISPER_LEN (size_t) 1
#define PING_FLAG (unsigned char *) "\x03"
#define PING_LEN (size_t) 1
#define PONG_FLAG (unsigned char *) "\x04"
#define PONG_LEN (size_t) 1
#define COMPRESSION_FLAG (unsigned char *) "\x01"
#define COMPRESSION_LEN (size_t) 1
#define HANDSHAKE_FLAG (unsigned char *) "\x05"
#define HANDSHAKE_LEN (size_t) 1
#define NOTIFY_FLAG (unsigned char *) "\x06"
#define NOTIFY_LEN (size_t) 1
#define PEERS_FLAG (unsigned char *) "\x07"
#define PEERS_LEN (size_t) 1
#define REQUEST_FLAG (unsigned char *) "\x08"
#define REQUEST_LEN (size_t) 1
#define RESEND_FLAG (unsigned char *) "\x09"
#define RESEND_LEN (size_t) 1
#define RESPONSE_FLAG (unsigned char *) "\x0A"
#define RESPONSE_LEN (size_t) 1
#define STORE_FLAG (unsigned char *) "\x0B"
#define STORE_LEN (size_t) 1
#define RETRIEVE_FLAG (unsigned char *) "\x0C"
#define RETRIEVE_LEN (size_t) 1
#define BZ2_FLAG (unsigned char *) "\x10"
#define BZ2_LEN (size_t) 1
#define GZIP_FLAG (unsigned char *) "\x11"
#define GZIP_LEN (size_t) 1
#define LZMA_FLAG (unsigned char *) "\x12"
#define LZMA_LEN (size_t) 1
#define ZLIB_FLAG (unsigned char *) "\x13"
#define ZLIB_LEN (size_t) 1
#define BWTC_FLAG (unsigned char *) "\x14"
#define BWTC_LEN (size_t) 1
#define CONTEXT1_FLAG (unsigned char *) "\x15"
#define CONTEXT1_LEN (size_t) 1
#define DEFSUM_FLAG (unsigned char *) "\x16"
#define DEFSUM_LEN (size_t) 1
#define DMC_FLAG (unsigned char *) "\x17"
#define DMC_LEN (size_t) 1
#define FENWICK_FLAG (unsigned char *) "\x18"
#define FENWICK_LEN (size_t) 1
#define HUFFMAN_FLAG (unsigned char *) "\x19"
#define HUFFMAN_LEN (size_t) 1
#define LZJB_FLAG (unsigned char *) "\x1A"
#define LZJB_LEN (size_t) 1
#define LZJBR_FLAG (unsigned char *) "\x1B"
#define LZJBR_LEN (size_t) 1
#define LZP3_FLAG (unsigned char *) "\x1C"
#define LZP3_LEN (size_t) 1
#define MTF_FLAG (unsigned char *) "\x1D"
#define MTF_LEN (size_t) 1
#define PPMD_FLAG (unsigned char *) "\x1E"
#define PPMD_LEN (size_t) 1
#define SIMPLE_FLAG (unsigned char *) "\x1F"
#define SIMPLE_LEN (size_t) 1
#define SNAPPY_FLAG (unsigned char *) "\x20"
#define SNAPPY_LEN (size_t) 1

static size_t NUM_RESERVED = 0x30;

static unsigned char *RESERVED_FLAGS[] = {
    BROADCAST_FLAG,
    RENEGOTIATE_FLAG,
    WHISPER_FLAG,
    PING_FLAG,
    PONG_FLAG,
    HANDSHAKE_FLAG,
    NOTIFY_FLAG,
    PEERS_FLAG,
    REQUEST_FLAG,
    RESEND_FLAG,
    RESPONSE_FLAG,
    STORE_FLAG,
    RETRIEVE_FLAG,
    (unsigned char *) "\x0D",
    (unsigned char *) "\x0E",
    (unsigned char *) "\x0F",
    BZ2_FLAG,
    GZIP_FLAG,
    LZMA_FLAG,
    ZLIB_FLAG,
    BWTC_FLAG,
    CONTEXT1_FLAG,
    DEFSUM_FLAG,
    DMC_FLAG,
    FENWICK_FLAG,
    HUFFMAN_FLAG,
    LZJB_FLAG,
    LZJBR_FLAG,
    LZP3_FLAG,
    MTF_FLAG,
    PPMD_FLAG,
    SIMPLE_FLAG,
    SNAPPY_FLAG,
    (unsigned char *) "\x21",
    (unsigned char *) "\x22",
    (unsigned char *) "\x23",
    (unsigned char *) "\x24",
    (unsigned char *) "\x25",
    (unsigned char *) "\x26",
    (unsigned char *) "\x27",
    (unsigned char *) "\x28",
    (unsigned char *) "\x29",
    (unsigned char *) "\x2A",
    (unsigned char *) "\x2B",
    (unsigned char *) "\x2C",
    (unsigned char *) "\x2D",
    (unsigned char *) "\x2E",
    (unsigned char *) "\x2F",
    NULL /* sentinel */
};

static size_t RESERVED_LENS[] = {
    BROADCAST_LEN,
    RENEGOTIATE_LEN,
    WHISPER_LEN,
    PING_LEN,
    PONG_LEN,
    HANDSHAKE_LEN,
    NOTIFY_LEN,
    PEERS_LEN,
    REQUEST_LEN,
    RESEND_LEN,
    RESPONSE_LEN,
    STORE_LEN,
    RETRIEVE_LEN,
    1,
    1,
    1,
    BZ2_LEN,
    GZIP_LEN,
    LZMA_LEN,
    ZLIB_LEN,
    BWTC_LEN,
    CONTEXT1_LEN,
    DEFSUM_LEN,
    DMC_LEN,
    FENWICK_LEN,
    HUFFMAN_LEN,
    LZJB_LEN,
    LZJBR_LEN,
    LZP3_LEN,
    MTF_LEN,
    PPMD_LEN,
    SIMPLE_LEN,
    SNAPPY_LEN,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    0 /* sentinel */
};

static size_t NUM_COMPRESSIONS = 0;

static unsigned char *COMPRESSION_FLAGS[] = {
    NULL /* sentinel */
};

static size_t COMPRESSION_LENS[] = {
    0 /* sentinel */
};

static unsigned long long getUTC() {
    /**
    * .. c:function:: unsigned long getUTC()
    *
    *     Returns the current UNIX second in UTC
    */
    time_t t;
    time(&t);
    return mktime(gmtime(&t));
}

static void get_user_salt(char result[36])  {
    /**
    * .. c:function:: static void get_user_salt(char result[36])
    *
    *     This generates a uuid4 for use in this library. ``result`` should be of length 36
    */
    size_t i = 0;
    char *temp_hex_set = (char*)"0123456789abcdef";
    srand(time(NULL));
    CP2P_DEBUG("Building user_salt\n");
    strncpy(result, "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx", 36);
    for (; i < 36; i++) {
        if (result[i] == 'x')
            result[i] = temp_hex_set[(rand() % 16)];
        else if (result[i] == 'y')
            result[i] = temp_hex_set[((rand() % 16) & 0x3) | 0x8];
    }
}

static unsigned long long unpack_value(const char *str, size_t len)   {
    /**
    * .. c:function:: static unsigned long long unpack_value(const char *str, size_t len)
    *
    *     Unpacks a big-endian binary value into an unsigned long long
    *
    *     :param str: The value you'd like to unpack
    *
    *     :param len: The length of this value
    *
    *     :returns: The value this string contained
    *
    *     .. warning::
    *
    *         Integer overflow will not be accounted for
    */
    unsigned long long val = 0;
    size_t i = 0;
    for (; i < len; i++)    {
        val = val << 8;
        val += (unsigned char)str[i];
    }
    return val;
}

static void pack_value(size_t len, char *arr, unsigned long long i)  {
    /**
    * .. c:function:: static void pack_value(size_t len, char *arr, unsigned long long i)
    *
    *     Packs an unsigned long long into a big-endian binary buffer of length len
    *
    *     :param len:   The length of the string you'd like to produce
    *     :param arr:   The buffer you would like to fill
    *     :param i:     The value you'd like to pack
    *
    *     .. warning::
    *
    *         Integer overflow will not be accounted for
    */
    size_t j = 0;
    memset(arr, 0, len);
    for (; j < len && i != 0; j++)    {
        arr[len - j - 1] = i & 0xff;
        i = i >> 8;
    }
}

static int sanitize_string(char *str, size_t *len, int sizeless)    {
    /**
    * .. c:function:: static int sanitize_string(char *str, size_t *len, int sizeless)
    *
    *     Mutates str to be clean for processing by process_string.
    *
    *     :param str:       The string you wish to mutate
    *     :param len:       The length of said string
    *     :param sizeless:  A boolean which indicates whether the string has a standard size header
    *
    *     :returns: ``-1`` if str was invalid for processing, ``0`` if all went well
    */
    if (!sizeless)  {
        if (unpack_value(str, 4) != *len - 4)
            return -1;
        memmove(str, str + 4, *len - 4);
        *len -= 4;
    }
    return 0;
}

static int decompress_string(char *str, size_t len, char **result, size_t *res_len, char **compressions, size_t *compression_sizes, size_t num_compressions) {
    /**
    * .. c:function:: static int decompress_string(char *str, size_t len, char *result, size_t *res_len, char **compressions, size_t *compression_sizes, size_t num_compressions)
    *
    *     Puts a decompressed copy of str into result, and updates res_len to contain its length.
    *
    *     :param str:               The string you wish to decompress
    *     :param len:               The length of this string
    *     :param result:            A pointer to the resulting string
    *     :param res_len:           A pointer to the length of the result
    *     :param compressions:      The list of possible compression methods
    *     :param compression_sizes: The length of each compression method
    *     :param num_compressions:  The number of compression methods
    *
    *     :returns: ``-1`` if decompression failed, ``0`` if all went well
    *
    *     .. warning::
    *
    *         If you do not :c:func:`free` ``result`` you will develop a memory leak
    */
    // TODO: Implement zlib/gzip compression
    *result = (char *) malloc(sizeof(char) * len);
    memcpy(result, str, len);
    *res_len = len;
    return 0;
}

static int process_string(const char *str, size_t len, char ***packets, size_t **lens, size_t *num_packets)  {
    /**
    * .. c:function:: static int process_string(const char *str, size_t len, char **packets, size_t **lens, size_t *num_packets)
    *
    *     Transforms a serialized string into an array of packets. This is formatted as an array of strings, an array of lengths,
    *     and a number of packets. You must provide a pointer to these. Packets must be initialized as an array of :c:type:`char *`.
    *
    *     :param str:       The string to deserialize
    *     :param len:       The length of this string
    *     :param packets:   A pointer to the returned array of packets. This will be initialized for you
    *     :param lens:      A pointer to the returned array of packet lengths. This will be initiaized for you
    *     :num_packets:     A pointer to the number of packets. This will be initialized for you
    *
    *     :returns: ``0`` if successful, any other number if not. If it returns non-``0``, ``packets`` and ``lens`` will point to ``NULL``
    *
    *     .. warning::
    *
    *         If you do not :c:func:`free` ``packets`` and ``lens`` you will develop a memory leak
    */
    size_t processed = 0;
    size_t factor = 16;
    size_t i;
    *num_packets = 0;
    *lens = (size_t *) malloc(sizeof(size_t) * factor);
    CP2P_DEBUG("Entering while loop\n");
    while (processed < len)   {
        size_t tmp = unpack_value(str + processed, 4);
        CP2P_DEBUG("Processing for packet %i\n", *num_packets);
        if (!(*num_packets % factor))    {
            factor *= 2;
            *lens = (size_t *) realloc(*lens, sizeof(size_t) * factor);
        }
        (*lens)[*num_packets] = tmp;
        processed += tmp + 4;
        *num_packets += 1;
    }
    if (processed > len)    {
        free(*lens);
        *lens = NULL;
        *packets = NULL;
        return -1;
    }
    CP2P_DEBUG("Exited while loop\n");
    *lens = (size_t *) realloc(*lens, sizeof(size_t) * (*num_packets));
    *packets = (char **) realloc(*packets, sizeof(char *) * (*num_packets));
    processed = 4;
    CP2P_DEBUG("Entering for loop\n");
    for (i = 0; i < *num_packets; i++)    {
        (*packets)[i] = (char *) malloc(sizeof(char) * (*lens)[i]);
        memcpy((*packets)[i], str + processed, (*lens)[i]);
        processed += (*lens)[i] + 4;
    }
    return 0;
}

#ifdef _cplusplus
}
#endif

#endif

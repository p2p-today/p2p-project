/**
* Base Module
* ===========
*/

#ifndef C2P_BASE
#define C2P_BASE

#ifdef _cplusplus
extern "C" {
#endif

#define BROADCAST_FLAG (unsigned char *) "\x00"
#define BROADCAST_LEN (size_t) 1
#define WATERFALL_FLAG (unsigned char *) "\x01"
#define WATERFALL_LEN (size_t) 1
#define WHISPER_FLAG (unsigned char *) "\x02"
#define WHISPER_LEN (size_t) 1
#define RENEGOTIATE_FLAG (unsigned char *) "\x03"
#define RENEGOTIATE_LEN (size_t) 1
#define PING_FLAG (unsigned char *) "\x04"
#define PING_LEN (size_t) 1
#define PONG_FLAG (unsigned char *) "\x05"
#define PONG_LEN (size_t) 1
#define COMPRESSION_FLAG (unsigned char *) "\x01"
#define COMPRESSION_LEN (size_t) 1
#define HANDSHAKE_FLAG (unsigned char *) "\x03"
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

static size_t NUM_RESERVED = 0x20;

static unsigned char *RESERVED_FLAGS[] = {
    BROADCAST_FLAG,
    WATERFALL_FLAG,
    WHISPER_FLAG,
    RENEGOTIATE_FLAG,
    PING_FLAG,
    PONG_FLAG,
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
    SIMPLE_FLAG
};

static size_t RESERVED_LENS[] = {
    BROADCAST_LEN,
    WATERFALL_LEN,
    WHISPER_LEN,
    RENEGOTIATE_LEN,
    PING_LEN,
    PONG_LEN,
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
    SIMPLE_LEN
};

static size_t NUM_COMPRESSIONS = 0;

static unsigned char *COMPRESSION_FLAGS[] = {
};

static size_t COMPRESSION_LENS[] = {
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
    srand(time(NULL));
    CP2P_DEBUG("Building user_salt\n");
    strncpy(result, "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx", 36);
    char *temp_hex_set = (char*)"0123456789abcdef";
    for (size_t i = 0; i < 36; i++) {
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
    for (size_t i = 0; i < len; i++)    {
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
    memset(arr, 0, len);
    for (size_t j = 0; j < len && i != 0; j++)    {
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
    *     .. warning::
    *
    *         If you do not :c:func:`free` ``packets`` and ``lens`` you will develop a memory leak
    */
    size_t processed = 0;
    size_t expected = len;
    *lens = (size_t *) malloc(sizeof(size_t) * 4);
    *num_packets = 0;
    CP2P_DEBUG("Entering while loop\n")
    while (processed != expected)   {
        CP2P_DEBUG("Processing for packet %i\n", *num_packets);
        size_t tmp = unpack_value(str + processed, 4);
        if (*num_packets >= 4)
            *lens = (size_t *) realloc(*lens, sizeof(size_t) * (*num_packets + 1));
        (*lens)[*num_packets] = tmp;
        processed += 4;
        expected -= tmp;
        *num_packets += 1;
    }
    CP2P_DEBUG("Exited while loop\n")
    *packets = (char **) realloc(*packets, sizeof(char *) * (*num_packets));
    CP2P_DEBUG("Entering for loop\n");
    for (size_t i = 0; i < *num_packets; i++)    {
        (*packets)[i] = (char *) malloc(sizeof(char) * (*lens)[i]);
        memcpy((*packets)[i], str + processed, (*lens)[i]);
        processed += (*lens)[i];
    }
    return 0;
}

#ifdef _cplusplus
}
#endif

#endif

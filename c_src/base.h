#ifndef C2P_BASE
#define C2P_BASE

#ifdef _cplusplus
extern "C" {
#endif

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
    *     .. note::
    *
    *         You must :c:func:`free` ``result`` or you will develop a memory leak
    */
    // TODO: Implement zlib/gzip compression
    *result = (char *) malloc(sizeof(char) * len);
    memcpy(result, str, len);
    *res_len = len;
    return 0;
}

static int process_string(char *str, size_t len, char ***packets, size_t **lens, size_t *num_packets)  {
    /**
    * .. c:function:: static int process_string(char *str, size_t len, char **packets, size_t **lens, size_t *num_packets)
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
    while (processed != expected)   {
        size_t tmp = unpack_value(str + processed, 4);
        if (*num_packets >= 4)
            *lens = (size_t *) realloc(*lens, sizeof(size_t) * (*num_packets));
        *lens[*num_packets] = tmp;
        processed += 4;
        expected -= tmp;
        *num_packets += 1;
    }
    *packets = (char **) malloc(sizeof(char *) * (*num_packets));
    for (size_t i = 0; i < *num_packets; i++)    {
        *packets[i] = (char *) malloc(sizeof(char) * (*lens[i]));
        memcpy(*packets[i], str + processed, *lens[i]);
        processed += *lens[i];
    }
    return 0;
}

#ifdef _cplusplus
}
#endif

#endif
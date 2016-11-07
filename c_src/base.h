#ifdef _cplusplus
extern "C" {
#endif

static unsigned long getUTC() {
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

#ifdef _cplusplus
}
#endif
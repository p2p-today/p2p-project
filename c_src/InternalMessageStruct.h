/**
* Internal Message Header
* =======================
*
* This header contains the C functions needed for using the message format in the p2p.today project.
*
* It automatically includes :doc:`base.h <./base>` and :doc:`BaseConverter.h <./BaseConverter>`
*
* Using this requires a compiled copy of the sha2 hashes, provided in ``c_src/sha/sha2.c``
*/

#include <msgpack.h>
#include "./base.h"
#include "./sha/sha2.h"
#include "./BaseConverter.h"

#ifdef _cplusplus
extern "C" {
#endif

typedef struct  {
    /**
    * .. c:type:: typedef struct InternalMessageStruct
    *
    *     .. c:member:: unsigned char msg_type
    *
    *         The type of message this is. These are described in :doc:`protocol/flags <../../protocol/flags>`.
    *
    *     .. c:member:: char *sender
    *
    *         The message sender's ID
    *
    *     .. c:member:: size_t sender_len
    *
    *     .. c:member:: unsigned long long timestamp
    *
    *         The time at which this message was sent, in UTC seconds since 1/1/1970.
    *
    *     .. note::
    *
    *         Members after these are not garunteed to be present. A function to ensure their existence will be
    *         provided as noted. Otherwise check if their length term is ``0`` to determine existence.
    *
    *     .. c:member:: char **compression
    *
    *         An array of possible compression algorigthms
    *
    *         This can be initialized with :c:func:`setInternalMessageCompressions`
    *
    *     .. c:member:: size_t *compression_lens
    *
    *         The length of each compression string, in the same order
    *
    *     .. c:member:: size_t num_compression
    *
    *         The number of compression methods
    *
    *     .. c:member:: char *id
    *
    *         The checksum/ID of this message
    *
    *         To ensure this value is set, call :c:func:`ensureInternalMessageID`
    *
    *     .. c:member:: size_t id_len
    *
    *     .. c:member:: char *str
    *
    *         The serialized version of this message
    *
    *     .. c:member:: size_t str_len
    */
    unsigned char msg_type;
    char *sender;
    size_t sender_len;
    unsigned long long timestamp;
    msgpack_sbuffer* buffer;
    msgpack_packer* packer;
    msgpack_unpacker unpacker;
    char **compression;
    size_t *compression_lens;
    size_t num_compressions;
    char *compression_used;
    size_t compression_used_len;
    char *id;
    size_t id_len;
    char *str;
    size_t str_len;
} InternalMessageStruct;


static InternalMessageStruct *startInternalMessage(const size_t num_packets, const unsigned char type, const char *sender, size_t sender_len, const char sender_is_unicode, const unsigned long long timestamp)   {
    /**
    * .. c:function:: static InternalMessageStruct *startInternalMessage(const size_t num_packets, const char *type, size_t type_len, const char *sender, const size_t sender_len, const unsigned long long timestamp)
    *
    *     Constructs an InternalMessageStruct. This copies all given data into a struct, then returns this struct's pointer.
    *
    *     :param num_packets        The number of items you will pack (must be exact)
    *     :param type:              The item to place in :c:member:`InternalMessageStruct.msg_type`
    *     :param sender:            The item to place in :c:member:`InternalMessageStruct.sender`
    *     :param sender_len:        The length of the above
    *     :param sender_is_unicode: If true, pack sender as a string, not a buffer
    *     :param timestamp:         If non-zero, pack timestamp as this value
    *
    *     :returns: A pointer to the resulting :c:type:`InternalMessageStruct`
    *
    *     .. warning::
    *
    *          You must use :c:func:`destroyInternalMessage` on the resulting object, or you will develop a memory leak
    */
    InternalMessageStruct *ret;
    CP2P_DEBUG("Inside real constructor. num_packets=%i\n", num_packets);
    ret = (InternalMessageStruct *) malloc(sizeof(InternalMessageStruct));
    ret->msg_type = type;
    ret->sender = (char *) malloc(sizeof(char) * sender_len);
    memcpy(ret->sender, sender, sender_len);
    ret->sender_len = sender_len;
    ret->timestamp = timestamp || getUTC();
    ret->buffer = msgpack_sbuffer_new();
    ret->packer = msgpack_packer_new(ret->buffer, msgpack_sbuffer_write);
    msgpack_pack_array(ret->packer, num_packets + 3);
    msgpack_pack_int(ret->packer, ret->msg_type);
    if (sender_is_unicode)  {
        msgpack_pack_str(ret->packer, ret->sender_len);
        msgpack_pack_str_body(ret->packer, ret->sender, ret->sender_len);
    }
    else    {
        msgpack_pack_bin(ret->packer, ret->sender_len);
        msgpack_pack_bin_body(ret->packer, ret->sender, ret->sender_len);
    }
    msgpack_pack_int(ret->packer, ret->timestamp);
    msgpack_unpacker_init(&(ret->unpacker), MSGPACK_UNPACKER_INIT_BUFFER_SIZE);
    ret->compression = NULL;
    ret->compression_lens = NULL;
    ret->num_compressions = 0;
    ret->compression_used = NULL;
    ret->compression_used_len = 0;
    ret->id = NULL;
    ret->id_len = 0;
    ret->str = NULL;
    ret->str_len = 0;
    CP2P_DEBUG("Returning\n");
    return ret;
}

static void destroyInternalMessage(InternalMessageStruct *des)    {
    /**
    * .. c:function:: static void destroyInternalMessage(InternalMessageStruct *des)
    *
    *     :c:func:`free` an :c:type:`InteralMessageStruct` and its members
    *
    *     :param des: A pointer to the InternalMessageStruct you wish to destroy
    */
    size_t i;
    CP2P_DEBUG("1\n");
    msgpack_sbuffer_free(des->buffer);
    CP2P_DEBUG("2\n");
    msgpack_packer_free(des->packer);
    CP2P_DEBUG("3\n");
    if (des->compression != NULL)   {
        CP2P_DEBUG("4\n");
        for (i = 0; i < des->num_compressions; i++)  {
            free(des->compression[i]);
        }
        CP2P_DEBUG("5\n");
        free(des->compression);
        CP2P_DEBUG("6\n");
        free(des->compression_lens);
    }
    CP2P_DEBUG("7\n");
    if (des->id != NULL)    {
        free(des->id);
    }
    CP2P_DEBUG("8\n");
    if (des->str != NULL)   {
        free(des->str);
    }
    CP2P_DEBUG("9\n");
    free(des);
}

static void setInternalMessageCompressions(InternalMessageStruct *des, char **compression, size_t *compression_lens, size_t num_compressions)   {
    /**
    * .. c:function:: static void setInternalMessageCompressions(InternalMessageStruct *des, char **compression, size_t *compression_lens, size_t num_compressions)
    *
    *     Sets the compression methods for a particular :c:type:`InternalMessageStruct`. These methods are formatted as an array of strings, an array of lengths, and a
    *     number of methods. The data is copied, so you inputs can be local variables.
    *
    *     :param des:               A pointer to the relevant InternalMessageStruct
    *     :param compression:       An array of compression methods
    *     :param compression_lens:  An array of lengths for each compression method
    *     :param num_compressions:  The number of compression methods
    */
    size_t i;
    if (des->str != NULL)   {
        free(des->str);
    }
    if (des->compression != NULL)   {
        for (i = 0; i < des->num_compressions; i++)  {
            free(des->compression[i]);
        }
        free(des->compression);
        free(des->compression_lens);
    }
    des->compression = (char **) malloc(sizeof(char *) * num_compressions);
    des->compression_lens = (size_t *) malloc(sizeof(size_t) * num_compressions);
    for (i = 0; i < des->num_compressions; i++)  {
        des->compression[i] = (char *) malloc(sizeof(char) * compression_lens[i]);
        memcpy(des->compression[i], compression[i], compression_lens[i]);
    }
}

static void ensureInternalMessageID(InternalMessageStruct *des)  {
    /**
    * .. c:function:: static void ensureInternalMessageID(InternalMessageStruct *des)
    *
    *     Ensures that the InternalMessageStruct has an ID calculated and assigned
    *
    *     :param des: A pointer to the relevant InternalMessageStruct
    */
    SHA256_CTX ctx;

    if (des->id != NULL)   {
        CP2P_DEBUG("ID already exists\n")
        return;
    }

    des->id = calloc(SHA256_DIGEST_LENGTH, sizeof(char));
    SHA256_Init(&ctx);
    SHA256_Update(&ctx, (const unsigned char *) des->buffer->data, des->buffer->size);
    SHA256_Final((unsigned char *) des->id, &ctx);
    des->id_len = SHA256_DIGEST_LENGTH;
}

static void ensureInternalMessageStr(InternalMessageStruct *des) {
    /**
    * .. c:function:: static void ensureInternalMessageStr(InternalMessageStruct *des)
    *
    *     Ensures that the InternalMessageStruct has a serialized string calculated and assigned
    *
    *     :param des: A pointer to the relevant InternalMessageStruct
    */
    if (des->str != NULL)   {
        CP2P_DEBUG("str already exists\n");
        return;
    }
    CP2P_DEBUG("Building str\n");

    ensureInternalMessageID(des);
    des->str_len = 4 + des->id_len + des->buffer->size;
    des->str = (char *) malloc(des->str_len * sizeof(char));
    pack_value(4, des->str, des->str_len - 4);
    memcpy(des->str + 4, des->id, des->id_len);
    memcpy(des->str + 4 + des->id_len, des->buffer->data, des->buffer->size);
}

static InternalMessageStruct *deserializeInternalMessage(const char *serialized, size_t len, int sizeless, int *errored)  {
    /**
    * .. c:function:: static InternalMessageStruct *deserializeInternalMessage(const char *serialized, size_t len, int sizeless)
    *
    *     Deserializes an uncompressed :c:type:`InternalMessageStruct`. The ``sizeless`` parameter indicates whether the network size
    *     header is still present on the given string.
    *
    *     :param serialized:    The serialized message
    *     :param len:           The length of the serialized message
    *     :param sizeless:      A boolean which indicates whether the network size header is still present on the given string
    *     :param errored:       A pointer to a boolean. If this is set with a non-zero value, it indicates that the checksum test failed
    *
    *     :returns: An equivalent :c:type:`InternalMessageStruct`, or ``NULL`` if there was an error
    */
    char *tmp = (char *) malloc(sizeof(char) * len);
    unsigned char digest[SHA256_DIGEST_LENGTH];
    SHA256_CTX ctx;
    InternalMessageStruct *ret;
    msgpack_unpacker streamer;
    msgpack_unpacked result;
    msgpack_object_array array;
    unsigned char *sender;
    size_t sender_len, i;
    unsigned long long msg_type, timestamp;
    CP2P_DEBUG("Entering deserializeInternalMessage\n")
    memcpy(tmp, serialized, len);
    sanitize_string(tmp, &len, sizeless);
    CP2P_DEBUG("string sanitized\n")
    memset(digest, 0, SHA256_DIGEST_LENGTH);
    SHA256_Init(&ctx);
    SHA256_Update(&ctx, (const unsigned char *) tmp + SHA256_DIGEST_LENGTH, len - SHA256_DIGEST_LENGTH);
    SHA256_Final(digest, &ctx);
    if (memcmp(digest, tmp, SHA256_DIGEST_LENGTH))   {
        CP2P_DEBUG("Checksum not matched\n")
        *errored = -1;
        free(tmp);
        return NULL;
    }
    CP2P_DEBUG("Checksum matched\n")

    // start streaming for metadata
    msgpack_unpacker_init(&streamer, MSGPACK_UNPACKER_INIT_BUFFER_SIZE);
    msgpack_unpacker_reserve_buffer(&streamer, len - SHA256_DIGEST_LENGTH);
    memcpy(msgpack_unpacker_buffer(&streamer), tmp + SHA256_DIGEST_LENGTH, len - SHA256_DIGEST_LENGTH);
    msgpack_unpacker_buffer_consumed(&streamer, len - SHA256_DIGEST_LENGTH);
    msgpack_unpacked_init(&result);
    msgpack_unpacker_next(&streamer, &result);
    array = result.data.via.array;
    free(tmp);
    if (array.size < 3) {
        *errored = -1;
        return NULL;
    }
    msg_type = array.ptr[0].via.u64;
    sender = array.ptr[1].via.str.ptr;
    sender_len = array.ptr[1].via.str.size;
    timestamp = array.ptr[2].via.u64;
    ret = startInternalMessage(array.size - 3, msg_type, (const char *) sender, sender_len, (array.ptr[1].type == MSGPACK_OBJECT_STR), timestamp);
    // start packing rest of stuff
    for (i = 3; i < array.size; ++i)    {
        msgpack_pack_object(ret->packer, array.ptr[i]);
    }
    return ret;
}

static InternalMessageStruct *deserializeCompressedInternalMessage(const char *serialized, size_t len, int sizeless, int *errored, char **compression, size_t *compression_lens, size_t num_compressions)    {
    /**
    * .. c:function:: static InternalMessageStruct *deserializeCompressedInternalMessage(const char *serialized, size_t len, int sizeless, char **compression, size_t *compression_lens, size_t num_compressions)
    *
    *     Deserializes a compressed :c:type:`InternalMessageStruct`. The ``sizeless`` parameter indicates whether the network size
    *     header is still present on the given string.
    *
    *     :param serialized:        See :c:func:`deserializeInternalMessage`
    *     :param len:               See :c:func:`deserializeInternalMessage`
    *     :param sizeless:          See :c:func:`deserializeInternalMessage`
    *     :param errored:           See :c:func:`deserializeInternalMessage`
    *     :param compression:       See :c:func:`setInternalMessageCompressions`
    *     :param compression_lens:  See :c:func:`setInternalMessageCompressions`
    *     :param num_compressions:  See :c:func:`setInternalMessageCompressions`
    *
    *     :returns: An equivalent :c:type:`InternalMessageStruct`, or ``NULL`` if there was an error
    */
    char *tmp = (char *) malloc(sizeof(char) * len);
    char *result;
    size_t res_len;
    InternalMessageStruct *ret;
    memcpy(tmp, serialized, len);
    sanitize_string(tmp, &len, sizeless);
    decompress_string(tmp, len, &result, &res_len, compression, compression_lens, num_compressions);
    ret = deserializeInternalMessage(result, res_len, 0, errored);
    if (!errored)   {
        setInternalMessageCompressions(ret, compression, compression_lens, num_compressions);
    }
    return ret;
}

#ifdef _cplusplus
}
#endif

#include "./base.h"

#ifdef _cplusplus
extern "C" {
#endif

struct InternalMessageStruct    {
    char *msg_type;
    size_t msg_type_len;
    char *sender;
    size_t sender_len;
    unsigned long long timestamp;
    char **payload;
    size_t *payload_lens;
    size_t num_payload;
    char **compression;
    size_t *compression_lens;
    size_t num_compressions;
    char *compression_used;
    size_t compression_used_len;
    char *id;
    size_t id_len;
    char *str;
    size_t str_len;
};


static struct InternalMessageStruct *constructInternalMessage(const char *type, size_t type_len, const char *sender, size_t sender_len, char **payload, size_t *payload_lens, size_t num_payload)   {
    CP2P_DEBUG("Inside real constructor. num_payload=%i\n", num_payload);
    struct InternalMessageStruct *ret = (struct InternalMessageStruct *) malloc(sizeof(InternalMessageStruct));
    ret->msg_type = (char *) malloc(sizeof(char) * type_len);
    memcpy(ret->msg_type, type, type_len);
    ret->msg_type_len = type_len;
    ret->sender = (char *) malloc(sizeof(char) * sender_len);
    memcpy(ret->sender, sender, sender_len);
    ret->sender_len = sender_len;
    ret->timestamp = getUTC();
    ret->payload = (char **) malloc(sizeof(char *) * num_payload);
    ret->payload_lens = (size_t *) malloc(sizeof(size_t) * num_payload);
    CP2P_DEBUG("At for loop\n");
    for (size_t i = 0; i < num_payload; i++)    {
        ret->payload[i] = (char *) malloc(sizeof(char) * payload_lens[i]);
        ret->payload_lens[i] = payload_lens[i];
        memcpy(ret->payload[i], payload[i], payload_lens[i]);
    }
    CP2P_DEBUG("Exited for loop\n");
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

static void destroyInternalMessage(struct InternalMessageStruct *des)    {
    free(des->msg_type);
    for (size_t i = 0; i < des->num_payload; i++)   {
        free(des->payload[i]);
    }
    free(des->payload);
    free(des->payload_lens);
    if (des->compression != NULL)   {
        for (size_t i = 0; i < des->num_compressions; i++)  {
            free(des->compression[i]);
        }
        free(des->compression);
        free(des->compression_lens);
    }
    if (des->id != NULL)    {
        free(des->id);
    }
    if (des->str != NULL)   {
        free(des->str);
    }
    free(des);
}


static void setInternalMessageCompressions(struct InternalMessageStruct *des, char **compression, size_t *compression_lens, size_t num_compressions)   {
    if (des->compression != NULL)   {
        for (size_t i = 0; i < des->num_compressions; i++)  {
            free(des->compression[i]);
        }
        free(des->compression);
        free(des->compression_lens);
    }
    des->compression = (char **) malloc(sizeof(char *) * num_compressions);
    des->compression_lens = (size_t *) malloc(sizeof(size_t) * num_compressions);
    for (size_t i = 0; i < des->num_compressions; i++)  {
        des->compression[i] = (char *) malloc(sizeof(char) * compression_lens[i]);
        memcpy(des->compression[i], compression[i], compression_lens[i]);
    }
}

static struct InternalMessageStruct *deserializeInternalMessage(const char *serialized, size_t len, int sizeless)  {
    char *tmp = (char *) malloc(sizeof(char) * len);
    memcpy(tmp, serialized, len);
    sanitize_string(tmp, &len, sizeless);
    char **packets = (char **) malloc(sizeof(char *) * 4);
    size_t *lens;
    size_t num_packets;
    CP2P_DEBUG("Entering process_string\n");
    process_string(tmp, len, &packets, &lens, &num_packets);
    CP2P_DEBUG("Exiting process_string\n");
    struct InternalMessageStruct *ret = constructInternalMessage(
        packets[0], lens[0],
        packets[1], lens[1],
        packets + 4, lens + 4, num_packets - 4);
    ret->timestamp = from_base_58(packets[3], lens[3]);
    return ret;
}

static struct InternalMessageStruct *deserializeCompressedInternalMessage(const char *serialized, size_t len, int sizeless, char **compression, size_t *compression_lens, size_t num_compressions)    {
    char *tmp = (char *) malloc(sizeof(char) * len);
    memcpy(tmp, serialized, len);
    sanitize_string(tmp, &len, sizeless);
    char *result;
    size_t res_len;
    decompress_string(tmp, len, &result, &res_len, compression, compression_lens, num_compressions);
    struct InternalMessageStruct *ret = deserializeInternalMessage(result, res_len, 0);
    setInternalMessageCompressions(ret, compression, compression_lens, num_compressions);
    return ret;
}

#ifdef _cplusplus
}
#endif

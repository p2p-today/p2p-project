#include <string.h>
#include "./sha/sha2.h"
#include "./BaseConverter.h"

#ifdef _cplusplus
extern "C" {
#endif

typedef struct  {
    char *subnet, *encryption, *_id;
    size_t subnetSize, encryptionSize, idSize;
} SubnetStruct;

static SubnetStruct *getSubnet(char *subnet, size_t subnetSize, char *encryption, size_t encryptionSize) {
    SubnetStruct *ret = (SubnetStruct *) malloc(sizeof(SubnetStruct));
    ret->subnetSize = subnetSize;
    ret->encryptionSize = encryptionSize;
    ret->subnet = (char *) malloc(sizeof(char) * subnetSize);
    memcpy(ret->subnet, subnet, subnetSize);
    ret->encryption = (char *) malloc(sizeof(char) * encryptionSize);
    memcpy(ret->encryption, encryption, encryptionSize);
    ret->_id = NULL;
    ret->idSize = 0;
    return ret;
}

static void destroySubnet(SubnetStruct *sub)    {
    free(sub->subnet);
    free(sub->encryption);
    if (sub->_id != NULL)
        free(sub->_id);
    free(sub);
}

static char *subnetID(SubnetStruct *sub) {
    if (sub->_id == NULL)   {
        char buffer[6];
        unsigned char digest[SHA256_DIGEST_LENGTH];
        SHA256_CTX ctx;
        size_t buffSize = sprintf(buffer, "%llu.%llu", (unsigned long long)C2P_PROTOCOL_MAJOR_VERSION, (unsigned long long)C2P_PROTOCOL_MINOR_VERSION);
        size_t infoSize = buffSize + sub->subnetSize + sub->encryptionSize;
        char *info = (char *) malloc(sizeof(char) * infoSize);

        memcpy(info, sub->subnet, sub->subnetSize);
        memcpy(info + sub->subnetSize, sub->encryption, sub->encryptionSize);
        memcpy(info + sub->subnetSize + sub->encryptionSize, buffer, buffSize);

        memset(digest, 0, SHA256_DIGEST_LENGTH);
        SHA256_Init(&ctx);
        SHA256_Update(&ctx, (unsigned char*)info, infoSize);
        SHA256_Final(digest, &ctx);

        sub->_id = ascii_to_base_58((char *)digest, SHA256_DIGEST_LENGTH, &(sub->idSize), 1);
    }
    return sub->_id;
}

#ifdef _cplusplus
}
#endif

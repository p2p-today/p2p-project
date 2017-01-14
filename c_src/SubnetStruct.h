/**
* Subnet Header
* =============
*
* This header contains the C functions needed for Protocol object in the p2p.today project.
*
* It automatically includes :doc:`BaseConverter.h <./BaseConverter>`
*
* Using this requires a compiled copy of the sha2 hashes, provided in ``c_src/sha/sha2.c``
*/

#include <string.h>
#include "./sha/sha2.h"
#include "./BaseConverter.h"

#ifdef _cplusplus
extern "C" {
#endif

typedef struct  {
    /**
    * .. c:type:: typedef struct SubnetStruct
    *
    *     .. c:member:: char *subnet
    *
    *         The name of the desired subnet
    *
    *     .. c:member:: size_t subnetSize
    *
    *         The length of the desired subnet
    *
    *     .. c:member:: char *encryption
    *
    *         The desired transport method
    *
    *     .. c:member:: size_t encryptionSize
    *
    *         The length of the transport method
    *
    *     .. c:member:: char *_id
    *
    *         Private field which contains the hash ID of this network
    *
    *         Use :c:func:`subnetID` to safely obtain this value. It is
    *         is allocated and calculated on demand only.
    *
    *     .. c:member:: size_t *_id
    *
    *         The length of this network's hash ID
    */
    char *subnet, *encryption, *_id;
    size_t subnetSize, encryptionSize, idSize;
} SubnetStruct;

static SubnetStruct *getSubnet(const char *subnet, size_t subnetSize, const char *encryption, size_t encryptionSize) {
    /**
    * .. c:function:: static SubnetStruct *getSubnet(const char *subnet, size_t subnetSize, const char *encryption, size_t encryptionSize)
    *
    *     Constructs an SubnetStruct. This copies all given data into a struct, then returns this struct's pointer.
    *
    *     :param subnet:            The item to place in :c:member:`SubnetStruct.subnet`
    *     :param subnetSize:        The length of the above
    *     :param encryption:        The item to place in :c:member:`SubnetStruct.encryption`
    *     :param encryptionSize:    The length of the above
    *
    *     :returns: A pointer to the resulting :c:type:`SubnetStruct`
    *
    *     .. warning::
    *
    *          You must use :c:func:`destroySubnet` on the resulting object, or you will develop a memory leak
    */
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
    /**
    * .. c:function:: static void destroySubnet(SubnetStruct *des)
    *
    *     :c:func:`free` an :c:type:`SubnetStruct` and its members
    *
    *     :param des: A pointer to the SubnetStruct you wish to destroy
    */
    free(sub->subnet);
    free(sub->encryption);
    if (sub->_id != NULL)
        free(sub->_id);
    free(sub);
}

static char *subnetID(SubnetStruct *sub) {
    /**
    * .. c:function:: static char *subnetID(SubnetStruct *sub)
    *
    *     Ensures that a :c:type:`SubnetStruct` has an ID, and returns this ID.
    *
    *     :returns: The given :c:type:`SubnetStruct`'s ID
    */
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

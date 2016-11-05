#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "./spf/SuperFastHash.h"

#define DICTSIZE 8191
#define hash(key, keySize) (SuperFastHash(key, keySize) % DICTSIZE)

struct LLNode {
    struct LLNode *next;
    char *key, *val;
    size_t keySize, valSize;
};

struct LLNode **getDict()    {
    return (struct LLNode **) malloc(sizeof(struct LLNode *) * DICTSIZE);
}

struct LLNode *_dictLookup(struct LLNode **dict, char *key, size_t keySize)   {
    struct LLNode *node = dict[hash(key, keySize)];
    for (; node != NULL; node = node->next)
        if (keySize == node->keySize && memcmp(key, node->key, keySize) == 0)
            return node; /* found */
    return NULL; /* not found */
}

void dictDestroyEntry(struct LLNode *entry) {
    free((void *)entry->key);
    free((void *)entry->val);
    free((void *)entry);
}

void dictRemove(struct LLNode **dict, char *key, size_t keySize)    {
    struct LLNode *prev = NULL;
    struct LLNode *node = dict[hash(key, keySize)];
    while (node != NULL)    {
        prev = node;
        node = node->next;
        if (keySize == node->keySize && memcmp(key, node->key, keySize) == 0)
            break; /* found */
    }
    if (node != NULL)   {
        prev->next = node->next;
        dictDestroyEntry(node);
    }
}

char *dictLookup(struct LLNode **dict, char *key, size_t keySize, size_t *valSize)   {
    struct LLNode *node = _dictLookup(dict, key, keySize);
    if (node != NULL)
        if (valSize != NULL)
            *valSize = node->valSize;
        return node->val;
    return NULL;
}

void dictStore(struct LLNode **dict, char *key, size_t keySize, char *value, size_t valSize) {
    struct LLNode *node = _dictLookup(dict, key, keySize);
    if (node == NULL)   {
        node = (struct LLNode *) malloc(sizeof(*node));
        size_t hashval = hash(key, keySize);
        node->next = dict[hashval];
        dict[hashval] = node;
        node->keySize = keySize;
        node->key = (char *) malloc(sizeof(char) * keySize);
        memcpy(node->key, key, sizeof(char) * keySize);
    }
    else    {
        free((void *)node->val);
    }
    node->valSize = valSize;
    node->val = (char *) malloc(sizeof(char) * valSize);
    memcpy(node->val, value, sizeof(char) * valSize);
}

void dictDestroy(struct LLNode **dict)  {
    for (size_t i = 0; i < DICTSIZE; i++)   {
        while (dict[i] != NULL) {
            struct LLNode *node = dict[i];
            dict[i] = node->next;
            dictDestroyEntry(node);
        }
    }
    free((void *)dict);
}

int main(void) {
    // your code goes here
    struct LLNode **dict = NULL;
    dict = getDict();
    dictStore(dict, "abc", 3, "def", 3);
    printf("\"abc\" = \"%s\"\n", dictLookup(dict, "abc", 3, NULL));
    dictDestroy(dict);
    return 0;
}

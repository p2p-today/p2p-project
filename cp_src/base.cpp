#include "base.h"
#include <ctype.h>

using namespace std;

unsigned long long unpack_value(string str)  {
    return unpack_value(str.c_str(), str.length());
}

string pack_value(size_t len, unsigned long long i) {
    char arr[len] = {};
    pack_value(len, arr, i);
    return string(arr, len);
}

protocol::protocol(string sub, string enc)  {
    CP2P_DEBUG("Defining subnet with length: %i\n", sub.length())
    _base = getSubnet((char *)sub.c_str(), sub.length(), (char *)enc.c_str(), enc.length());
    CP2P_DEBUG("Done defining\n")
}

protocol::~protocol()   {
    destroySubnet(_base);
}

string protocol::id()  {
    char *_id = subnetID(_base);
    return string(_id, _base->idSize);
}

string protocol::subnet()   {
    return string(_base->subnet, _base->subnetSize);
}

string protocol::encryption()   {
    return string(_base->encryption, _base->encryptionSize);
}

pathfinding_message::pathfinding_message(string type, string sen, vector<string> load) {
    msg_type = type;
    sender = sen;
    timestamp = getUTC();
    payload = load;
    compression = vector<string>();
    compression_fail = false;
}

pathfinding_message::pathfinding_message(string type, string sen, vector<string> load, vector<string> comp)   {
    msg_type = type;
    sender = sen;
    timestamp = getUTC();
    payload = load;
    compression = comp;
}

vector<string> process_string(string str)   {
    unsigned long processed = 0;
    unsigned long expected = str.length();
    vector<unsigned long> pack_lens;
    vector<string> packets;
    while (processed != expected)   {
        unsigned long tmp = unpack_value(str.substr(processed, 4));
        pack_lens.push_back(tmp);
        processed += 4;
        expected -= pack_lens.back();
    }
    // Then reconstruct the packets
    for (unsigned long i = 0; i < pack_lens.size(); i++)    {
        packets.push_back(str.substr(processed, pack_lens[i]));
        processed += pack_lens[i];
    }
    return packets;
}

string sanitize_string(string str, bool sizeless)    {
    if (!sizeless)
        return str.substr(4);
    return str;
}

string decompress_string(string str, vector<string> compressions)   {
    return str;
}

pathfinding_message::~pathfinding_message()  {}

string pathfinding_message::compression_used()  {
    if (compression.size())
        return compression[0];
    return string("");
}

string pathfinding_message::time_58()   {
    return to_base_58(timestamp);
    // size_t i = 0;
    // char *temp = to_base_58(timestamp, i);
    // return string(temp, i);
}

string pathfinding_message::id()    {
    if (cache.timestamp == timestamp && cache.payload == payload && cache.id != "")   {
        CP2P_DEBUG("Fetching cached ID\n")
        return string(cache.id); //for copy constructor
    }

    string t58 = time_58();
    size_t done = 0, expected = t58.length();

    for (unsigned long i = 0; i < payload.size(); i++)
        expected += payload[i].length();

    unsigned char *info = new unsigned char[expected];

    for (unsigned long i = 0; i < payload.size(); i++)  {
        memcpy(info + done, payload[i].c_str(), payload[i].length());
        done += payload[i].length();
    }
    memcpy(info + done, t58.c_str(), t58.length());

    unsigned char digest[SHA384_DIGEST_LENGTH];
    memset(digest, 0, SHA384_DIGEST_LENGTH);
    SHA384_CTX ctx;
    SHA384_Init(&ctx);
    SHA384_Update(&ctx, (unsigned char*)info, expected);
    SHA384_Final(digest, &ctx);

    cache.payload = vector<string>(payload);
    cache.timestamp = timestamp;
    cache.id = ascii_to_base_58(string((char*)digest, SHA384_DIGEST_LENGTH));

#ifdef CP2P_DEBUG_FLAG
    printf("ID for [\"");
    for (size_t i = 0; i < expected; i++)   {
        printf("\\x%02x", info[i]);
    }
    printf("\"]:\n");
#endif
    CP2P_DEBUG("%s\n", cache.id.c_str());

    return string(cache.id);    //for copy constructor
}

vector<string> pathfinding_message::packets()   {
    vector<string> packs;
    packs.reserve(4 + payload.size());
    packs.push_back(msg_type);
    packs.push_back(sender);
    packs.push_back(id());
    packs.push_back(time_58());
    packs.insert(packs.end(), payload.begin(), payload.end());
    return packs;
}

string pathfinding_message::base_string()   {
    if (cache.timestamp == timestamp && cache.msg_type == msg_type && cache.payload == payload)
        return string(cache.base_string);   //for copy constructor

    string header = "";
    string base = "";
    vector<string> packs = packets();
    for (unsigned long i = 0; i < packs.size(); i++)    {
        header += pack_value(4, (unsigned long long)packs[i].size());
        base += packs[i];
    }

    //cache.timestamp = timestamp;  //implied by call to packets, which calls id
    //cache.payload = payload;      //implied by call to packets, which calls id
    cache.msg_type = msg_type;
    cache.base_string = header + base;

    return string(cache.base_string);   //for copy constructor
}

string pathfinding_message::str()    {
    string base = base_string();
    string header = pack_value(4, (unsigned long long)base.length());
    return header + base;
}

unsigned long long pathfinding_message::length()    {
    return base_string().length();
}

string pathfinding_message::header()    {
    return pack_value(4, (unsigned long long)length());
}

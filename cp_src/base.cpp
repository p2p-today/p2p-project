#include "base.h"
#include <ctype.h>

using namespace std;

unsigned long getUTC() {
    time_t t;
    time(&t);
    return mktime(gmtime(&t));
}

unsigned long long unpack_value(string str)  {
    unsigned long long val = 0;
    for (unsigned int i = 0; i < str.length(); i++)    {
        val = val << 8;
        val += (unsigned char)str[i];
    }
    return val;
}

string pack_value(size_t len, unsigned long long i) {
    vector<unsigned char> arr((size_t)len, 0);
    for (size_t j = 0; j < len; j++)    {
        arr[len - j - 1] = i & 0xff;
        i = i >> 8;
        if (i == 0)
            break;
    }
    return string(arr.begin(), arr.end());
}

protocol::protocol(string sub, string enc)  {
    CP2P_DEBUG("Defining subnet with length: %i\n", sub.length())
    subnet = sub;
    CP2P_DEBUG("Defining encryption with length: %i\n", enc.length())
    encryption = enc;
    CP2P_DEBUG("Done defining\n")
}

protocol::~protocol()   {}

string protocol::id()  {
    if (cache.subnet == subnet && cache.encryption == encryption && cache.id != "")
        return cache.id;

    char buffer[5];
    size_t buff_size = sprintf(buffer, "%llu.%llu", (unsigned long long)CP2P_PROTOCOL_MAJOR_VERSION, (unsigned long long)CP2P_PROTOCOL_MINOR_VERSION);
    string info = subnet + encryption + string(buffer, buff_size);

    unsigned char digest[SHA256_DIGEST_LENGTH];
    memset(digest, 0, SHA256_DIGEST_LENGTH);
    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    SHA256_Update(&ctx, (unsigned char*)info.c_str(), info.length());
    SHA256_Final(digest, &ctx);

    cache.subnet = string(subnet);
    cache.encryption = string(encryption);
    cache.id = ascii_to_base_58(string((char*)digest, SHA256_DIGEST_LENGTH));
    return cache.id;
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

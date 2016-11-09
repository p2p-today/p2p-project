#include "base.h"
#include <ctype.h>

using namespace std;

unsigned long long unpack_value(string str)  {
    return unpack_value(str.c_str(), str.length());
}

string pack_value(size_t len, unsigned long long i) {
    char *arr = new char[len];
    pack_value(len, arr, i);
    string ret = string(arr, len);
    delete[] arr;
    return ret;
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

pathfinding_message::pathfinding_message(struct InternalMessageStruct *base)  {
    _base = base;
}

pathfinding_message::pathfinding_message(string type, string sen, vector<string> load) {
    init(type, sen, load);
}

pathfinding_message::pathfinding_message(string type, string sen, vector<string> load, vector<string> comp)   {
    init(type, sen, load);
    setCompression(comp);
}

void pathfinding_message::init(string type, string sen, vector<string> load)    {
    CP2P_DEBUG("Entered constructor\n");
    const size_t num_payload = load.size();
    size_t *payload_lens = new size_t[num_payload];
    CP2P_DEBUG("Running suspicious line\n");
    char **payload = new char*[num_payload];
    for (size_t i = 0; i < num_payload; i++)    {
        payload_lens[i] = load[i].length();
        payload[i] = (char *) load[i].c_str();
    }
    CP2P_DEBUG("Real constructor\n");
    _base = constructInternalMessage(type.c_str(), type.length(),
                                     sen.c_str(),  sen.length(),
                                     payload, payload_lens, num_payload);
    CP2P_DEBUG("Exited real constructor\n");
    delete[] payload_lens;
    delete[] payload;
    CP2P_DEBUG("delete[] doesn't hate you\n");
}

void pathfinding_message::setCompression(vector<string> comp)   {
    const size_t num_compressions = comp.size();
    size_t *compression_lens = new size_t[num_compressions];
    char **compression = new char*[num_compressions];
    for (size_t i = 0; i < num_compressions; i++)    {
        compression_lens[i] = comp[i].length();
        compression[i] = (char *) comp[i].c_str();
    }
    setInternalMessageCompressions(_base, compression, compression_lens, num_compressions);
    delete[] compression_lens;
    delete[] compression;
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
    size_t len = str.length();
    char *res = new char[len];
    memcpy(res, str.c_str(), len);
    int status = sanitize_string(res, &len, sizeless);
    if (status) {
        printf("Bad status returned in sanitize_string\n");
    }
    return string(res, len);
}

string decompress_string(string str, vector<string> compressions)   {
    return str;
}

pathfinding_message::~pathfinding_message()  {
    destroyInternalMessage(_base);
}

string pathfinding_message::msg_type()  {
    return string(_base->msg_type, _base->msg_type_len);
}

string pathfinding_message::sender()    {
    CP2P_DEBUG("%s\n", _base->sender);
    return string(_base->sender, _base->sender_len);
}

unsigned long long pathfinding_message::timestamp() {
    return _base->timestamp;
}

vector<string> pathfinding_message::compression()   {
    if (_base->compression != NULL) {
        vector<string> compression;
        compression.reserve(_base->num_compressions);
        for (size_t i = 0; i < _base->num_compressions; i++) {
            compression.push_back(string(_base->compression[i], _base->compression_lens[i]));
        }
        return compression;
    }
    return vector<string>();
}

string pathfinding_message::compression_used()  {
    if (_base->compression != NULL)
        return string(_base->compression[0], _base->compression_lens[0]);
    return string("");
}

string pathfinding_message::time_58()   {
    return to_base_58(_base->timestamp);
    // size_t i = 0;
    // char *temp = to_base_58(timestamp, i);
    // return string(temp, i);
}

vector<string> pathfinding_message::payload()   {
    vector<string> payload;
    CP2P_DEBUG("I was called\n");
    payload.reserve(_base->num_payload);
    for (size_t i = 0; i < _base->num_payload; i++) {
        CP2P_DEBUG("%s\n", _base->payload[i]);
        payload.push_back(string(_base->payload[i], _base->payload_lens[i]));
    }
    return payload;
}

string pathfinding_message::id()    {
    ensureInternalMessageID(_base);
    return string(_base->id, _base->id_len);
}

vector<string> pathfinding_message::packets()   {
    vector<string> packs;
    vector<string> payload = pathfinding_message::payload();
    packs.reserve(4 + payload.size());
    packs.push_back(msg_type());
    packs.push_back(sender());
    packs.push_back(id());
    packs.push_back(time_58());
    packs.insert(packs.end(), payload.begin(), payload.end());
    return packs;
}

string pathfinding_message::base_string()   {
    string header = "";
    string base = "";
    vector<string> packs = packets();
    for (unsigned long i = 0; i < packs.size(); i++)    {
        header += pack_value(4, (unsigned long long)packs[i].size());
        base += packs[i];
    }

    return header + base;
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

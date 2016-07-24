#include "base.h"

using namespace std;

unsigned long getUTC() {
    time_t t;
    time(&t);
    return mktime(gmtime(&t));
}

const string base_58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

string to_base_58(unsigned long long i) {
    string str = "";
    while (i)   {
        str = base_58[i % 58] + str;
        i = i / 58;
    }
    if (str == "")
        str = base_58[0];
    return str;
}

string divide_by_58(string digest, int &remainder) {
    string answer = string("");
    for (int i = 0; i < digest.length(); i++)    {
        unsigned char b = digest[i];
        //cout << "b = " << b << endl; // prints working character
        int c = remainder * 256 + b;
        //cout << "c = " << c << endl; // prints currently divided number
        int d = c / 58;
        //cout << "d = " <<d << endl; // prints divided number over twelve
        remainder = c % 58;
        //cout <<"remainder = "<< remainder << endl; // prints remainder
        if (answer != "" || d != 0) {
            answer += (char)d;
        }
    }
    return answer;
}

string to_base_58(string digest, unsigned long sz)   {
    string answer = "";
    int chr = 0;
    while (digest.length()) {
        printf("%s\n", digest);
        digest = divide_by_58(digest, chr);
        answer += base_58[chr];
    }
    return answer;
}

unsigned long long from_base_58(string str) {
    unsigned long long ret = 0;
    for (unsigned int i = 0; i < str.length(); i++)    {
        ret = ret * 58 + base_58.find(str[i]); 
    }
    return ret;
}

unsigned long unpack_ulong(string str)  {
    unsigned long val = 0;
    for (unsigned int i = 0; i < str.length(); i++)    {
        val *= 256;
        val += (unsigned char)str[i];
    }
    return val;
}

string pack_ulong(uint32_t i)  {
    unsigned char arr[4];
    arr[0] = i >> 24 & 0xff;
    arr[1] = i >> 16 & 0xff;
    arr[2] = i >> 8 & 0xff;
    arr[3] = i & 0xff;
    return string(arr, arr+4);
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
        pack_lens.push_back(unpack_ulong(str.substr(processed, 4)));
        processed += 4;
        expected -= pack_lens[-1];
    }
    // Then reconstruct the packets
    for (unsigned long i = 0; i < pack_lens.size(); i++)    {
        packets.push_back(str.substr(processed, processed + pack_lens[i]));
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
    return NULL;
}

string pathfinding_message::time_58()   {
    return to_base_58(timestamp);
}

string pathfinding_message::id()    {
    string str;

    for (unsigned long i = 0; i < payload.size(); i++)
        str.append(payload[i]);
    str.append(time_58());

    string digest = sha384(str);
    return digest;
    // size_t ret_size = 70;
    // char ret[ret_size];
    // b58enc(ret, &ret_size, digest.c_str(), digest.length());
    // printf("%s\n", digest.c_str());
    // printf("%s\n", ret);

    // string ret_string = string(ret);
    // printf("%s\n", ret_string.c_str());
    // return ret_string;
}

vector<string> pathfinding_message::packets()   {
    vector<string> packs;
    packs.reserve(4 + payload.size());
    packs.push_back(msg_type);
    packs.push_back(sender);
    packs.push_back(id());
    packs.push_back(to_base_58(timestamp));
    packs.insert(packs.end(), payload.begin(), payload.end());
    return packs;
}

string pathfinding_message::base_string()   {
    string header = "";
    string base = "";
    vector<string> packs = packets();
    for (unsigned long i = 0; i < packs.size(); i++)    {
        header += pack_ulong((uint32_t)packs[i].size());
        base += packs[i];
    }
    return header + base;
}

string pathfinding_message::str()    {
    string base = base_string();
    string header = pack_ulong((uint32_t)base.length());
    for (int i = 0; i < header.length(); i++)
        printf("%i ", header[i]);
    printf("%s\n", (header + base).c_str());
    return header + base;
}

unsigned long long pathfinding_message::length()    {
    return base_string().length();
}

string pathfinding_message::header()    {
    return pack_ulong(length());
}
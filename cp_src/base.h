#ifndef CP2P_PROTOCOL_MAJOR_VERSION
#define CP2P__STR( ARG ) #ARG
#define CP2P__STR__( ARG ) CP2P__STR(ARG)

#define CP2P_PROTOCOL_MAJOR_VERSION 0
#define CP2P_PROTOCOL_MINOR_VERSION 4
#define CP2P_NODE_VERSION 255
#define CP2P_VERSION CP2P__STR__(CP2P_PROTOCOL_MAJOR_VERSION) "." CP2P__STR__(CP2P_PROTOCOL_MINOR_VERSION) "." CP2P__STR__(CP2P_NODE_VERSION)

#ifdef CP2P_DEBUG_FLAG
    #define CP2P_DEBUG(...) printf(__VA_ARGS__);
#else
    #define CP2P_DEBUG(...)
#endif

#include <string>
#include <sstream>
#include <iostream>
#include <cstdlib>
#include <vector>
#include <time.h>
#include <stdio.h>
#include <string.h>
#include "sha/sha256.h"
#include "sha/sha384.h"
#include "base_converter/BaseConverter.h"

using namespace std;

typedef basic_string<unsigned char> ustring;

namespace flags {
    static const unsigned char\
    *reserved_cstr = (unsigned char*)"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F",
    *implemented_compressions_cstr = (unsigned char*)"";


    static const vector<unsigned char>\
    reserved(reserved_cstr, reserved_cstr + 0x20),
    implemented_compressions(implemented_compressions_cstr, implemented_compressions_cstr + 0);

    static const unsigned char\
    broadcast   =  0x00,  // also sub-flag
    waterfall   =  0x01,
    whisper     =  0x02,  // also sub-flag
    renegotiate =  0x03,
    ping        =  0x04,  // Unused, but reserved
    pong        =  0x05,  // Unused, but reserved

    // sub-flags
    //broadcast   =  0x00,
    compression =  0x01,
    //whisper     =  0x02,
    handshake   =  0x03,
    //ping        =  0x04,
    //pong        =  0x05,
    notify      =  0x06,
    peers       =  0x07,
    request     =  0x08,
    resend      =  0x09,
    response    =  0x0A,
    store       =  0x0B,
    retrieve    =  0x0C,

    // implemented compression methods
    gzip    =  0x11,
    zlib    =  0x13,

    // non-implemented compression methods (based on list from compressjs):
    bwtc    =  0x14,
    bz2     =  0x10,
    context1=  0x15,
    defsum  =  0x16,
    dmc     =  0x17,
    fenwick =  0x18,
    huffman =  0x19,
    lzjb    =  0x1A,
    lzjbr   =  0x1B,
    lzma    =  0x12,
    lzp3    =  0x1C,
    mtf     =  0x1D,
    ppmd    =  0x1E,
    simple  =  0x1F;
}

unsigned long getUTC();
string to_base_58(unsigned long long i);
string divide_by_58(string digest, int &remainder);
string to_base_58(string digest, unsigned long sz);
unsigned long long from_base_58(string str);
unsigned long long unpack_value(string str);
string pack_value(size_t len, unsigned long long i);
string sanitize_string(string str, bool sizeless);
string decompress_string(string str, vector<string> compressions);
vector<string> process_string(string str);

class protocol  {
    public:
        protocol(string subnet, string encryption);
        ~protocol();
        string id();
        string subnet, encryption;
};

class pathfinding_message   {
    public:
        pathfinding_message(string msg_type, string sender, vector<string> payload);
        pathfinding_message(string msg_type, string sender, vector<string> payload, vector<string> compressions);

        static pathfinding_message feed_string(string msg)   {
            vector<string> packets = process_string(msg);
            pathfinding_message pm = pathfinding_message(
                packets[0],
                packets[1], 
                vector<string>(packets.begin() + 4, packets.end()));
            pm.timestamp = from_base_58(packets[3]);
            return pm;
        }

        static pathfinding_message feed_string(string msg, bool sizeless)  {
            return pathfinding_message::feed_string(
                sanitize_string(msg, sizeless));
        }

        static pathfinding_message feed_string(string msg, vector<string> compressions)    {
            return pathfinding_message::feed_string(
                decompress_string(msg, compressions));
        };

        static pathfinding_message feed_string(string msg, bool sizeless, vector<string> compressions) {
            return pathfinding_message::feed_string(
                sanitize_string(msg, sizeless),
            compressions);
        };
        ~pathfinding_message();
        string msg_type, sender;
        unsigned long timestamp;
        vector<string> payload;
        vector<string> compression;
        bool compression_fail;
        string compression_used();
        string time_58();
        string id();
        vector<string> packets();
        string base_string();
        string str();
        unsigned long long length();
        string header();
};

#endif
#ifndef CP2P_PROTOCOL_MAJOR_VERSION
#define CP2P__STR( ARG ) #ARG
#define CP2P__STR__( ARG ) CP2P__STR(ARG)

#define CP2P_PROTOCOL_MAJOR_VERSION 0
#define CP2P_PROTOCOL_MINOR_VERSION 4
#define CP2P_NODE_VERSION 319
#define CP2P_VERSION CP2P__STR__(CP2P_PROTOCOL_MAJOR_VERSION) "." CP2P__STR__(CP2P_PROTOCOL_MINOR_VERSION) "." CP2P__STR__(CP2P_NODE_VERSION)

#ifdef CP2P_DEBUG_FLAG
    #define CP2P_DEBUG(...) printf(__VA_ARGS__);
#else
    #define CP2P_DEBUG(...)
#endif

//This macro was taken from http://www.pixelbeat.org/programming/gcc/static_assert.html under the GNU All-Permissive License
#define ASSERT_CONCAT_(a, b) a##b
#define ASSERT_CONCAT(a, b) ASSERT_CONCAT_(a, b)
/* These can't be used after statements in c89. */
#ifdef __COUNTER__
  #define STATIC_ASSERT(e,m) \
    ;enum { ASSERT_CONCAT(static_assert_, __COUNTER__) = 1/(int)(!!(e)) }
#else
  /* This can't be used twice on the same line so ensure if using in headers
   * that the headers are not included twice (by wrapping in #ifndef...#endif)
   * Note it doesn't cause an issue when used on same line of separate modules
   * compiled with gcc -combine -fwhole-program.  */
  #define STATIC_ASSERT(e,m) \
    ;enum { ASSERT_CONCAT(assert_line_, __LINE__) = 1/(int)(!!(e)) }
#endif
//End macro

#include <string>
#include <sstream>
#include <iostream>
#include <cstdlib>
#include <vector>
#include <time.h>
#include <stdio.h>
#include <string.h>
#include "../c_src/sha/sha2.h"
#include "../c_src/BaseConverter.h"

using namespace std;

STATIC_ASSERT(sizeof(size_t) >= 4, "Size of strings is too small to easily meet protocol specs");

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

static string get_user_salt()  {
    srand (time(NULL));
    CP2P_DEBUG("Building user_salt\n");
    char temp_user_salt[] = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx";
    char *temp_hex_set = (char*)"0123456789abcdef";
    for (size_t i = 0; i < 36; i++) {
        if (temp_user_salt[i] == 'x')
            temp_user_salt[i] = temp_hex_set[(rand() % 16)];
        else if (temp_user_salt[i] == 'y')
            temp_user_salt[i] = temp_hex_set[((rand() % 16) & 0x3) | 0x8];
    }

    const string user_salt = string(temp_user_salt, 36);

    return user_salt;
}

const static string user_salt = get_user_salt();

unsigned long getUTC();
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
    private:
        struct {
            string id, subnet, encryption;
        } cache;
};

class pathfinding_message   {
    public:
        pathfinding_message(string msg_type, string sender, vector<string> payload);
        pathfinding_message(string msg_type, string sender, vector<string> payload, vector<string> compressions);

        static pathfinding_message *feed_string(string msg)   {
#ifdef CP2P_DEBUG_FLAG
            printf("String fed: \"");
            for (size_t i = 0; i < msg.length(); i++)   {
                printf("\\x%02x", msg[i]);
            }
            printf("\":\n");
#endif
            vector<string> packets = process_string(msg);
            pathfinding_message *pm = new pathfinding_message(
                packets[0],
                packets[1],
                vector<string>(packets.begin() + 4, packets.end()));
            CP2P_DEBUG("Setting timestamp as %s (%i)", packets[3].c_str(), from_base_58(packets[3].c_str(), packets[3].length()))
            pm->timestamp = from_base_58(packets[3].c_str(), packets[3].length());
            return pm;
        }

        static pathfinding_message *feed_string(string msg, bool sizeless)  {
            return pathfinding_message::feed_string(
                sanitize_string(msg, sizeless));
        }

        static pathfinding_message *feed_string(string msg, vector<string> compressions)    {
            return pathfinding_message::feed_string(
                decompress_string(msg, compressions));
        };

        static pathfinding_message *feed_string(string msg, bool sizeless, vector<string> compressions) {
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
    private:
        struct {
            string msg_type, sender, id, base_string;
            unsigned long timestamp;
            vector<string> payload;
        } cache;
};

#endif
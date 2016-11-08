/**
* Base Module
* ===========
*
* This module contains common functions and classes used throughout the rest of the library
*/
#ifndef CP2P_PROTOCOL_MAJOR_VERSION
#define CP2P__STR( ARG ) #ARG
#define CP2P__STR__( ARG ) CP2P__STR(ARG)

#define CP2P_PROTOCOL_MAJOR_VERSION 0
#define CP2P_PROTOCOL_MINOR_VERSION 4
#define CP2P_NODE_VERSION 516
#define CP2P_VERSION CP2P__STR__(CP2P_PROTOCOL_MAJOR_VERSION) "." CP2P__STR__(CP2P_PROTOCOL_MINOR_VERSION) "." CP2P__STR__(CP2P_NODE_VERSION)
/**
* .. c:macro:: CP2P_PROTOCOL_MAJOR_VERSION
*
*     This macro defines the major version number. A change here indicates a major change or release, and may be breaking. In a scheme x.y.z, it would be x
*
* .. c:macro:: CP2P_PROTOCOL_MINOR_VERSION
*
*     This macro defines the minor version number. It refers specifically to minor protocol revisions, and all changes here are API compatible (after 1.0), but not compatbile with other nodes. In a scheme x.y.z, it would be y
*
* .. c:macro:: CP2P_NODE_VERSION
*
*     This macro defines the patch version number. It refers specifically to node policies, and all changes here are backwards compatible. In a scheme x.y.z, it would be z
*
* .. c:macro:: CP2P_VERSION
*
*     This macro is a string literal. It combines all the above macros into a single string. It will generate whatever a string literal would normally be interpreted as in that context.
*
* .. c:macro:: CP2P_DEBUG_FLAG
*
*     This macro indicates whether cp2p should generate debug prints. If you define this as anything it will print
*/

#ifdef CP2P_DEBUG_FLAG
    #define CP2P_DEBUG(...) printf(__VA_ARGS__);
#else
    #define CP2P_DEBUG(...)
#endif

//This macro was taken from:
//http://www.pixelbeat.org/programming/gcc/static_assert.html
//under the GNU All-Permissive License, which is included below:
//Copyright © Pádraig Brady 2008
//
//Copying and distribution of this file, with or without modification,
//are permitted in any medium without royalty provided the copyright
//notice and this notice are preserved.
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
#include "../c_src/SubnetStruct.h"
#include "../c_src/InternalMessageStruct.h"
#include "../c_src/base.h"

using namespace std;

STATIC_ASSERT(sizeof(size_t) >= 4, "Size of strings is too small to easily meet protocol specs");

namespace flags {
    static const unsigned char\
    *reserved = (unsigned char*)"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F",
    *implemented_compressions = (unsigned char*)"";

    static const size_t\
    reserved_len = 0x20,
    compression_len = 0x00;

    /**
    * .. cpp:var:: static const unsigned char *flags::reserved_cstr
    *
    *     This binary data string contains every reserved flag.
    *
    *     .. note::
    *
    *         This will be refactored later to an array of :c:type:`unsigned char *` s, but for know just know that all flags are one char long.
    *
    * .. cpp:var:: static const size_t flags::reserved_len
    *
    *     The length of the above string
    *
    * .. cpp:var:: static const unsigned char *flags::implemented_compressions_cstr
    *
    *     This binary data string contains the flag of every implemented compression methods.
    *
    *     .. note::
    *
    *         This will be refactored later to an array of :c:type:`unsigned char *` s, but for know just know that all flags are one char long.
    *
    * .. cpp:var:: static const size_t flags::compression_len
    *
    *     The length of the above string
    *
    * .. cpp:var:: static const unsigned char flags::other_flags
    *
    *     These are the flags currently reserved. They are guarunteed to be the same names and values as the flags within :py:class:`py2p.base.flags`.
    *
    *     .. note::
    *
    *         This will be refactored later to an array of :c:type:`unsigned char *` s, but for know just know that all flags are one char long.
    */

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
    /**
    * .. cpp:function:: static std::string get_user_salt()
    *
    *     This generates a uuid4 for use in this library
    */
    char temp_user_salt[36];
    get_user_salt(temp_user_salt);
    const string user_salt = string(temp_user_salt, 36);

    return user_salt;
}

/**
* .. cpp:var:: const static std::string user_salt
*
*     A generated uuid4 for use in this library
*/
const static string user_salt = get_user_salt();

unsigned long long unpack_value(string str);
/**
* .. cpp:function:: unsigned long long unpack_value(std::string str)
*
*     Unpacks a big-endian binary value into an unsigned long long
*
*     :param str: The value you'd like to unpack
*
*     :returns: The value this string contained
*
*     .. warning::
*
*         Integer overflow will not be accounted for
*/
string pack_value(size_t len, unsigned long long i);
/**
* .. cpp:function:: std::string pack_value(size_t len, unsigned long long i)
*
*     Packs an unsigned long long into a big-endian binary string of length len
*
*     :param len:   The length of the string you'd like to produce
*     :param i:     The value you'd like to pack
*
*     :returns: A :cpp:class:`std::string` packed with the equivalent big-endian data
*
*     .. warning::
*
*         Integer overflow will not be accounted for
*/
string sanitize_string(string str, bool sizeless);
/**
* .. cpp:function:: std::string sanitize_string(std::string str, bool sizeless)
*
*     This function takes in a string and removes metadata that the :cpp:class:`pathfinding_message` deserializer can't handle
*
*     :param str:       The string you would like to sanitize
*     :param sizeless:  A bool indicating if this string has a size header attached
*
*     :returns: A :cpp:class:`std::string` which has the safe version of ``str``
*/
string decompress_string(string str, vector<string> compressions);
/**
* .. cpp:function:: std::string decompress_string(std::string str, std::vector<std::string> compressions)
*
*     This function is currently an identity function which returns ``str``. In the future this function will
*     decompress strings for the :cpp:class:`pathfinding_message` parser to deal with.
*
*     :param str:           The string you would like to decompress
*     :param compressions:  A :cpp:class:`std::vector\<std::string>` which contains the list of possible compression methods
*
*     :returns: A :cpp:class:`std::string` which has the decompressed version of ``str``
*/
vector<string> process_string(string str);
/**
* .. cpp:function:: std::vector<std::string> process_string(std::string str)
*
*     This deserializes a :cpp:class:`pathfinding_message` string into a :cpp:class:`std::vector\<std::string>` of packets
*
*     :param str: The :cpp:class`std::string` you would like to parse
*
*     :returns: A :cpp:class:`std::vector\<std::string>` which contains the packets serialized in this string
*/

class protocol  {
    /**
    * .. cpp:class:: protocol
    *
    *     This class is used as a subnet object. Its role is to reject undesired connections.
    *     If you connect to someone who has a different protocol object than you, this descrepency is detected,
    *     and you are silently disconnected.
    */
    public:
        protocol(string subnet, string encryption);
        /**
        *     .. cpp:function:: protocol::protocol(std::string, std::string encryption)
        *
        *         :param subnet:        The subnet you'd like to use
        *         :param encryption:    The encryption method you'd like to use
        */
        ~protocol();
        /**
        *     .. cpp:function:: protocol::~protocol()
        *
        *         An empty deconstructor
        */
        string id();
        /**
        *     .. cpp:function:: std::string protocol::id()
        *
        *         :returns: A :cpp:class:`std::string` which contains the base_58 encoded, SHA256 based ID of this protocol object
        */
        string subnet();
        /**
        *     .. cpp:function:: std::string protocol::subnet
        *
        */
        string encryption();
        /**
        *     .. cpp:function:: std::string protocol::encryption
        */
    private:
        struct SubnetStruct *_base;
};

class pathfinding_message   {
    /**
    * .. cpp:class:: pathfinding_message
    *
    *     This is the message serialization/deserialization class.
    */
    public:
        pathfinding_message(string msg_type, string sender, vector<string> payload);
        pathfinding_message(string msg_type, string sender, vector<string> payload, vector<string> compressions);
        /**
        *     .. cpp:function:: pathfinding_message::pathfinding_message(std::string msg_type, std::string sender, std::vector<std::string> payload)
        *
        *     .. cpp:function:: pathfinding_message::pathfinding_message(std::string msg_type, std::string sender, std::vector<std::string> payload, std::vector<std::string> compressions)
        *
        *
        *         :param msg_type:      This is the main flag checked by nodes, used for routing information
        *         :param sender:        The ID of the person sending the message
        *         :param payload:       A :cpp:class:`std::vector\<std::string>` of "packets" that you want your peers to receive
        *         :param compression:   A :cpp:class:`std::vector\<std::string>` of compression methods that the receiver supports
        */

        static pathfinding_message feed_string(string msg)   {
            return pathfinding_message::feed_string(msg, 0);
        }

        static pathfinding_message feed_string(string msg, bool sizeless)  {
            return pathfinding_message(deserializeInternalMessage(msg.c_str(), msg.length(), sizeless));
        }

        static pathfinding_message feed_string(string msg, vector<string> compressions)    {
            return pathfinding_message::feed_string(msg, 0, compressions);
        };

        static pathfinding_message feed_string(string msg, bool sizeless, vector<string> compressions) {
            size_t num_compression = compressions.size();
            size_t *compression_len = new size_t[num_compression];
            char **compression = new char*[num_compression];
            for (size_t i = 0; i < num_compression; i++)    {
                compression[i] = (char *) compressions[i].c_str();
                compression_len[i] = compressions[i].length();
            }
            pathfinding_message ret = pathfinding_message(
                deserializeCompressedInternalMessage(
                    msg.c_str(), msg.length(), sizeless, compression, compression_len, num_compression
                )
            );
            delete[] compression;
            delete[] compression_len;
            return ret;
        };
        /**
        *     .. cpp:function:: static pathfinding_message *pathfinding_message::feed_string(std::string msg)
        *
        *     .. cpp:function:: static pathfinding_message *pathfinding_message::feed_string(std::string msg, bool sizeless)
        *
        *     .. cpp:function:: static pathfinding_message *pathfinding_message::feed_string(std::string msg, std::vector<std::string> compressions)
        *
        *     .. cpp:function:: static pathfinding_message *pathfinding_message::feed_string(std::string msg, bool sizeless, std::vector<std::string> compressions)
        *
        *         :param msg:           A :cpp:class:`std::string` which contains the serialized message
        *         :param sizeless:      A :c:type:`bool` which indicates if the message has a size header attached (default: it does)
        *         :param compressions:  A :cpp:class:`std::vector\<std::string>` which contains the possible compression methods this message may be using
        *
        *         :returns: A pointer to the deserialized message
        */
        ~pathfinding_message();
        /**
        *     .. cpp:function:: pathfinding_message::~pathfinding_message()
        */
        string msg_type();
        string sender();
        unsigned long long timestamp();
        vector<string> payload();
        vector<string> compression();
        void setCompression(vector<string> comp);
        /**
        *     .. cpp:var:: std::string pathfinding_message::msg_type
        *
        *     .. cpp:var:: std::string pathfinding_message::sender
        *
        *     .. cpp:var:: unsigned long long pathfinding_message::timestamp
        *
        *     .. cpp:var:: std::vector<std::string> pathfinding_message::payload
        *
        *     .. cpp:var:: std::vector<std::string> pathfinding_message::compression
        */
        string compression_used();
        /**
        *     .. cpp:function:: std::string pathfinding_message::compression_used()
        *
        *         :returns: The compression method this message was sent under
        */
        string time_58();
        /**
        *     .. cpp:function:: std::string pathfinding_message::time_58()
        *
        *         :returns: :cpp:var:`pathfinding_message::timestamp` encoded in base_58
        */
        string id();
        /**
        *     .. cpp:function:: std::string pathfinding_message::id()
        *
        *         :returns: A SHA384 hash of this message encoded in base_58
        */
        vector<string> packets();
        /**
        *     .. cpp:function:: std::vector<std::string> pathfinding_message::packets()
        *
        *         A copy of :cpp:var:`pathfinding_message::payload` with some additional metadata appended to the front. Specifically:
        *
        *         0. :cpp:var:`pathfinding_message::msg_type`
        *         #. :cpp:var:`pathfinding_message::sender`
        *         #. :cpp:func:`pathfinding_message::id()`
        *         #. :cpp:func:`pathfinding_message::time_58()`
        *         #. :cpp:var:`pathfinding_message::payload` from here on out
        *
        *         :returns: A :cpp:class:`std::vector\<std::string>` in the above format
        */
        string base_string();
        /**
        *     .. cpp:function:: std::string pathfinding_message::base_string()
        *
        *         :returns: the serialized message, excepting the four byte size header at the beginning
        */
        string str();
        /**
        *     .. cpp:function:: std::string pathfinding_message::str()
        *
        *         :returns: the serialized message, including the four byte size header at the beginning
        */
        unsigned long long length();
        /**
        *     .. cpp:function:: unsigned long long pathfinding_message::length()
        *
        *         :returns: the length of the serialized message, excepting the four byte size header at the beginning
        */
        string header();
        /**
        *     .. cpp:function:: std::string pathfinding_message::header()
        *
        *         :returns: the four byte size header at the beginning of the serialized message
        */
    private:
        struct InternalMessageStruct *_base;
        pathfinding_message(struct InternalMessageStruct *base);
        void init(string msg_type, string sen, vector<string> load);
};

#endif

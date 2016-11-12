/**
* Base Module
* ===========
*
* This module contains common functions and classes used throughout the rest of the library
*/

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

static string get_user_salt()  {
    /**
    * .. cpp:function:: static std::string get_user_salt()
    *
    *     This generates a uuid4 for use in this library
    */
    char temp_user_salt[36];
    get_user_salt(temp_user_salt);
    return string(temp_user_salt, 36);
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
        SubnetStruct *_base;
};

class pathfinding_message   {
    /**
    * .. cpp:class:: pathfinding_message
    *
    *     This is the message serialization/deserialization class.
    *
    *     .. note::
    *
    *         This is just a wrapper for :c:type:`InternalMessageStruct`. Use that if you prefer efficiency over pleasant APIs.
    */
    public:
        pathfinding_message(string msg_type, string sender, vector<string> payload);
        pathfinding_message(string msg_type, string sender, vector<string> payload, vector<string> compressions);
        /**
        *     .. cpp:function:: pathfinding_message::pathfinding_message(std::string msg_type, std::string sender, std::vector<std::string> payload)
        *
        *     .. cpp:function:: pathfinding_message::pathfinding_message(std::string msg_type, std::string sender, std::vector<std::string> payload, std::vector<std::string> compressions)
        *
        *         :param msg_type:      This is the main flag checked by nodes, used for routing information
        *         :param sender:        The ID of the person sending the message
        *         :param payload:       A :cpp:class:`std::vector\<std::string>` of "packets" that you want your peers to receive
        *         :param compression:   A :cpp:class:`std::vector\<std::string>` of compression methods that the receiver supports
        */

        static pathfinding_message *feed_string(string msg)   {
            return pathfinding_message::feed_string(msg, 0);
        }

        static pathfinding_message *feed_string(string msg, bool sizeless)  {
            CP2P_DEBUG("Entering deserialization\n");
            int error = 0;
            return new pathfinding_message(deserializeInternalMessage(msg.c_str(), msg.length(), sizeless, &error));
        }

        static pathfinding_message *feed_string(string msg, vector<string> compressions)    {
            return pathfinding_message::feed_string(msg, 0, compressions);
        };

        static pathfinding_message *feed_string(string msg, bool sizeless, vector<string> compressions) {
            size_t num_compression = compressions.size();
            size_t *compression_len = new size_t[num_compression];
            char **compression = new char*[num_compression];
            for (size_t i = 0; i < num_compression; i++)    {
                compression[i] = (char *) compressions[i].c_str();
                compression_len[i] = compressions[i].length();
            }
            int error = 0;
            pathfinding_message *ret = new pathfinding_message(
                deserializeCompressedInternalMessage(
                    msg.c_str(), msg.length(), sizeless, &error, compression, compression_len, num_compression
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
        InternalMessageStruct *_base;
        pathfinding_message(InternalMessageStruct *base);
        void init(string msg_type, string sen, vector<string> load);
};

#endif

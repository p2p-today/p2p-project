#ifndef BASE
#define BASE 0

#include <openssl/sha.h>

#if 1 //def OPENSSL_NO_SHA512
#include <Python.h>
#endif

#include <string>
#include <iostream>
#include <cstdlib>
#include <vector>
#include <time.h>
#include <stdio.h>

using namespace std;

unsigned long getUTC();
string to_base_58(unsigned long long i);
string divide_by_58(string digest, int &remainder);
string to_base_58(string digest, unsigned long sz);
unsigned long long from_base_58(string str);
unsigned long unpack_ulong(string str);
string pack_ulong(unsigned long i);
string sanitize_string(string str, bool sizeless);
string decompress_string(string str, vector<string> compressions);
vector<string> process_string(string str);

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
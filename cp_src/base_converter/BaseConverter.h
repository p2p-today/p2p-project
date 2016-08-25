// Arbitrary precision base conversion by Daniel Gehriger <gehriger@linkcad.com>
// Permission for use was given here: http://archive.is/BFA8H#17%
// This has been heavily modified since copying, and has been hardcoded for a specific case

#include <string>
#include <cmath>

using namespace std;

const static string base_58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const static string ascii   = string((char *)"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff", 256);

static string to_base_58(unsigned long long i) {
    string str = "";
    while (i)   {
        str = base_58[i % 58] + str;
        i /= 58;
    }
    if (str == "")
        str = base_58[0];
    return str;
}

static unsigned long long from_base_58(string str) {
    unsigned long long ret = 0;
    for (unsigned int i = 0; i < str.length(); i++)    {
        ret = ret * (unsigned long long) 58 + (unsigned long long) base_58.find(str[i]);
    }
    return ret;
}

static string dec2base(unsigned int value)    {
    string result = "\x00\x00\x00\x00";
    size_t pos = 3;
    do  {
        result[pos] = ascii[value % 256];
        pos--;
        value /= 256;
    } 
    while (value > 0);

    return result;
}

static unsigned int base2dec(const string& value) {
    unsigned int result = 0;
    for (size_t i = 0; i < value.length(); ++i) {
        result *= 256;
        unsigned int c = ascii.find(value[i]);
        if (c == string::npos)
            throw runtime_error("Invalid character");

        result += c;
    }

    return result;
}

static unsigned int divide_58(string& x) {
    size_t length = x.length();
    size_t pos = 0;
    char quotient[length] = {};

    for (size_t i = 0; i < length; ++i) {
        size_t j = i + 1 + x.length() - length;
        if (x.length() < j)
            break;

        unsigned int value = base2dec(x.substr(0, j));

        quotient[pos] = ascii[value / 58];
        pos++;
        x = dec2base(value % 58) + x.substr(j);
    }

    // calculate remainder
    unsigned int remainder = base2dec(x);

    // remove leading "zeros" from quotient and store in 'x'
    x.assign(quotient, pos);
    size_t n = x.find_first_not_of(ascii[0]);
    if (n != string::npos)
        x = x.substr(n);
    else
        x.clear();

    return remainder;
}

static string ascii_to_base_58_(string input)    {
    size_t res_size = ceil(input.length() * 1.4);
    size_t pos = res_size - 1;
    unsigned char result[res_size] = {};

    do  {
        unsigned int remainder = divide_58(input);
        result[pos] = ascii[remainder];
        pos--;
    }
    while (!input.empty() && !(input.length() == 1 && input[0] == ascii[0]));

    return string(result + pos + 1, result + res_size - 1);
}

static string ascii_to_base_58(string input, size_t minDigits) {
    string result = ascii_to_base_58_(input);
    if (result.length() < minDigits)
        return string(minDigits - result.length(), base_58[0]) + result;
    else
        return result;
}

static string ascii_to_base_58(string input)   {
    return ascii_to_base_58(input, 1);
}
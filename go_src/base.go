/**
* Base Module
* ===========
*
* This module contains common functions and types used in the rest of the library.
*/
package main

import (
    "bytes"
    "compress/gzip"
    "compress/zlib"
    "crypto/rand"
    "crypto/sha256"
    "crypto/sha512"
    "fmt"
    "io/ioutil"
    "reflect"
    "strings"
    "time"
)

func pseudo_uuid() (string) {
    b := make([]byte, 16)
    _, err := rand.Read(b)
    if err != nil {
        panic(err)
    }

    b[8] = (b[8] | 0x80) & 0xBF
    b[6] = (b[6] | 0x40) & 0x4F

    return fmt.Sprintf("%X-%X-%X-%X-%X", b[:4], b[4:6], b[6:8], b[8:10], b[10:])
}

func getUTC() (int64)   {
    return time.Now().UTC().Unix()
}

func get_ulong(str interface{}) (int64)    {
    switch str.(type) {
        case []byte:
            return get_ulong_from_bytes(str.([]byte))
        case string:
            b := []byte(str.(string))
            return get_ulong_from_bytes(b)
        default:
            panic("Invalid type")
    }
}

func get_ulong_from_bytes(arr []byte) (int64) {
    if len(arr) != 4 {
        panic("not size of long")
    }
    val := int64(0)
    for i := 0; i < len(arr); i++   {
        val *= 256
        val += int64(arr[i])
    }
    return val
}

func pack_ulong(i int64) ([]byte)    {
    arr := []byte("\x00\x00\x00\x00")
    for c := 3; c >= 0; c-- {
        arr[c] = byte(i % int64(256))
        i /= 256
    }
    return arr
}

var compression []string = []string{"gzip", "zlib"}

func compress(data []byte, method string) ([]byte)  {
    switch method   {
        case "gzip":
            var b bytes.Buffer
            gz := gzip.NewWriter(&b)
            if _, err := gz.Write(data); err != nil {
                panic(err)
            }
            if err := gz.Flush(); err != nil {
                panic(err)
            }
            if err := gz.Close(); err != nil {
                panic(err)
            }
            return b.Bytes()
        case "zlib":
            var b bytes.Buffer
            gz := zlib.NewWriter(&b)
            if _, err := gz.Write(data); err != nil {
                panic(err)
            }
            if err := gz.Flush(); err != nil {
                panic(err)
            }
            if err := gz.Close(); err != nil {
                panic(err)
            }
            return b.Bytes()
        default:
            panic("Unknown compression method")
    }
}

func decompress(data []byte, method string) ([]byte)    {
    switch method   {
        case "gzip":
            b := bytes.NewBuffer(data)
            gz, err := gzip.NewReader(b)
            if err != nil   {
                panic(err)
            }
            var ret []byte
            if ret, err = ioutil.ReadAll(gz); err != nil    {
                panic(err)
            }
            return ret
        case "zlib":
            b := bytes.NewBuffer(data)
            gz, err := zlib.NewReader(b)
            if err != nil   {
                panic(err)
            }
            var ret []byte
            if ret, err = ioutil.ReadAll(gz); err != nil    {
                panic(err)
            }
            return ret
        default:
            panic("Unknown compression method")
    }
}

const base_58 string = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

func to_base_58(i interface{}) (string)   {
    switch i.(type) {
        case int32:
            return to_base_58_from_int64(int64(i.(int32)))
        case int:
            return to_base_58_from_int64(int64(i.(int)))
        case int64:
            return to_base_58_from_int64(i.(int64))
        case []byte:
            return to_base_58_from_bytes(i.([]byte))
        case string:
            return to_base_58_from_bytes([]byte(i.(string)))
        default:
            panic(reflect.TypeOf(i))
    }
}

func to_base_58_from_int64(i int64) (string)    {
    str := ""
    for i != 0 {
        str += string(base_58[i % int64(58)])
        i /= int64(58)
    }
    if str == "" {
        str = string(base_58[0])
    }
    return str
}

func divide_byte_by_58(b []byte, remainder int) ([]byte, int)   {
    answer := []byte("")
    for i := 0; i < len(b); i++ {
        char := int(b[i])
        c := remainder * 256 + char
        d := c / 58
        remainder = c % 58
        if len(answer) != 0 || d != 0   {
            answer = append(answer, byte(d))
        }
    }
    return answer, remainder
}

func to_base_58_from_bytes(b []byte) (string)   {
    answer := []byte("")
    var char int
    for len(b) != 0 {
        b, char = divide_byte_by_58(b, 0)
        answer = append([]byte{base_58[char]}, answer...)
    }
    return string(answer)
}

func from_base_58(str string) (int64)   {
    decimal := int64(0)
    for i := len(str) - 1; i >= 0; i-- {
        decimal *= 58
        decimal += int64(strings.Index(base_58, string(str[i])))
    }
    return decimal
}

type protocol struct    {
    subnet      string
    encryption  string
}

func (p protocol) id() string    {
    info := []byte(p.subnet + p.encryption)
    hash := sha256.New()
    hash.Write(info)
    return to_base_58(hash.Sum([]byte("")))
}

type pathfinding_message struct {
    protocol            protocol
    msg_type            string
    sender              string
    payload             [][]byte
    time                int64
    compression         []string
    compression_fail    bool
}

func (msg pathfinding_message) time_58() string {
    return to_base_58_from_int64(msg.time)
}

func (msg pathfinding_message) id() string  {
    payload_bytes := make([]byte, 0)
    for i := 0; i < len(msg.payload); i++   {
        payload_bytes = append(payload_bytes, msg.payload[i]...)
    }
    hash := sha512.New384()
    hash.Write(payload_bytes)
    return to_base_58_from_bytes(hash.Sum([]byte("")))
}

func (msg pathfinding_message) packets() [][]byte   {
    meta := [][]byte{
        []byte(msg.msg_type),
        []byte(msg.sender),
        []byte(msg.id()),
        []byte(msg.time_58())}
    return append(meta, msg.payload...)
}

func (msg pathfinding_message) compression_used() string    {
    for i := 0; i < len(msg.compression); i++   {
        for j := 0; j < len(compression); j++   {
            if msg.compression[i] == compression[j] {
                return msg.compression[i]
            }
        }
    }
    return ""
}

func (msg pathfinding_message) base_bytes() []byte  {
    header := make([]byte, 0)
    payload := make([]byte, 0)
    packets := msg.packets()
    for i := 0; i < len(packets); i++   {
        header = append(header, pack_ulong(int64(len(packets[i])))...)
        payload = append(payload, packets[i]...)
    }
    if comp := msg.compression_used(); comp != ""   {
        return compress(append(header, payload...), comp)
    }
    return append(header, payload...)
}

func (msg pathfinding_message) bytes() []byte   {
    payload := msg.base_bytes()
    header := pack_ulong(int64(len(payload)))
    return append(header, payload...)
}

func new_pathfinding_message(prot protocol, msg_type string, sender string, payload interface{}, compressions interface{}) (pathfinding_message)   {
    fmtd_payload := make([][]byte, 0)
    fmtd_compression := make([]string, 0)
    switch payload.(type)   {
        case [][]byte:
            fmtd_payload = payload.([][]byte)
        case []string:
            payload := payload.([]string)
            for i := 0; i < len(payload); i++   {
                fmtd_payload = append(fmtd_payload, []byte(payload[i]))
            }
        default:
            panic("payload is wrong type")
    }
    switch compressions.(type)   {
        case [][]byte:
            compressions := compressions.([][]byte)
            for i := 0; i < len(compressions); i++   {
                fmtd_compression = append(fmtd_compression, string(compressions[i]))
            }
        case []string:
            fmtd_compression = compressions.([]string)
        default:
            panic("compressions are wrong type")
    }
    return pathfinding_message{
                protocol:         prot,
                msg_type:         msg_type,
                sender:           sender,
                payload:          fmtd_payload,
                compression:      fmtd_compression,
                compression_fail: false,
                time:             getUTC()}
}

func sanitize_string(b []byte, sizeless bool) []byte    {
    if sizeless {
        return b
    }
    if get_ulong(string(b[:4])) != int64(len(b[4:]))    {
        panic("Size header is incorrect")
    }
    return b[4:]
}

func decompress_string(b []byte, compressions []string) []byte   {
    compression_used := ""
    for i := 0; i < len(compressions); i++   {
        for j := 0; j < len(compression); j++   {
            if compressions[i] == compression[j] {
                compression_used = compressions[i]
                break
            }
        }
    }
    if compression_used != ""   {
        return decompress(b, compression_used)
    }
    return b
}

func process_string(b []byte) [][]byte  {
    processed := 0
    expected := len(b)
    pack_lens := make([]int, 0)
    packets := make([][]byte, 0)
    for processed != expected   {
        pack_lens = append(pack_lens, int(get_ulong(b[processed:processed+4])))
        processed += 4
        expected -= pack_lens[len(pack_lens)-1]
    }
    for _, val := range pack_lens {
        start := processed
        processed += val
        end := processed
        packets = append(packets, b[start:end])
    }
    return packets
}

func feed_string(prot protocol, b []byte, sizeless bool, compressions []string) pathfinding_message {
    b = sanitize_string(b, sizeless)
    b = decompress_string(b, compressions)
    packets := process_string(b)
    return pathfinding_message{
                protocol:         prot,
                msg_type:         string(packets[0]),
                sender:           string(packets[1]),
                payload:          packets[4:],
                compression:      compressions,
                compression_fail: false,
                time:             from_base_58(string(packets[3]))}
}

func main() {
    fmt.Println(get_ulong("\xFF\x00\x00\x04"))
    fmt.Println(to_base_58(4))
    fmt.Println(to_base_58(256))
    fmt.Println(from_base_58(to_base_58(4)))
    fmt.Println(from_base_58(to_base_58(256)))
    fmt.Println(from_base_58(to_base_58([]byte("\xFF\x00\x00\x04"))))
    fmt.Println(protocol{
                subnet: "hi",
                encryption: "Plaintext"}.id())
    fmt.Println(pseudo_uuid())
    test_msg := new_pathfinding_message(
        protocol{
            "hi",
            "Plaintext"},
        "test",
        "test sender",
        []string{"test1", "test2"},
        []string{} )
    fmt.Println(test_msg.bytes())
    fmt.Println(string(test_msg.bytes()))
    test_msg.compression = []string{"gzip"}
    fmt.Println("With gzip")
    fmt.Println(test_msg.bytes())
    fmt.Println(string(test_msg.bytes()))
    test_msg.compression = []string{"zlib"}
    fmt.Println("With zlib")
    fmt.Println(test_msg.bytes())
    fmt.Println(string(test_msg.bytes()))
    fmt.Println(compress([]byte("test"), "gzip"))
    fmt.Println(compress([]byte("test"), "zlib"))
    fmt.Println(string(decompress(compress([]byte("test"), "gzip"), "gzip")))
    fmt.Println(string(decompress(compress([]byte("test"), "zlib"), "zlib")))
    fmt.Println(test_msg.bytes())
    from_feed := feed_string(protocol{
                    "hi",
                    "Plaintext"},
                    test_msg.bytes(),
                    false,
                    []string{"zlib"})
    fmt.Println(from_feed.bytes())
    fmt.Println(string(test_msg.bytes()) == string(from_feed.bytes()))
}
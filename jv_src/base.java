/**
* Base Module
* ===========
*
* This module contains common functions and classes used in the rest of the library.
*/
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.math.BigInteger;
import java.lang.Character;
import java.lang.StringBuilder;
import java.time.Instant;
import java.util.Arrays;
import java.util.ArrayList;

public class base   {

    public int[] version_info = {0, 4, 319};
    public String protocol_version = String.valueOf(version_info[0]) + "." + String.valueOf(version_info[1]);

    public class protocol   {
        String subnet;
        String encryption;

        public protocol(String subnet, String encryption)   {
            this.subnet = subnet;
            this.encryption = encryption;
        }

        String id() throws java.security.NoSuchAlgorithmException {
            String info = this.subnet + this.encryption + protocol_version;
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(info.getBytes());
            BigInteger i = new BigInteger(1, digest);
            return to_base_58(i);
        }
    }

    public class pathfinding_message    {
        String msg_type;
        String sender;
        String[] payload;
        long time;
        byte[][] compression;

        public pathfinding_message(String msg_type, String sender, String[] payload, byte[][] compression, long timestamp)   {
            this.msg_type = msg_type;
            this.sender = sender;
            this.payload = payload;
            this.compression = compression;
            this.time = timestamp;
        }

        public pathfinding_message(String msg_type, String sender, String[] payload, byte[][] compression)  {
            this(msg_type, sender, payload, compression, getUTC());
        }

        public pathfinding_message(String msg_type, String sender, String[] payload, long timestamp) {
            this(msg_type, sender, payload, new byte[0][0], timestamp);
        }

        public pathfinding_message(String msg_type, String sender, String[] payload)    {
            this(msg_type, sender, payload, new byte[0][0], getUTC());
        }

        private static byte[] sanitize_string(byte[] fed_string, boolean sizeless) throws Exception    {
            if (!sizeless)  {
                if (unpack_value(fed_string, 4) != fed_string.length - 4)   {
                    throw new Exception("Size header inaccurate " + Arrays.toString(Arrays.copyOfRange(fed_string, 0, 4)) + ", " + String.valueOf(fed_string.length - 4));
                }
                return Arrays.copyOfRange(fed_string, 4, fed_string.length);
            }
            return fed_string;
        }

        private static byte[] decompress_string(byte[] fed_string, byte[][] compressions)   {
            return fed_string;  //Eventually this will do decompression
        }

        private static String[] process_string(byte[] fed_string)   {
            int processed = 0;
            int expected = fed_string.length;
            ArrayList<Integer> pack_lens = new ArrayList<Integer>();

            while (processed != expected)   {
                byte[] pack_len = Arrays.copyOfRange(fed_string, processed, processed + 4);
                int new_len = (int)unpack_value(pack_len, 4);
                processed += 4;
                expected -= new_len;
                pack_lens.add(pack_lens.size(), new_len);
            }

            String[] packets = new String[pack_lens.size()];

            for (int i = 0; i < packets.length; i++)    {
                int end = processed + pack_lens.get(i);
                packets[i] = new String(Arrays.copyOfRange(fed_string, processed, end));
                processed = end;
            }

            return packets;
        }

        public static pathfinding_message feed_string(byte[] fed_string, boolean sizeless, byte[][] compressions) throws Exception     {
            byte[] sanitized_string = pathfinding_message.sanitize_string(fed_string, sizeless);
            sanitized_string = pathfinding_message.decompress_string(sanitized_string, compressions);
            String[] packets = pathfinding_message.process_string(sanitized_string);

            String[] payload = new String[packets.length-4];
            for (int i = 0; i < payload.length; i++)    {
                payload[i] = packets[4 + i];
            }

            pathfinding_message msg = new pathfinding_message(packets[0], packets[1], payload);
            msg.time = from_base_58(packets[3]);

            if (!packets[2].equals(msg.id())) {
                throw new Exception("Checksum match failed");
            }

            return msg;
        }

        public static pathfinding_message feed_string(byte[] fed_string, boolean sizeless) throws Exception     {
            return pathfinding_message.feed_string(fed_string, sizeless, new byte[0][0]);
        }

        public static pathfinding_message feed_string(byte[] fed_string, byte[][] compressions) throws Exception     {
            return pathfinding_message.feed_string(fed_string, false, compressions);
        }

        public static pathfinding_message feed_string(byte[] fed_string) throws Exception     {
            return pathfinding_message.feed_string(fed_string, false, new byte[0][0]);
        }

        public String time_58() {
            return to_base_58(this.time);
        }

        public String id() throws java.security.NoSuchAlgorithmException    {
            StringBuilder builder = new StringBuilder();
            for(String s : this.payload) {
                builder.append(s);
            }
            String info = builder.toString() + this.time_58();
            MessageDigest md = MessageDigest.getInstance("SHA-384");
            byte[] digest = md.digest(info.getBytes());
            BigInteger i = new BigInteger(1, digest);
            return to_base_58(i);
        }

        public String[] getPackets() throws java.security.NoSuchAlgorithmException  {
            String[] packets = new String[4 + this.payload.length];
            packets[0] = this.msg_type;
            packets[1] = this.sender;
            packets[2] = this.id();
            packets[3] = this.time_58();
            for (int i = 0; i < this.payload.length; i++)   {
                packets[4 + i] = this.payload[i];
            }
            return packets;
        }

        public byte[] non_len_string() throws java.security.NoSuchAlgorithmException {
            String id = this.id();
            String[] packets = this.getPackets();
            byte[][] encoded_packets = new byte[packets.length][];
            byte[] encoded_lengths = new byte[4 * packets.length];
            int total_length = 4 * packets.length;

            for (int i = 0; i < packets.length; i++)    {
                encoded_packets[i] = packets[i].getBytes();
                total_length += encoded_packets[i].length;
            }

            byte[] ret = new byte[total_length];

            for (int i = 0; i < encoded_packets.length; i++)    {
                byte[] len = pack_value(encoded_packets[i].length, 4);
                ret[(4 * i) + 0] = len[0];
                ret[(4 * i) + 1] = len[1];
                ret[(4 * i) + 2] = len[2];
                ret[(4 * i) + 3] = len[3];
            }

            int index = encoded_packets.length * 4;
            for (int i = 0; i < encoded_packets.length; i++)    {
                for (int j = 0; j < encoded_packets[i].length; j++) {
                    ret[index++] = encoded_packets[i][j];
                }
            }

            return ret;
        }

        public byte[] serialize() throws java.security.NoSuchAlgorithmException {
            byte[] non_len_string = this.non_len_string();

            // This is where compression should happen in the future

            byte[] ret = new byte[4 + non_len_string.length];
            byte[] len = pack_value(non_len_string.length, 4);

            ret[0] = len[0];
            ret[1] = len[1];
            ret[2] = len[2];
            ret[3] = len[3];

            for (int i = 0; i < non_len_string.length; i++) {
                ret[4 + i] = non_len_string[i];
            }

            return ret;
        }
    }

    public long unpack_value(byte[] arr, int len)    {
        long ret = 0;
        for (int i = 0; i < len; i++)   {
            ret *= 256;
            ret += arr[i];
        }
        return ret;
    }

    public byte[] pack_value(long value, int length)    {
        byte[] ret = new byte[length];
        Arrays.fill(ret, (byte) 0);
        for (int i = length - 1; i != 0 && value != 0; i++)   {
            ret[i] = (byte) (value % 256);
            value /= 256;
        }
        return ret;
    }

    public String base_58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

    public String to_base_58(long i)    {
        return to_base_58(BigInteger.valueOf(i));
    }

    public String to_base_58(BigInteger i)  {
        String ret = "";
        BigInteger fifty_eight = new BigInteger("58");
        BigInteger working_value = i;
        while (working_value.toString() != "0")   {
            BigInteger[] divAndRem = working_value.divideAndRemainder(fifty_eight);
            int index = divAndRem[1].intValue();
            ret = Character.toString(base_58.charAt(index)) + ret;
            working_value = divAndRem[0];
        }
        return ret;
    }

    public long from_base_58(String str)    {
        long ret = 0;
        for (int i = 0; i < str.length(); i++) {
            ret *= 58;
            ret += base_58.indexOf(str.charAt(i));
        }
        return ret;
    }

    public long getUTC() {
        return Instant.now().getEpochSecond();
    }
}

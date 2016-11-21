import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.math.BigInteger;
import java.lang.StringBuilder;
import java.util.Arrays;
import java.util.ArrayList;

public class InternalMessage    {
    String msg_type;
    String sender;
    String[] payload;
    long time;
    byte[][] compression;

    public InternalMessage(String msg_type, String sender, String[] payload, byte[][] compression, long timestamp)   {
        this.msg_type = msg_type;
        this.sender = sender;
        this.payload = payload;
        this.compression = compression;
        this.time = timestamp;
    }

    public InternalMessage(String msg_type, String sender, String[] payload, byte[][] compression)  {
        this(msg_type, sender, payload, compression, base.getUTC());
    }

    public InternalMessage(String msg_type, String sender, String[] payload, long timestamp) {
        this(msg_type, sender, payload, new byte[0][0], timestamp);
    }

    public InternalMessage(String msg_type, String sender, String[] payload)    {
        this(msg_type, sender, payload, new byte[0][0], base.getUTC());
    }

    private static byte[] sanitize_string(byte[] fed_string, boolean sizeless) throws Exception    {
        if (!sizeless)  {
            if (base.unpack_value(fed_string, 4) != fed_string.length - 4)   {
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
        ArrayList<String> packets = new ArrayList<String>();

        while (processed < expected)   {
            System.out.println(packets.size());
            byte[] pack_len = Arrays.copyOfRange(fed_string, processed, processed + 4);
            int new_len = (int) base.unpack_value(pack_len, 4);
            processed += 4;
            packets.add(new String(Arrays.copyOfRange(fed_string, processed, processed + new_len)));
            processed += new_len;
        }

        return packets.toArray(new String[packets.size()]);
    }

    public static InternalMessage feed_string(byte[] fed_string, boolean sizeless, byte[][] compressions) throws Exception     {
        byte[] sanitized_string = InternalMessage.sanitize_string(fed_string, sizeless);
        sanitized_string = InternalMessage.decompress_string(sanitized_string, compressions);
        String[] packets = InternalMessage.process_string(sanitized_string);

        String[] payload = new String[packets.length-4];
        for (int i = 0; i < payload.length; i++)    {
            payload[i] = packets[4 + i];
        }

        InternalMessage msg = new InternalMessage(packets[0], packets[1], payload);
        msg.time = base.from_base_58(packets[3]);

        if (!packets[2].equals(msg.id())) {
            throw new Exception("Checksum match failed");
        }

        return msg;
    }

    public static InternalMessage feed_string(byte[] fed_string, boolean sizeless) throws Exception     {
        return InternalMessage.feed_string(fed_string, sizeless, new byte[0][0]);
    }

    public static InternalMessage feed_string(byte[] fed_string, byte[][] compressions) throws Exception     {
        return InternalMessage.feed_string(fed_string, false, compressions);
    }

    public static InternalMessage feed_string(byte[] fed_string) throws Exception     {
        return InternalMessage.feed_string(fed_string, false, new byte[0][0]);
    }

    public String time_58() {
        return base.to_base_58(this.time);
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
        return base.to_base_58(i);
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
        int index = 0;

        for (int i = 0; i < encoded_packets.length; i++)    {
            byte[] len = base.pack_value(encoded_packets[i].length, 4);
            ret[index++] = len[0];
            ret[index++] = len[1];
            ret[index++] = len[2];
            ret[index++] = len[3];
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
        byte[] len = base.pack_value(non_len_string.length, 4);

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

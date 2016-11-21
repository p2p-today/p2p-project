/**
* Base Module
* ===========
*
* This module contains common functions and classes used in the rest of the library.
*/
import java.math.BigInteger;
import java.lang.Character;
import java.time.Instant;
import java.util.Arrays;

public class base   {

    public static int[] version_info = {0, 4, 319};
    public static String protocol_version = String.valueOf(version_info[0]) + "." + String.valueOf(version_info[1]);

    public static long unpack_value(byte[] arr, int len)    {
        long ret = 0;
        for (int i = 0; i < len; i++)   {
            ret *= 256;
            ret += arr[i];
        }
        return ret;
    }

    public static byte[] pack_value(long value, int length)    {
        byte[] ret = new byte[length];
        Arrays.fill(ret, (byte) 0);
        for (int i = length - 1; i != 0 && value != 0; i++)   {
            ret[i] = (byte) (value % 256);
            value /= 256;
        }
        return ret;
    }

    public static String base_58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

    public static String to_base_58(long i)    {
        return to_base_58(BigInteger.valueOf(i));
    }

    public static String to_base_58(BigInteger i)  {
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

    public static long from_base_58(String str)    {
        long ret = 0;
        for (int i = 0; i < str.length(); i++) {
            ret *= 58;
            ret += base_58.indexOf(str.charAt(i));
        }
        return ret;
    }

    public static long getUTC() {
        return Instant.now().getEpochSecond();
    }
}

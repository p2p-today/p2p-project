import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.math.BigInteger;

public class protocol   {
    String subnet;
    String encryption;

    public protocol(String subnet, String encryption)   {
        this.subnet = subnet;
        this.encryption = encryption;
    }

    String id() throws java.security.NoSuchAlgorithmException {
        String info = this.subnet + this.encryption + base.protocol_version;
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        byte[] digest = md.digest(info.getBytes());
        BigInteger i = new BigInteger(1, digest);
        return base.to_base_58(i);
    }
}

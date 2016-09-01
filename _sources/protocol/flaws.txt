Potential Serialization Flaws
=============================

The structure has a couple immediately obvious shortcomings.

First, the maximum message size is 4,294,967,299 bytes (including compression and headers). It could well be that in the future there will be more data to send in a single message. But equally so, a present-day attacker could use this to halt sections of a network using this structure. A short-term solution would be to have a soft-defined limit, but as has been shown in other protocols, this can calcify over time and do damage. In the end, this is more of a governance problem than a technical one. The discussion on this can be found in :issue:`84`.

Second, there is quite a lot of extra data being sent. Using the default parameters, if you want to send a 4 character message it will be expanded to 159 characters. That's ~42x larger. If you want these differences to be negligble, you need to send messages on the order of 512 characters. Then there is only an increase of ~34% (0% with decent compression). This can be improved by reducing the size of the various IDs being sent, or making the packet headers shorter. Both of these have disadvantages, however.

Making a shorter ID space means that you will be more likely to get a conflict. This isn't as much of a problem for node IDs as it is for message IDs, but it is certainly a problem you'd like to avoid. 

Making shorter packet headers presents few immediate problems, but it makes it more difficult for debugging, and may make it more difficult to establish standard headers in the future.

Results using opportunistic compression look roughly as follows (last updated in 0.4.231):

For 4 characters…

::

    original  4
    plaintext 167  (4175%)
    lzma      220  (5500%)
    bz2       189  (4725%)
    gzip      156  (3900%)

For 512 characters…

::

    original  512
    plaintext 677  (132.2%)
    lzma      568  (110.9%)
    bz2       555  (108.4%)
    gzip      487  (95.1%)

Because the reference implementations support all of these (excepting environment variations), this means that the overhead will drop away after ~500 characters. Communications with other implementations may be slower than this, however.
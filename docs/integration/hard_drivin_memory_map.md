# Hard Drivin' ADSP board memory map

**Status: MAME-discovery map awaiting full schematic decode**

## DSP-visible spaces

MAME currently maps program RAM at ADSP program addresses `0x0000–0x1fff`,
leaves `0x2000–0x3fff` as no-read, maps data RAM at data addresses
`0x0000–0x1fff`, and maps special board I/O at data addresses
`0x2000–0x2fff` [MAME-HARDDRIV, commit
`030fefcbd14e47c01ec9d67655be90f64a1dc8ab`, lines 676–693].

These ranges are emulator observations. The program/data memory and sequential
memory schematic sheets are the source that must establish decode aliases,
unpopulated ranges, and chip organization [ATARI-ADSP-SCHEM, PDF pp. 8–18].

## 68000-visible windows in MAME

| 68000 byte range | MAME interpretation |
|---|---|
| `0x800000–0x807fff` | ADSP program RAM |
| `0x808000–0x80bfff` | ADSP data RAM |
| `0x810000–0x813fff` | selected output-buffer RAM |
| `0x818000–0x81801f` | write-only ADSP controls |
| `0x818060–0x81807f` | clear ADSP-to-host interrupt |
| `0x838000–0x83ffff` | read ADSP status |

Source: [MAME-HARDDRIV, same commit, lines 4817–4835]. These windows describe
MAME's main-board integration, not yet a proven PAL decode. Address mirrors and
partial decoding are open questions pending the main-board and PAL sheet audit.

## Program-word host packing

MAME represents each 24-bit program word in a 32-bit container exposed as two
successive 16-bit host words, high half first [MAME-HARDDRIV-MACHINE, same
commit, lines 549–575]. The upper eight stored bits may be padding or a board
packing artifact. The wrapper must not adopt this layout until the program
memory/buffer schematics and host bus wiring have been transcribed.

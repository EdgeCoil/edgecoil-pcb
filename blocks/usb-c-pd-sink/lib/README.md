# lib: this block's own library parts

The symbols and footprints of the block's parts that KiCad's libraries lack (U3 HUSB238_002DD C7471904), library
nickname `lp`. They are LCSC/EasyEDA's own, converted with easyeda2kicad and saved in KiCad 9's
format, so that JLC's placement matches pad for pad. Third-party: not covered by the block's
CERN-OHL-S-2.0 licence, and their terms of reuse have not yet been reviewed.

Copied byte for byte from the date-label-printer rev B library by
`python3 -m edgecoil_pcb.blocks bundle <block dir> lp=<library dir>`, which also writes SHA256SUMS
(checked in CI). `bundle --check` compares the copy with a board library. Never edit these files
here: change the board's library, then re-bundle.

A board may use this copy (`local_libs={"lp": ("<path to this lib>", "")}`) or its own
(`parts(libs={"lp": "mylib"})`).

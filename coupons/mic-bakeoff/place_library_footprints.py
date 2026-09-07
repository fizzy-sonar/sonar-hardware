"""Place the emitted library assets using KiCad's own transform semantics.

Run with a Python interpreter providing pcbnew; invoked by generate_coupon.py.
The hand-emitted board carries routing/placement/nets, while the library supplies
the one canonical pad, mask, paste and courtyard geometry. Never duplicate these.
"""

from pathlib import Path
import re
import uuid

import pcbnew


def normalize(path):
    pcbnew.KIID.SeedGenerator(22)
    board = pcbnew.LoadBoard(str(path))
    library = path.parent / "libs/coupon.pretty"
    hole_index = 0
    for old in list(board.GetFootprints()):
        ref = old.GetReference()
        if ref == "H":
            hole_index += 1
            ref = f"H{hole_index}"
        name = old.GetFPID().GetLibItemName()
        if ref == "JP1":
            name = "PINHEADER_1X02_T016"
        fp = pcbnew.FootprintLoad(str(library), name)
        if fp is None:
            raise RuntimeError(f"Missing canonical footprint {name}")
        board.Add(fp)  # layer flipping needs the parent board's copper stack.
        fp.SetFPID(pcbnew.LIB_ID("coupon", name))
        fp.SetPosition(old.GetPosition())
        fp.SetOrientation(old.GetOrientation())
        if old.IsFlipped():
            fp.SetLayerAndFlip(pcbnew.B_Cu)
        fp.SetReference(ref)
        fp.SetValue(old.GetValue())
        nets = {p.GetNumber(): p.GetNetCode() for p in old.Pads()}
        for pad in fp.Pads():
            if pad.GetNumber() in nets:
                pad.SetNetCode(nets[pad.GetNumber()])
        x, y = pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y)
        field = fp.Reference()
        field.SetTextAngleDegrees(0)
        field.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
        field.SetTextThickness(pcbnew.FromMM(0.12))
        field.SetTextPos(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y - 1.5)))
        field.SetMirrored(fp.IsFlipped())
        if ref.startswith("M"):
            field.SetTextPos(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y - 2.6)))
        elif ref in ("C1", "C2", "C3", "C4"):
            field.SetTextPos(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y + 2.3)))
        elif ref == "U1":
            field.SetTextPos(pcbnew.VECTOR2I(pcbnew.FromMM(15.0), pcbnew.FromMM(7.3)))
        elif ref == "C11":
            field.SetTextPos(pcbnew.VECTOR2I(pcbnew.FromMM(11.0), pcbnew.FromMM(6.3)))
        elif ref in ("C7", "C8"):
            field.SetTextPos(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y + 1.9)))
        elif ref == "R1":
            field.SetTextPos(pcbnew.VECTOR2I(pcbnew.FromMM(3.0), pcbnew.FromMM(14.0)))
        elif ref == "TP2":
            field.SetTextPos(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y + 1.5)))
        elif ref == "J1":
            field.SetTextPos(pcbnew.VECTOR2I(pcbnew.FromMM(64.0), pcbnew.FromMM(22.5)))
        elif ref == "JP1":
            field.SetTextPos(pcbnew.VECTOR2I(pcbnew.FromMM(60.0), pcbnew.FromMM(27.7)))
        elif ref.startswith("H"):
            field.SetVisible(False)
        fp.Value().SetVisible(False)
        board.Remove(old)
    pcbnew.SaveBoard(str(path), board)
    # Library instances need distinct IDs. The generated board has no external
    # references to item UUIDs; make every serialized occurrence stable and unique.
    count = iter(range(1000000))
    path.write_text(
        re.sub(
            r'\(uuid "[^"]+"\)',
            lambda m: '(uuid "'
            + str(uuid.uuid5(uuid.NAMESPACE_URL, f"sonar-t022/{path.stem}/{next(count)}"))
            + '")',
            path.read_text(),
        )
    )
    print(f"canonical library placement: {path.stem}")


if __name__ == "__main__":
    import sys

    normalize(Path(sys.argv[1]))

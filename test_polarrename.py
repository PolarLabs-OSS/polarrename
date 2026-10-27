import tempfile
from pathlib import Path
from polarrename import Rules,plan,apply
with tempfile.TemporaryDirectory() as td:
    folder=Path(td)
    a=folder/"one.txt";b=folder/"two.txt"
    a.write_text("ONE");b.write_text("TWO")
    changes=plan([a,b],Rules(prefix="PL_",numbered=True))
    assert [dst.name for src,dst in changes]==["PL_one_001.txt","PL_two_002.txt"]
    moved=apply(changes)
    assert all(dst.exists() for src,dst in moved)
    apply([(dst,src) for src,dst in moved])
    assert a.read_text()=="ONE" and b.read_text()=="TWO"
    try:
        plan([a,b],Rules(search="one",replace="two"))
        raise AssertionError("Conflict should fail")
    except ValueError:pass
    print("PASS: numbering, rename, undo, conflict guard")

"""Presentation-only escape fix for the frozen sheet generator's CSV download script."""
from .m3 import ROOT


def fix(path):
    original=path.read_bytes()
    corrected=original.replace(b".join('\r\n')",b".join('\\r\\n')").replace(b".join('\n')",b".join('\\r\\n')")
    if corrected!=original: path.write_bytes(corrected)
    return corrected!=original


def main():
    print('HTML CSV export escape corrected:',fix(ROOT/'review/m3_labeling_sheet.html'))


if __name__=='__main__': main()

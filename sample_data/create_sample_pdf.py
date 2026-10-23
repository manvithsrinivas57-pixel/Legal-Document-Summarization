"""Utility script to generate a well-formed PDF from sample judgment text."""

from pathlib import Path
import pypdf


def generate_clean_pdf(output_path: Path, text_path: Path):
    """Generate a valid PDF containing the sample judgment text."""
    with open(text_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Construct PDF text stream
    content = "BT\n/F1 9 Tf\n40 760 Td\n13 TL\n"
    for line in lines:
        sanitized = (
            line.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .encode("latin-1", "replace")
            .decode("latin-1")
        )
        content += f"({sanitized}) ' \n"
    content += "ET\n"
    stream_bytes = content.encode("latin1")

    # Build objects with exact byte offsets
    header = b"%PDF-1.4\n"
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = (
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    obj4 = (
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin1")
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )
    obj5 = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"

    objects = [obj1, obj2, obj3, obj4, obj5]
    offsets = []
    current_offset = len(header)
    for obj in objects:
        offsets.append(current_offset)
        current_offset += len(obj)

    xref_offset = current_offset
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n"
    trailer = f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"

    pdf_data = header + b"".join(objects) + xref.encode("latin1") + trailer.encode("latin1")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pdf_data)

    # Verify with pypdf
    reader = pypdf.PdfReader(str(output_path))
    assert len(reader.pages) == 1
    extracted = reader.pages[0].extract_text()
    assert len(extracted) > 100
    print(f"Generated clean PDF '{output_path}' ({len(extracted)} extracted characters).")


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    generate_clean_pdf(base / "sample_civil_appeal.pdf", base / "sample_indian_judgment.txt")

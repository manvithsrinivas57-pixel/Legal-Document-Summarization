"""Generate multi-case judgment PDFs and a synthetic scanned PDF fixture for tests."""

from pathlib import Path
import pypdf

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "sample_data"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def build_pdf_from_text(output_path: Path, lines: list[str]) -> Path:
    """Build a valid PDF 1.4 document containing the provided text lines."""
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

    reader = pypdf.PdfReader(str(output_path))
    assert len(reader.pages) == 1
    return output_path


def build_scanned_pdf(output_path: Path) -> Path:
    """Build a valid PDF 1.4 document with drawing paths but zero extractable text (image-only simulation)."""
    # Graphics stream without text operators (re = rectangle, f = fill)
    stream_bytes = b"q 0.8 0.8 0.8 rg 50 50 512 692 re f Q\n"

    header = b"%PDF-1.4\n"
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = (
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R >>\nendobj\n"
    )
    obj4 = (
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin1")
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )

    objects = [obj1, obj2, obj3, obj4]
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

    reader = pypdf.PdfReader(str(output_path))
    extracted = reader.pages[0].extract_text() or ""
    assert len(extracted.strip()) == 0, f"Expected 0 text characters, got {len(extracted)}"
    return output_path


def main():
    # Case 2: Service Law / Retiral Recovery (Punjab & Haryana High Court)
    service_writ_lines = [
        "IN THE HIGH COURT OF PUNJAB AND HARYANA AT CHANDIGARH",
        "CIVIL WRIT PETITION NO. 15057 OF 2004",
        "DR. INDERJIT SINGH WASU ... PETITIONER",
        "VERSUS",
        "MANAGING COMMITTEE, GURU NANAK NAV BHARAT COLLEGE & ORS. ... RESPONDENTS",
        "M.M. KUMAR, J.",
        "1. The prayer in this petition under Article 226 of the Constitution is for quashing the order dated 13.11.2003",
        "effecting recovery of Rs. 2,93,285/- from Death-cum-Retirement Gratuity of the petitioner after superannuation.",
        "2. The petitioner served as Principal from 1.11.1999 and retired on superannuation on 28.1.2003.",
        "Ten months after retirement, respondent college issued a show-cause notice and ordered recovery on grounds of excess pay.",
        "3. Having heard learned counsel, we find that relationship of employer and employee terminated upon superannuation.",
        "Under Rule 2.2(b) of the Punjab Civil Services Rules, Volume II, recovery from pension cannot be ordered",
        "unless departmental proceedings were instituted before retirement with prior sanction of the government.",
        "4. Merely issuing a show-cause notice after superannuation does not constitute initiation of formal disciplinary proceedings.",
        "Fastening pecuniary liability on a retired employee without inquiry violates Article 14 of the Constitution.",
        "5. The impugned recovery order dated 13.11.2003 is hereby quashed. Respondents are directed to refund Rs. 2,93,285/-",
        "with interest at 12% per annum within two months. Petition allowed with costs.",
    ]
    p1 = build_pdf_from_text(SAMPLE_DIR / "sample_service_writ.pdf", service_writ_lines)
    print(f"Generated Case 2: {p1}")

    # Case 3: Criminal Appeal (Supreme Court of India)
    criminal_appeal_lines = [
        "IN THE SUPREME COURT OF INDIA",
        "CRIMINAL APPELLATE JURISDICTION",
        "CRIMINAL APPEAL NO. 882 OF 2018",
        "STATE OF PUNJAB ... APPELLANT",
        "VERSUS",
        "SATPAL SINGH ... RESPONDENT",
        "R.F. NARIMAN, J.",
        "1. This criminal appeal by special leave under Article 136 of the Constitution challenges the acquittal",
        "of the respondent by the High Court of Punjab and Haryana for offences under Section 409 of the Indian Penal Code",
        "and Section 13(1)(c) of the Prevention of Corruption Act, 1988.",
        "2. The prosecution alleged that while serving as Cashier in the Department of Irrigation, the respondent",
        "misappropriated public funds amounting to Rs. 4,50,000/- between June 2010 and August 2011.",
        "3. The trial court convicted the respondent. However, the High Court held that the prosecution failed to examine",
        "the principal auditor who prepared the reconciliation ledger, rendering the audit report inadmissible under Section 67 of the Evidence Act.",
        "4. It is settled law that in an appeal against acquittal, this Court will interfere only if the findings of the High Court",
        "are perverse or palpably erroneous. Suspicion, however grave, cannot substitute proof beyond reasonable doubt.",
        "5. We find no substantial ground to dislodge the view taken by the High Court. The Criminal Appeal is accordingly dismissed.",
    ]
    p2 = build_pdf_from_text(SAMPLE_DIR / "sample_criminal_appeal.pdf", criminal_appeal_lines)
    print(f"Generated Case 3: {p2}")

    # Scanned PDF Fixture (0 extractable characters)
    p3 = build_scanned_pdf(SAMPLE_DIR / "sample_scanned_image_only.pdf")
    print(f"Generated Scanned PDF Fixture: {p3}")


if __name__ == "__main__":
    main()

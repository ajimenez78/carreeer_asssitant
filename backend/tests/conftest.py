import io
import zipfile

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


@pytest.fixture
def pdf_bytes():
    def create(text="Synthetic Staff engineer", *, pages=1, encrypted=False):
        writer = PdfWriter()
        for _ in range(pages):
            page = writer.add_blank_page(width=600, height=800)
            if text:
                font = DictionaryObject(
                    {
                        NameObject("/Type"): NameObject("/Font"),
                        NameObject("/Subtype"): NameObject("/Type1"),
                        NameObject("/BaseFont"): NameObject("/Helvetica"),
                    }
                )
                page[NameObject("/Resources")] = DictionaryObject(
                    {
                        NameObject("/Font"): DictionaryObject(
                            {NameObject("/F1"): writer._add_object(font)}
                        )
                    }
                )
                stream = DecodedStreamObject()
                stream.set_data(f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode())
                page[NameObject("/Contents")] = writer._add_object(stream)
        if encrypted:
            writer.encrypt("synthetic-test-password")
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

    return create


@pytest.fixture
def docx_bytes():
    def create(text="Synthetic Staff engineer", *, extra_size=0, declaration=""):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "[Content_Types].xml",
                '<Types xmlns="http://schemas.openxmlformats.org/package/'
                '2006/content-types"><Override PartName="/word/document.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.document.main+xml"/></Types>',
            )
            archive.writestr(
                "word/document.xml",
                declaration
                + '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
                + text
                + "</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>"
                "Historical Python</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"
                "</w:body></w:document>",
            )
            if extra_size:
                archive.writestr("word/padding", b"x" * extra_size)
        return output.getvalue()

    return create

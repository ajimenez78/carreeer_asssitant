import io
import zipfile
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from career_assistant.config import Settings
from career_assistant.database import (
    database_engine,
    database_url,
    ensure_local_database,
    migrate_database,
)
from career_assistant.persistence import ensure_owner


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


@pytest.fixture(scope="session")
def database():
    # The creator rejects remote hosts before any connection or destructive action.
    url = database_url(Settings()).set(database=f"career_test_{uuid4().hex}")
    ensure_local_database(url)
    engine = database_engine(url)
    try:
        migrate_database(url)
        yield engine
    finally:
        engine.dispose()
        with psycopg.connect(
            url.set(drivername="postgresql", database="postgres").render_as_string(
                hide_password=False
            ),
            autocommit=True,
            connect_timeout=5,
        ) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {}").format(sql.Identifier(url.database))
            )


@pytest.fixture
def sessions(database):
    with database.begin() as connection:
        connection.execute(text("TRUNCATE owners, document_deletions CASCADE"))
    factory = sessionmaker(database, expire_on_commit=False)
    with factory.begin() as session:
        ensure_owner(session)
    return factory

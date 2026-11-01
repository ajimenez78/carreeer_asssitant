# Synthetic source fixture

`synthetic.doc` is a binary Word 97 document exported with an isolated
LibreOffice profile from this synthetic RTF:

```rtf
{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}}\f0\fs24 Synthetic background\par Staff engineer at Example Systems, 2018-2023.\par Historical Python and frontend experience.\par Education not provided.\par}
```

It contains no actual CV/profile content. Its short OLE WordDocument stream
reproduces antiword's small-stream limitation; catdoc reads it correctly.
PDF/DOCX/Markdown fixtures are generated deterministically by the test suite.
